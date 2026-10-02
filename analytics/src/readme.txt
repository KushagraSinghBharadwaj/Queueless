============================================================
QUEUELESS — AI / DATA / ANALYTICS TEAM HANDOFF
============================================================

Owner:
DATA / AI / ANALYTICS

Purpose:
This document explains everything implemented in the Analytics
module, the current ML pipeline, what the Backend must integrate,
and what the Frontend must display.

This document is intended for:
1. Backend developer
2. Frontend developer
3. AI / Analytics developer
4. Future maintenance of the project


============================================================
1. WHAT THE AI / ANALYTICS MODULE DOES
============================================================

The Analytics module is responsible for:

1. Queue data generation for development/testing
2. Data validation
3. Data preprocessing
4. Queue analytics
5. Feature engineering
6. ML model training
7. Model comparison
8. Wait-time prediction
9. Prediction uncertainty/range
10. Real-data pipeline
11. Retraining decision logic
12. Standard ML output contract

The main purpose is:

USER QUEUE INFORMATION
        |
        v
BACKEND
        |
        v
AI / ANALYTICS
        |
        v
PREDICTED WAIT TIME
        |
        v
BACKEND
        |
        v
FRONTEND
        |
        v
USER


============================================================
2. CURRENT PROJECT STRUCTURE
============================================================

analytics/
|
+-- data/
|   +-- external/
|   |   +-- queue_data_real.csv
|   |
|   +-- processed/
|   |   +-- queue_data_clean.csv
|   |   +-- queue_data_real_clean.csv
|   |
|   +-- raw/
|       +-- queue_data.csv
|
+-- models/
|   +-- queue_wait_model.pkl
|   +-- model_metadata.json
|
+-- outputs/
|   +-- analytics_summary.json
|   +-- model_comparison.csv
|
+-- src/
    +-- analytics.py
    +-- baseline.py
    +-- data_generator.py
    +-- data_generator_backup.py
    +-- data_validation.py
    +-- features.py
    +-- model_comparison.py
    +-- output_contract.py
    +-- predict.py
    +-- preprocessing.py
    +-- real_data_loader.py
    +-- retraining.py
    +-- train.py
    +-- README.txt


============================================================
3. DATASET
============================================================

Development dataset:

File:
analytics/data/raw/queue_data.csv

Current size:
10,000 records

Facilities:

1. Canteen
2. Library
3. Printing Shop
4. Admin Office
5. Computer Lab
6. Bus Stop

Important columns:

record_id
timestamp
facility_id
facility
queue_length
position
people_served
service_time
average_service_time
recent_service_rate
day_of_week
hour
is_weekend
is_peak_hour
wait_time
data_source


IMPORTANT:
The current 10,000-record dataset is SYNTHETIC.

It is used for:
- development
- testing
- ML pipeline development
- API integration testing

It must NOT be presented as real-world QueueLess accuracy.

Real QueueLess data must eventually replace or supplement
this development dataset.


============================================================
4. DATA GENERATION
============================================================

File:

analytics/src/data_generator.py

The generator creates realistic-looking queue records
for development.

It includes:

- Multiple facilities
- Different service speeds
- Different queue sizes
- Peak hours
- Weekend behavior
- Service rates
- Queue positions
- Wait times
- Timestamps

Current generated dataset:

10,000 records

Random seed:

42

This makes development results reproducible.


============================================================
5. DATA VALIDATION
============================================================

File:

analytics/src/data_validation.py

Validation checks include:

- Missing values
- Duplicate records
- Duplicate record IDs
- Negative queue length
- Invalid queue position
- Invalid service time
- Invalid average service time
- Negative wait time
- Required columns

Current validation result:

VALIDATION PASSED

Records checked:
10,000

Columns:
16

No data quality problems detected.


============================================================
6. DATA PREPROCESSING
============================================================

File:

analytics/src/preprocessing.py

The preprocessing pipeline:

1. Removes completely empty rows
2. Removes duplicate record IDs
3. Converts timestamps
4. Converts numeric columns
5. Removes invalid timestamps
6. Removes invalid queue records
7. Sorts records chronologically
8. Resets the dataframe index
9. Saves the cleaned dataset

Output:

analytics/data/processed/queue_data_clean.csv

Current result:

Raw records:
10,000

Clean records:
10,000

Removed:
0


============================================================
7. ANALYTICS
============================================================

File:

analytics/src/analytics.py

The analytics pipeline calculates:

Overall:

- Total records
- Average wait time
- Maximum wait time
- Average queue length
- Total people served

Facility-level:

- Average wait time
- Average queue length
- Average service time
- Total people served

Peak-hour:

- Average wait time
- Average queue length

Hourly:

- Average wait time
- Average queue length

Output:

analytics/outputs/analytics_summary.json


Current development statistics:

Average wait time:
27.62 minutes

Average queue length:
9.36 people

Maximum wait time:
131.46 minutes

Total people served:
49,313


IMPORTANT:
These statistics are from synthetic development data.


============================================================
8. FEATURE ENGINEERING
============================================================

The ML pipeline creates additional features.

Important engineered features:

queue_pressure
=
queue_length * average_service_time

people_ahead
=
position

service_rate
=
60 / average_service_time

Other features:

- day_of_week
- hour
- is_weekend
- is_peak_hour
- facility one-hot encoding


============================================================
9. MACHINE LEARNING MODEL
============================================================

Current model:

Random Forest Regressor

File:

analytics/models/queue_wait_model.pkl

Training split:

80% chronological training data
20% chronological test data

This is a TIME-AWARE split.

We do not randomly shuffle the dataset because queue
prediction should respect the time order of observations.


============================================================
10. CURRENT MODEL FEATURES
============================================================

The model currently uses:

queue_length
position
people_served
average_service_time
recent_service_rate
day_of_week
hour
is_weekend
is_peak_hour
queue_pressure
people_ahead
service_rate
facility_Admin Office
facility_Bus Stop
facility_Canteen
facility_Computer Lab
facility_Library
facility_Printing Shop


============================================================
11. MODEL PERFORMANCE
============================================================

Current Random Forest development result:

Training records:
8,000

Test records:
2,000

MAE:
2.73 minutes

RMSE:
3.25 minutes

R2:
0.9642


IMPORTANT:

These results are based on SYNTHETIC data.

The synthetic wait_time was generated using queue-related
variables, including queue length and service time.

Therefore:

R2 = 0.9642

does NOT mean:

"QueueLess is 96.42% accurate in the real world."

It only shows that the current ML pipeline works well
on the development dataset.

Real-world performance must be measured after collecting
actual QueueLess data.


============================================================
12. BASELINE MODEL
============================================================

File:

analytics/src/baseline.py

A simple baseline was created:

estimated_wait
=
position * average_service_time

Baseline result:

MAE:
13.46 minutes

RMSE:
18.43 minutes

This provides a simple reference point for evaluating the
ML model.


============================================================
13. MODEL COMPARISON
============================================================

File:

analytics/src/model_comparison.py

Models compared:

1. Linear Regression
2. Random Forest
3. Gradient Boosting

Development results:

Linear Regression:
MAE  = 2.69
RMSE = 3.17
R2   = 0.9659

Random Forest:
MAE  = 2.73
RMSE = 3.26
R2   = 0.9641

Gradient Boosting:
MAE  = 2.62
RMSE = 3.09
R2   = 0.9676

Output:

analytics/outputs/model_comparison.csv

IMPORTANT:

These results are only a synthetic-data benchmark.

The currently saved production-style prediction model remains
the Random Forest model.

Do not change the production model to Gradient Boosting
without retraining the saved model and updating the
prediction pipeline.


============================================================
14. WAIT-TIME PREDICTION
============================================================

File:

analytics/src/predict.py

The prediction function accepts:

facility
queue_length
position
people_served
average_service_time
day_of_week
hour

The pipeline calculates the required engineered features
and sends them into the trained model.


Example:

Facility:
Canteen

Queue:
30

Position:
25

People served:
80

Average service time:
2.5 minutes

Day:
2

Hour:
13


Current development prediction:

82.31 minutes


============================================================
15. PREDICTION UNCERTAINTY
============================================================

The Random Forest contains multiple decision trees.

The prediction pipeline collects predictions from the
individual trees and calculates an estimated range.

Example:

Predicted wait:
82.31 minutes

Estimated range:
77.45 - 87.68 minutes


IMPORTANT:

This is an empirical model-based prediction range.

It is NOT a calibrated statistical confidence interval.

Frontend should display it as:

"Estimated wait"

and optionally:

"Expected range"

It should NOT display:

"95% confidence"

unless a future statistically calibrated uncertainty
method is implemented.


============================================================
16. REAL DATA PIPELINE
============================================================

Real-data file:

analytics/data/external/queue_data_real.csv

Processed real-data file:

analytics/data/processed/queue_data_real_clean.csv


File:

analytics/src/real_data_loader.py


The real pipeline:

Real CSV
   |
   v
Schema validation
   |
   v
clean_data()
   |
   v
Processed real dataset


The pipeline was tested successfully.

Test records:
5

Raw:
5

Clean:
5


IMPORTANT:

The 5 records currently in the real-data CSV were only
created to test the pipeline.

They are NOT actual QueueLess observations.

When real data becomes available, these test records
must be replaced with actual collected data.


============================================================
17. RETRAINING STRATEGY
============================================================

File:

analytics/src/retraining.py

Retraining does NOT happen automatically yet.

The current system checks whether retraining should be
considered.

Current development thresholds:

Minimum new real records:
100

Maximum acceptable MAE:
10 minutes


Logic:

New real data
      |
      v
Are there at least 100 records?
      |
   NO | YES
      |
      v
Do not retrain
      |
      YES
      v
Evaluate current model on real data
      |
      v
MAE > 10 minutes?
      |
   YES       NO
    |         |
    v         v
RETRAIN    KEEP MODEL


The current 5-record test dataset correctly produces:

RETRAINING NOT REQUIRED YET

Important:
The thresholds are development values and should be reviewed
after real QueueLess data is collected.


============================================================
18. ML OUTPUT CONTRACT
============================================================

File:

analytics/src/output_contract.py

The Analytics module now produces a standardized response
for the Backend.

Example:

{
    "facility": "Canteen",
    "predicted_wait_minutes": 82.31,
    "estimated_range": {
        "lower_minutes": 77.45,
        "upper_minutes": 87.68
    },
    "prediction_unit": "minutes",
    "generated_at": "timestamp",
    "model_status": "active"
}


This is the IMPORTANT interface between:

AI / Analytics
        |
        v
Backend


Backend developers should use these field names exactly
unless the team agrees to change the contract.


============================================================
19. BACKEND — REQUIRED UPDATES
============================================================

BACKEND TEAM MUST UPDATE THE BACKEND BASED ON THIS
ANALYTICS CONTRACT.


A. Create/confirm a prediction API endpoint

Example:

POST /api/predict-wait-time


Request:

{
    "facility": "Canteen",
    "queue_length": 30,
    "position": 25,
    "people_served": 80,
    "average_service_time": 2.5,
    "day_of_week": 2,
    "hour": 13
}


Response:

{
    "facility": "Canteen",
    "predicted_wait_minutes": 82.31,
    "estimated_range": {
        "lower_minutes": 77.45,
        "upper_minutes": 87.68
    },
    "prediction_unit": "minutes",
    "generated_at": "timestamp",
    "model_status": "active"
}


B. Backend must validate input

At minimum:

queue_length >= 0
position >= 0
position <= queue_length
average_service_time > 0
facility must be a valid facility


C. Backend should NOT calculate the ML prediction itself.

Backend responsibility:

- Receive user/queue information
- Send valid input to Analytics/ML
- Receive prediction
- Return prediction to Frontend


D. Backend should preserve the prediction structure.

Do not rename:

predicted_wait_minutes

estimated_range

lower_minutes

upper_minutes

without informing the AI and Frontend developers.


E. Backend should handle ML errors.

Example:

If ML service/model is unavailable:

Return a controlled API error instead of crashing.


F. Backend should store useful historical information.

Eventually store:

- facility
- queue_length
- position
- predicted_wait
- actual_wait
- timestamp

Actual wait time is important for future model evaluation
and retraining.


============================================================
20. FRONTEND — REQUIRED UPDATES
============================================================

FRONTEND TEAM MUST UPDATE THE UI TO USE THE NEW ML OUTPUT.


A. Display predicted waiting time.

Example:

Estimated Wait

82 min


B. Display estimated range.

Example:

Expected range:
77 - 88 min


C. Show the facility.

Example:

Canteen


D. Show queue information.

Example:

People waiting:
30

Your position:
25


E. Show prediction status if useful.

Example:

AI prediction active


F. Do NOT display technical ML information to normal users.

Do NOT show:

R2
MAE
RMSE
model name
feature importance
training records


Those are developer/analytics metrics, not user-facing
information.


G. Handle loading state.

Example:

Calculating wait time...


H. Handle API failure.

Example:

"Wait-time prediction is temporarily unavailable."


I. Handle no queue.

If:

queue_length = 0

Frontend should show something like:

"No queue right now"


J. Update automatically when queue information changes.

If the backend sends a new prediction, frontend should
refresh the displayed wait time.


============================================================
21. IMPORTANT FRONTEND USER EXPERIENCE
============================================================

The QueueLess user should eventually see something similar
to:

------------------------------------------------------------

CANTEEN

People waiting:
30

Your position:
25

Estimated wait:
82 min

Expected range:
77 - 88 min

Prediction updated:
Just now

------------------------------------------------------------


The UI should be simple and easy to understand.


============================================================
22. BACKEND ↔ AI ↔ FRONTEND FLOW
============================================================

FINAL EXPECTED ARCHITECTURE:


                    FRONTEND
                       |
                       |
                 Queue information
                       |
                       v
                    BACKEND
                       |
                       |
                Prediction request
                       |
                       v
                AI / ANALYTICS
                       |
                       v
                ML MODEL
                       |
                       v
                Prediction
                       |
                       v
                    BACKEND
                       |
                       v
                   FRONTEND
                       |
                       v
              User sees wait time


============================================================
23. CURRENT AI FILE RESPONSIBILITIES
============================================================

data_generator.py
-----------------
Creates development queue data.


data_validation.py
------------------
Checks data quality.


preprocessing.py
----------------
Cleans and prepares datasets.


analytics.py
------------
Generates queue analytics.


features.py
-----------
Contains feature engineering logic.


baseline.py
-----------
Creates a simple non-ML baseline.


train.py
--------
Trains and saves the Random Forest model.


model_comparison.py
-------------------
Compares ML algorithms.


predict.py
----------
Loads the model and predicts waiting time.


output_contract.py
------------------
Defines the standard AI -> Backend output.


real_data_loader.py
-------------------
Loads and processes real QueueLess data.


retraining.py
-------------
Checks whether model retraining should be considered.


============================================================
24. COMMANDS FOR AI / ANALYTICS
============================================================

Generate development data:

python analytics\src\data_generator.py


Validate data:

python analytics\src\data_validation.py


Preprocess:

python analytics\src\preprocessing.py


Run analytics:

python analytics\src\analytics.py


Run baseline:

python analytics\src\baseline.py


Train model:

python analytics\src\train.py


Compare models:

python analytics\src\model_comparison.py


Run prediction:

python analytics\src\predict.py


Test real-data pipeline:

python analytics\src\real_data_loader.py


Check retraining:

python analytics\src\retraining.py


Test output contract:

python analytics\src\output_contract.py


============================================================
25. CURRENT STATUS
============================================================

1. Dataset schema
   COMPLETE

2. Synthetic data generation
   COMPLETE

3. Data validation
   COMPLETE

4. Analytics / EDA
   COMPLETE

5. Baseline
   COMPLETE

6. Model comparison
   COMPLETE

7. Time-aware validation
   COMPLETE

8. Feature engineering
   COMPLETE

9. Prediction uncertainty
   COMPLETE

10. Real-data pipeline
    COMPLETE

11. Retraining strategy
    DEVELOPMENT VERSION COMPLETE

12. ML output contract
    COMPLETE

13. Documentation
    IN PROGRESS

14. Git commit
    PENDING

15. Git push
    PENDING

16. Pull Request
    PENDING

17. Backend integration
    PENDING

18. Frontend integration
    PENDING


============================================================
26. IMPORTANT LIMITATIONS
============================================================

1. Current ML model was developed using synthetic data.

2. Current accuracy metrics do not represent production
   QueueLess accuracy.

3. The current retraining thresholds are development values.

4. Prediction uncertainty is not statistically calibrated.

5. Real QueueLess data is required for reliable production
   evaluation.

6. Backend and frontend must follow the output contract.

7. Changes to model input/output fields must be communicated
   between AI, Backend, and Frontend developers.


============================================================
27. IMMEDIATE TEAM ACTION ITEMS
============================================================

AI / ANALYTICS:
- Finish documentation
- Run final tests
- Commit analytics changes
- Push branch
- Create Pull Request
- Share ML output contract with Backend


BACKEND:
- Create/confirm prediction endpoint
- Accept prediction input fields
- Connect to AI/Analytics prediction system
- Return standardized prediction response
- Store prediction + actual wait data
- Add validation and error handling


FRONTEND:
- Consume prediction API
- Display predicted wait
- Display estimated range
- Display queue position
- Display people waiting
- Add loading state
- Add error state
- Refresh prediction when queue changes


============================================================
28. DO NOT BREAK THESE INTERFACES
============================================================

AI INPUT:

facility
queue_length
position
people_served
average_service_time
day_of_week
hour


AI OUTPUT:

facility
predicted_wait_minutes
estimated_range.lower_minutes
estimated_range.upper_minutes
prediction_unit
generated_at
model_status


If any field needs to be changed:

STOP AND INFORM:
AI + BACKEND + FRONTEND


============================================================
END OF AI / ANALYTICS HANDOFF DOCUMENT
============================================================

----------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------


yes — Backend + Frontend need updates right now

This is the important part. Your AI work is no longer isolated. The three of you should now work in parallel:

Backend teammate — immediate work
1. Prediction API endpoint
2. Request validation
3. Connect AI prediction
4. Return the output contract
5. Store prediction + actual wait data

The backend should ultimately accept something like:

{
  "facility": "Canteen",
  "queue_length": 30,
  "position": 25,
  "people_served": 80,
  "average_service_time": 2.5,
  "day_of_week": 2,
  "hour": 13
}

and return:

{
  "facility": "Canteen",
  "predicted_wait_minutes": 82.31,
  "estimated_range": {
    "lower_minutes": 77.45,
    "upper_minutes": 87.68
  },
  "prediction_unit": "minutes",
  "generated_at": "2026-10-02T17:10:32",
  "model_status": "active"
}
Frontend teammate — immediate work

The UI should now have space for:

┌──────────────────────────────┐
│ CANTEEN                      │
│                              │
│ People waiting: 30           │
│ Your position: 25            │
│                              │
│ Estimated Wait               │
│ 82 min                       │
│                              │
│ Expected range               │
│ 77 – 88 min                  │
│                              │
│ ● Updated just now           │
└──────────────────────────────┘

And they need loading + error + empty queue states.

One important thing

Don't ask your teammates to integrate the current Python predict.py directly into the frontend.

The intended architecture is:

FRONTEND
   ↓
BACKEND API
   ↓
AI / ML
   ↓
MODEL
   ↓
AI RESULT
   ↓
BACKEND
   ↓
FRONTEND

----------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------
