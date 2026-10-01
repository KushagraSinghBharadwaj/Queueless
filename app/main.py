from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import json

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from analytics.src.predict import predict_wait_time

# ---------- Paths / database ----------

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'queueless.db'}"
MODEL_PATH = BASE_DIR / "analytics" / "models" / "queue_wait_model.pkl"
DATASET_PATH = BASE_DIR / "analytics" / "data" / "raw" / "queue_data.csv"
MODEL_METADATA_PATH = BASE_DIR / "analytics" / "models" / "model_metadata.json"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class QueueStatus(str, Enum):
    WAITING = "waiting"
    SERVING = "serving"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    location: Mapped[str] = mapped_column(String(200))
    average_service_minutes: Mapped[int] = mapped_column(Integer, default=3)


class QueueEntry(Base):
    __tablename__ = "queue_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(
        String(20), default=QueueStatus.WAITING.value, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


def get_db():
    with SessionLocal() as db:
        yield db


# These names MUST match the one-hot columns used to train the model.
MODEL_FACILITIES = {
    "Canteen": ("Block A", 3),
    "Library": ("Block C", 4),
    "Printing Shop": ("Block B", 3),
    "Admin Office": ("Main Building", 5),
    "Computer Lab": ("Block D", 4),
    "Bus Stop": ("Main Gate", 2),
}


def seed_facilities(db: Session):
    existing = db.scalars(select(Facility).order_by(Facility.id)).all()

    # Development cleanup: remove the old placeholder facilities only when
    # there are no queue entries. This prevents accidental deletion of live data.
    active_entries_count = db.scalar(select(QueueEntry).limit(1)) is not None
    existing_names = {item.name for item in existing}

    if existing and not existing_names.intersection(MODEL_FACILITIES) and not active_entries_count:
        for item in existing:
            db.delete(item)
        db.commit()
        existing = []

    if not existing:
        for name, (location, service_minutes) in MODEL_FACILITIES.items():
            db.add(
                Facility(
                    name=name,
                    location=location,
                    average_service_minutes=service_minutes,
                )
            )
        db.commit()
        return

    # Add any missing model-compatible facilities without overwriting real data.
    for name, (location, service_minutes) in MODEL_FACILITIES.items():
        if name not in existing_names:
            db.add(
                Facility(
                    name=name,
                    location=location,
                    average_service_minutes=service_minutes,
                )
            )
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_facilities(db)
    yield


app = FastAPI(
    title="QueueLess API",
    description="Real-time virtual queue management with AI wait prediction",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Schemas ----------

class FacilityCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    location: str = Field(min_length=1, max_length=200)
    average_service_minutes: int = Field(default=3, ge=1, le=120)


class JoinQueueRequest(BaseModel):
    facility_id: int = Field(gt=0)
    user_id: str = Field(min_length=1, max_length=100)


class LeaveQueueRequest(BaseModel):
    entry_id: int = Field(gt=0)
    user_id: str = Field(min_length=1, max_length=100)


# ---------- Helpers ----------

def get_facility(db: Session, facility_id: int) -> Facility:
    facility = db.get(Facility, facility_id)
    if facility is None:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility


def active_entries(db: Session, facility_id: int):
    statement = (
        select(QueueEntry)
        .where(
            QueueEntry.facility_id == facility_id,
            QueueEntry.status.in_(
                [QueueStatus.WAITING.value, QueueStatus.SERVING.value]
            ),
        )
        .order_by(QueueEntry.id)
    )
    return list(db.scalars(statement).all())


def queue_position(db: Session, entry: QueueEntry) -> int | None:
    if entry.status not in (
        QueueStatus.WAITING.value,
        QueueStatus.SERVING.value,
    ):
        return None

    for position, item in enumerate(active_entries(db, entry.facility_id), start=1):
        if item.id == entry.id:
            return position
    return None


def current_time_features():
    now = datetime.now()
    hour = now.hour
    return {
        "day_of_week": now.weekday(),
        "hour": hour,
        "is_peak_hour": (
            (10 <= hour <= 11)
            or (12 <= hour <= 14)
            or (16 <= hour <= 17)
        ),
    }


def completed_today(db: Session, facility_id: int) -> int:
    now = datetime.now()
    start = datetime(now.year, now.month, now.day)
    statement = select(QueueEntry).where(
        QueueEntry.facility_id == facility_id,
        QueueEntry.status == QueueStatus.COMPLETED.value,
        QueueEntry.created_at >= start,
    )
    return len(db.scalars(statement).all())


def ai_prediction(
    db: Session,
    facility: Facility,
    queue_length: int,
) -> float:
    if queue_length <= 0:
        return 0.0

    features = current_time_features()

    return predict_wait_time(
        queue_length=queue_length,
        people_served=completed_today(db, facility.id),
        average_service_time=float(facility.average_service_minutes),
        day_of_week=features["day_of_week"],
        hour=features["hour"],
        is_peak_hour=features["is_peak_hour"],
        facility=facility.name,
    )


def entry_response(db: Session, entry: QueueEntry):
    facility = get_facility(db, entry.facility_id)
    position = queue_position(db, entry)

    if position is None:
        predicted = None
    else:
        # The AI should use the live queue size.
        entries = active_entries(db, facility.id)

        waiting_count = sum(
            1
            for item in entries
            if item.status == QueueStatus.WAITING.value
        )

        predicted = ai_prediction(
            db,
            facility,
            waiting_count,
        )

    return {
        "entry_id": entry.id,
        "facility_id": entry.facility_id,
        "user_id": entry.user_id,
        "status": entry.status,
        "position": position,
        "estimated_wait_minutes": predicted,
        "prediction_source": "random_forest",
    }


# ---------- Health ----------

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "QueueLess API",
        "ai_model_loaded": MODEL_PATH.exists(),
    }


# ---------- Facilities ----------

@app.get("/api/facilities")
def list_facilities(db: Session = Depends(get_db)):
    facilities = db.scalars(select(Facility).order_by(Facility.id)).all()

    return [
        {
            "id": item.id,
            "name": item.name,
            "location": item.location,
            "average_service_minutes": item.average_service_minutes,
        }
        for item in facilities
        if item.name in MODEL_FACILITIES
    ]


@app.post("/api/facilities", status_code=status.HTTP_201_CREATED)
def create_facility(
    data: FacilityCreate,
    db: Session = Depends(get_db),
):
    if data.name not in MODEL_FACILITIES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Facility name must match a trained model category: "
                + ", ".join(MODEL_FACILITIES)
            ),
        )

    existing = db.scalar(select(Facility).where(Facility.name == data.name))
    if existing:
        raise HTTPException(status_code=409, detail="Facility already exists")

    facility = Facility(**data.model_dump())
    db.add(facility)
    db.commit()
    db.refresh(facility)

    return {
        "id": facility.id,
        "name": facility.name,
        "location": facility.location,
        "average_service_minutes": facility.average_service_minutes,
    }


# ---------- Queue ----------

@app.get("/api/queue/{facility_id}")
def get_queue(facility_id: int, db: Session = Depends(get_db)):
    facility = get_facility(db, facility_id)

    if facility.name not in MODEL_FACILITIES:
        raise HTTPException(status_code=404, detail="AI-enabled facility not found")

    entries = active_entries(db, facility_id)
    waiting_count = sum(
        item.status == QueueStatus.WAITING.value for item in entries
    )

    return {
        "facility_id": facility.id,
        "facility_name": facility.name,
        "waiting_count": waiting_count,
        "serving": next(
            (
                item.id
                for item in entries
                if item.status == QueueStatus.SERVING.value
            ),
            None,
        ),
        "ai_predicted_wait_minutes": ai_prediction(
            db, facility, waiting_count
        ),
        "prediction_source": "random_forest",
        "entries": [entry_response(db, item) for item in entries],
    }


@app.post("/api/queue/join", status_code=status.HTTP_201_CREATED)
def join_queue(
    data: JoinQueueRequest,
    db: Session = Depends(get_db),
):
    facility = get_facility(db, data.facility_id)

    if facility.name not in MODEL_FACILITIES:
        raise HTTPException(status_code=400, detail="This facility is not AI-enabled")

    existing = db.scalar(
        select(QueueEntry).where(
            QueueEntry.facility_id == data.facility_id,
            QueueEntry.user_id == data.user_id,
            QueueEntry.status.in_(
                [QueueStatus.WAITING.value, QueueStatus.SERVING.value]
            ),
        )
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="User already has an active entry at this facility",
        )

    entry = QueueEntry(
        facility_id=facility.id,
        user_id=data.user_id,
        status=QueueStatus.WAITING.value,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry_response(db, entry)


@app.post("/api/queue/leave")
def leave_queue(
    data: LeaveQueueRequest,
    db: Session = Depends(get_db),
):
    entry = db.get(QueueEntry, data.entry_id)

    if entry is None or entry.user_id != data.user_id:
        raise HTTPException(status_code=404, detail="Queue entry not found")

    if entry.status != QueueStatus.WAITING.value:
        raise HTTPException(
            status_code=409,
            detail="Only waiting entries can leave the queue",
        )

    entry.status = QueueStatus.CANCELLED.value
    db.commit()

    return {
        "message": "Successfully left the queue",
        "entry_id": entry.id,
        "status": entry.status,
    }


@app.post("/api/queue/advance/{facility_id}")
def advance_queue(
    facility_id: int,
    db: Session = Depends(get_db),
):
    get_facility(db, facility_id)
    entries = active_entries(db, facility_id)

    current = next(
        (item for item in entries if item.status == QueueStatus.SERVING.value),
        None,
    )

    if current:
        current.status = QueueStatus.COMPLETED.value

    next_entry = next(
        (item for item in entries if item.status == QueueStatus.WAITING.value),
        None,
    )

    if next_entry:
        next_entry.status = QueueStatus.SERVING.value

    db.commit()

    return {
        "message": "Queue advanced",
        "completed_entry_id": current.id if current else None,
        "now_serving_entry_id": next_entry.id if next_entry else None,
    }


# ---------- Analytics ----------

@app.get("/api/analytics/summary")
def analytics_summary():
    if not DATASET_PATH.exists():
        raise HTTPException(status_code=404, detail="Historical dataset not found")

    import pandas as pd

    df = pd.read_csv(DATASET_PATH)

    historical = (
        df.groupby("facility")["wait_time"]
        .mean()
        .round(2)
        .reset_index()
        .rename(columns={"wait_time": "average_wait_minutes"})
        .to_dict(orient="records")
    )

    metadata = {}
    if MODEL_METADATA_PATH.exists():
        try:
            metadata = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
        except Exception:
            metadata = {}

    return {
        "historical_records": int(len(df)),
        "facilities": historical,
        "model": metadata,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
