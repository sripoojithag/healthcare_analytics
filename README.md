# Healthcare Data Warehouse & Analytics Platform

An enterprise-grade, portfolio-ready healthcare analytics and data warehousing platform engineered from the UCI Diabetes 130-US Hospitals (1999–2008) dataset (101,766 inpatient encounters).

---

## 1. System Architecture

```
[ Raw Healthcare Data (CSV) ]
             │
             ▼
[ Ingestion & Schema Guard ] ──► Validates 50 expected attributes, tracks errors, rejects invalid IDs
             │
             ▼
[ ETL & Data Quality Pipeline ] ──► Cleans sentinels ('?'), imputes categoricals, standardizes medications,
             │                     generates data quality audit reports
             ▼
[ Star Schema Data Warehouse ] ──► FactEncounter, DimPatient, DimDiagnosis, DimEncounterContext
             │
             ├──► [ SQL Analytics Engine ] (CTEs, Window Functions, Dimensional Joins)
             │
             └──► [ FastAPI Microservices ]
                     ├── Health & Warehouse Status (`/api/v1/health`)
                     ├── Ingestion & File Upload (`/api/v1/ingestion/upload`)
                     ├── Data Quality Audits (`/api/v1/quality/summary`)
                     ├── Clinical & Readmission Analytics (`/api/v1/analytics/*`)
                     └── HIPAA-Aligned Masked Encounters (`/api/v1/encounters`)
```

---

## 2. Data Warehouse Star Schema

The data warehouse models 101,766 hospital encounters into an optimized Star Schema:

### Dimensions
* **`dim_patient`**: Natural patient identifier (`patient_nbr`), race, gender, age bracket (`age_group`), weight.
* **`dim_diagnosis`**: Unique ICD-9 codes mapped into standardized clinical diagnostic chapters (Circulatory, Respiratory, Diabetes, Digestive, Genitourinary, Neoplasms, Injury, Musculoskeletal, Other).
* **`dim_encounter_context`**: Admission type, discharge disposition, admission source, payer code, and medical specialty.

### Fact Table
* **`fact_encounter`**: Central inpatient encounter facts.
  - Foreign keys: `patient_key`, `primary_diag_key`, `context_key`
  - Metrics: `time_in_hospital`, `num_lab_procedures`, `num_procedures`, `num_medications`, `number_outpatient`, `number_emergency`, `number_inpatient`, `number_diagnoses`
  - Glycemic indicators: `max_glu_serum`, `a1c_result`
  - Medications: `metformin`, `insulin`, `diabetes_med`, `change`
  - Targets: `readmitted`, `readmitted_binary` (0/1), `readmitted_30d` (0/1)
  - Composite indexes for fast query performance.

---

## 3. SQL Analytics Suite

* **`sql/warehouse_ddl.sql`**: Full ANSI SQL & Azure SQL compatible DDL for dimension and fact tables, primary/foreign keys, and indexes.
* **`sql/warehouse_analytics.sql`**: Advanced analytical queries demonstrating CTEs, aggregations, and window functions (`RANK()`, `DENSE_RANK()`).
* **`sql/analytics_queries.sql`**: Preserved original exploratory queries from earlier research.

---

## 4. Setup & Local Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Run ETL & Database Migration
```bash
python3 -c "
from src.warehouse.db import init_db, SessionLocal
from src.warehouse.loader import load_cleaned_data_to_warehouse
from src.etl.cleaner import clean_healthcare_data
import pandas as pd

init_db()
print('Initializing Star Schema Data Warehouse...')
df = pd.read_csv('data/diabetic_data.csv', nrows=5000)
cleaned, metrics = clean_healthcare_data(df)
session = SessionLocal()
results = load_cleaned_data_to_warehouse(cleaned, session)
print('Loaded into warehouse:', results)
session.close()
"
```

### 3. Launch FastAPI Server
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation: `http://localhost:8000/docs`

---

## 5. Automated Testing (pytest)

Run the automated test suite across unit, integration, and API tests:

```bash
# Run all tests
pytest

# Run with test coverage
pytest --cov=src --cov-report=term-missing
```

### Test Suite Structure
```text
tests/
├── unit/
│   ├── test_baseline.py       # Validates assets, schema, original files
│   ├── test_etl.py            # Tests CSV ingestion, schema validation, cleaner
│   ├── test_data_quality.py   # Tests missingness, completeness, validity checks
│   ├── test_ml.py             # Tests ML pipeline, inference, and classification metrics
│   └── test_dsa.py            # Tests Heap Priority Queue & Graph Traversal (BFS/DFS)
├── integration/
│   └── test_warehouse.py      # Tests Star Schema, ETL loader, ORM, SQL analytics
└── api/
    ├── test_health_api.py     # Tests /api/v1/health & root discovery
    ├── test_analytics_api.py  # Tests /api/v1/analytics/kpis, age, stay, meds, predict
    ├── test_encounters_api.py # Tests /api/v1/encounters & HIPAA masking
    ├── test_ingestion_api.py  # Tests /api/v1/ingestion/upload validation
    ├── test_data_quality_api.py # Tests /api/v1/quality/summary
    ├── test_security_api.py   # Tests RBAC authorization and audit trail logging
    └── test_dsa_api.py        # Tests triage priority queue & graph traversal endpoints
```

---

## 6. Machine Learning Pipeline (Phase 5)

* **Leak-free Feature Engineering**: Target variables (`readmitted`, `readmitted_30d`) and identifiers (`encounter_id`, `patient_nbr`) are strictly excluded during feature assembly.
* **Architecture**: Scikit-learn `Pipeline` pairing `ColumnTransformer` (`StandardScaler` for numeric clinical features, `OneHotEncoder` for demographic and medication columns) with a `RandomForestClassifier`.
* **Classification Evaluation**: Beyond accuracy, models are rigorously evaluated with Precision, Recall, F1 score, ROC-AUC, and Confusion Matrix.
* **Versioned Artifacts**: Pre-trained model pipeline and training metadata are saved to `models/readmission_pipeline_v1.joblib` and `models/model_metadata.json`.
* **Real Inference in Streamlit**: The legacy Streamlit application (`app/application.py`) has been upgraded from a dummy heuristic to real Scikit-learn model inference via `predict_readmission_risk`.

### Retraining & Evaluation CLI
```bash
python3 src/ml/pipeline.py --train --eval --sample-size 15000
```

### Running Streamlit Live App
```bash
streamlit run app/application.py
```

---

## 7. React + TypeScript Platform Dashboard (Phase 6)

The frontend is a modern, modular React 19 + TypeScript dashboard communicating directly with the FastAPI endpoints and data warehouse:
* **Interactive KPI Cards**: Display total encounters, unique patients, 30-day readmission rate, and average length of stay.
* **Dynamic Cohort Charts**: Age cohort readmission bars and length-of-stay distribution charts rendered with Recharts.
* **Clinical Diagnostic Risk Breakdown**: Grouped ICD-9 diagnostic chapters with risk volume and prevalence.
* **Data Quality & Governance Panel**: Column-level completeness, duplicate detection, and validation metrics.
* **Bedside Risk Predictor**: Live risk simulation with low, medium, and high alert tier badges.
* **HIPAA-Masked Encounters Table**: Pagination and search with de-identified patient numbers (`PT-***{suffix}`).
* **Empty / Error / Loading States**: Comprehensive state management powered by `@tanstack/react-query`.

### Running React Dashboard
```bash
npm run dev
# Dashboard launches at http://localhost:3000
```

---

## 8. Security, RBAC & Audit Trail (Phase 7)

* **Role-Based Access Control (RBAC)**: Supports three distinct roles:
  * `viewer`: Read-only aggregate KPIs and analytical charts. Sensitive patient-level encounter listings and audit logs are restricted (403 Forbidden).
  * `analyst`: Access to analytics, predictive scoring, and de-identified patient encounters.
  * `admin`: Complete privileges including CSV ingestion uploads (`/api/v1/ingestion/upload`) and audit trail inspection (`/api/v1/audit/logs`).
* **Header-Based Authentication**: Role passed via `X-User-Role: viewer | analyst | admin` (or Bearer tokens in production).
* **PHI-Safe Audit Logging**: Thread-safe in-memory audit store captures timestamp, user, role, action, and target endpoint without persisting sensitive patient data.
* **CORS Security**: Configurable via `CORS_ORIGINS` environment variable (defaults to local preview ports).

---

## 9. Data Structures & Algorithms (Phase 8)

The platform demonstrates two tested, domain-relevant DSA components solving real clinical workflow bottlenecks:

### 1. Heap-Based Clinical Triage Priority Queue (`src/dsa/priority_queue.py`)
* **Clinical Problem**: Discharge planners and case managers have limited daily bandwidth. Patients must be triaged dynamically so the highest-risk individuals receive reviews first.
* **Multi-tiered Tie-Breaking Rules**:
  1. Primary: Predicted 30-day readmission risk probability (descending).
  2. Secondary: Length of hospital stay in days (descending; complex long-stay patients prioritized).
  3. Tertiary: Inpatient medication count (descending; polypharmacy risk).
  4. Quaternary: Monotonic FIFO sequence ID (guarantees deterministic ordering for identical metrics).
* **Complexity**:
  * **Enqueue**: $O(\log N)$ time, $O(1)$ auxiliary space.
  * **Dequeue**: $O(\log N)$ time, $O(1)$ auxiliary space.
  * **Peek**: $O(1)$ time, $O(1)$ auxiliary space.
  * **Space Complexity**: $O(N)$ total space for $N$ queued encounters.

### 2. Clinical Co-morbidity Graph Traversal (`src/dsa/graph.py`)
* **Clinical Problem**: Diabetic patients frequently present with multi-organ co-morbidities (circulatory disorders, renal complications, neuropathy, retinopathy). A graph abstraction maps disease transitions and progression pathways.
* **Algorithms**:
  * **Breadth-First Search (BFS)**: Level-order exploration discovering immediate co-occurring conditions first; calculates shortest diagnostic path between two conditions.
  * **Depth-First Search (DFS)**: Deep progression pathway exploration; supports both recursive and iterative implementations.
  * **Cycle Safety**: Uses $O(1)$ hash-set visited tracking to avoid infinite loops in circular clinical relationships.
  * **Disconnected Component Handling**: Partitions isolated conditions (e.g., eye disorders or rare conditions) into independent connected subgraphs.
* **Complexity**:
  * **BFS & DFS**: $O(V + E)$ time, $O(V)$ space.
  * **Shortest Path**: $O(V + E)$ time, $O(V)$ space.

---

## 10. Docker & Azure Cloud Deployment (Phase 9)

### Local Docker Multi-Container Development
Run the complete full-stack environment (FastAPI Backend + React Nginx Frontend) with one command:

```bash
# Build and launch all containers
docker-compose up --build

# Backend API:    http://localhost:8000 (Docs at /docs)
# Frontend SPA:   http://localhost:3000
```

### Production Azure Deployment
For complete production deployment instructions using **Azure Container Apps**, **Azure SQL Database (Serverless)**, and **Azure Key Vault**, see:
* **[Azure Deployment Architecture Guide](docs/azure_deployment.md)**

> *Note*: Azure deployment is fully optional. Local development operates out of the box with zero external cloud dependencies and zero cloud costs.

---

## 11. Admin Panel & Data Management System

A production-grade, secure **Admin Panel and Data Management System** governs access, dataset lifecycle, and model inference without redeploying code:

### 1. Cryptographic Authentication & Server-Enforced RBAC
* **PBKDF2-HMAC-SHA256**: Passwords hashed using 100,000 iterations and 16-byte random salt. Plaintext passwords never stored.
* **Signed Bearer Tokens**: Session tokens signed with HMAC-SHA256, expiration tracking, and an in-memory token revocation blacklist for instant logout invalidation.
* **Seed Accounts & Environment Overrides**:
  * Admin: `admin@healthcare.local` (Default: `AdminSecure#2026!`, configurable via `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD`).
  * Analyst: `analyst@healthcare.local` (`AnalystSecure#2026!`).
  * Viewer: `viewer@healthcare.local` (`ViewerSecure#2026!`).
* **Server-Authoritative Enforcement**: Frontend role switcher removed. All permissions enforced by backend `@router` dependencies (`require_role`).

### 2. Administrator Governance & Lockout Protection
* **Self-Demotion Safeguard**: An administrator cannot demote their own account to prevent accidental lockout.
* **Last-Active-Admin Protection**: The system prevents demoting or deactivating the last active administrator.
* **User Management**: Administrators can create new accounts, assign roles (`admin`, `analyst`, `viewer`), toggle account activation, and perform password resets.

### 3. Data Ops, Ingestion Modes & Dataset Deletion
* **Pre-Flight CSV Inspection**: Previews the first 5 records, detects columns, and flags missing schema attributes.
* **Append Mode (Default)**: Ingests new records and deduplicates against `encounter_id` to prevent duplicate hospital records.
* **Replace Mode (Transactional)**: Stages and validates new datasets in memory before replacing active warehouse data. Requires explicit confirmation.
* **Dataset Deletion & Empty State**: Allows administrators to purge active clinical records while preserving immutable audit logs and ingestion manifests. Requires entering the confirmation phrase `"DELETE ACTIVE DATASET"`. Dashboards automatically render graceful empty states without division-by-zero errors.

### 4. Dynamic Model Management & System Health
* **Model Artifact Switching**: Inspect accuracy, F1-score, and ROC-AUC metrics for versioned models (`readmission_pipeline_v1.joblib`) and dynamically set active inference models.
* **Immutable Audit Trail**: Append-only log recording authentications, role updates, uploads, and data deletions with client IP and timestamps.
* **System Status Health Check**: Real-time heartbeat endpoint reporting database connectivity, active encounter volume, and model loading state without exposing credentials.

