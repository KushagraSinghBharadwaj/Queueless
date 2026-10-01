
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)


# ---------- Database ----------

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'queueless.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
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
    average_service_minutes: Mapped[int] = mapped_column(
        Integer, default=3
    )


class QueueEntry(Base):
    __tablename__ = "queue_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    facility_id: Mapped[int] = mapped_column(
        ForeignKey("facilities.id"), index=True
    )
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Queueless API",
    description="Virtual queue management for campus facilities",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------- Request schemas ----------

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
            QueueEntry.status.in_([
                QueueStatus.WAITING.value,
                QueueStatus.SERVING.value,
            ]),
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

    entries = active_entries(db, entry.facility_id)
    for position, item in enumerate(entries, start=1):
        if item.id == entry.id:
            return position
    return None


def entry_response(db: Session, entry: QueueEntry):
    facility = get_facility(db, entry.facility_id)
    position = queue_position(db, entry)

    # A person currently being served also takes service time.
    waiting_ahead = max(0, (position or 1) - 1)
    serving_now = any(
        item.status == QueueStatus.SERVING.value
        for item in active_entries(db, entry.facility_id)
    )

    wait_minutes = (
        waiting_ahead * facility.average_service_minutes
        + (
            facility.average_service_minutes
            if serving_now and entry.status == QueueStatus.WAITING.value
            else 0
        )
    )

    return {
        "entry_id": entry.id,
        "facility_id": entry.facility_id,
        "user_id": entry.user_id,
        "status": entry.status,
        "position": position,
        "estimated_wait_minutes": (
            wait_minutes if position is not None else None
        ),
    }


# ---------- Health ----------

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Queueless API"}


# ---------- Facilities ----------

@app.get("/api/facilities")
def list_facilities(db: Session = Depends(get_db)):
    facilities = db.scalars(
        select(Facility).order_by(Facility.id)
    ).all()

    return [
        {
            "id": item.id,
            "name": item.name,
            "location": item.location,
            "average_service_minutes": item.average_service_minutes,
        }
        for item in facilities
    ]


@app.post("/api/facilities", status_code=status.HTTP_201_CREATED)
def create_facility(
    data: FacilityCreate,
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(Facility).where(Facility.name == data.name)
    )
    if existing:
        raise HTTPException(
            status_code=409, detail="Facility already exists"
        )

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
    entries = active_entries(db, facility_id)

    return {
        "facility_id": facility.id,
        "facility_name": facility.name,
        "waiting_count": sum(
            item.status == QueueStatus.WAITING.value for item in entries
        ),
        "serving": next(
            (
                item.id
                for item in entries
                if item.status == QueueStatus.SERVING.value
            ),
            None,
        ),
        "entries": [
            entry_response(db, item)
            for item in entries
        ],
    }


@app.post("/api/queue/join", status_code=status.HTTP_201_CREATED)
def join_queue(
    data: JoinQueueRequest,
    db: Session = Depends(get_db),
):
    facility = get_facility(db, data.facility_id)

    existing = db.scalar(
        select(QueueEntry).where(
            QueueEntry.facility_id == data.facility_id,
            QueueEntry.user_id == data.user_id,
            QueueEntry.status.in_([
                QueueStatus.WAITING.value,
                QueueStatus.SERVING.value,
            ]),
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
        (
            item for item in entries
            if item.status == QueueStatus.SERVING.value
        ),
        None,
    )

    # Complete the current service, if one exists.
    if current:
        current.status = QueueStatus.COMPLETED.value

    # Start serving the next person in FIFO order.
    next_entry = next(
        (
            item for item in entries
            if item.status == QueueStatus.WAITING.value
        ),
        None,
    )

    if next_entry:
        next_entry.status = QueueStatus.SERVING.value

    db.commit()

    return {
        "message": "Queue advanced",
        "completed_entry_id": current.id if current else None,
        "now_serving_entry_id": (
            next_entry.id if next_entry else None
        ),
    }
