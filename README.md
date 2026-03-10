<div align="center">

![Banner](docs/banner.png)

# 🚦 AI-Based Traffic Violation Detection & Auto-Challan System

**An automated platform that detects traffic violations using computer vision, reads number plates with OCR, and issues digital challans — with minimal human intervention.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react)](https://react.dev)
[![SQLite](https://img.shields.io/badge/SQLite-local%20DB-lightblue?logo=sqlite)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

</div>

---

## 📖 Table of Contents

1. [What is this project?](#-what-is-this-project)
2. [How it works](#-how-it-works)
3. [User Roles](#-user-roles)
4. [Project Structure](#-project-structure)
5. [Getting Started (Step-by-Step)](#-getting-started-step-by-step)
6. [Backend API Reference](#-backend-api-reference)
7. [Database Schema](#-database-schema)
8. [Configuration](#-configuration)
9. [FAQ for Beginners](#-faq-for-beginners)

---

## 🤖 What is this project?

This is a **full-stack AI system** that automates traffic law enforcement:

- 📷 Traffic cameras capture footage
- 🧠 A **YOLO AI model** detects violations (no helmet, red light jump, wrong lane, triple riding)
- 🔤 **EasyOCR** reads the vehicle number plate
- ⚡ If the AI is **confident** → challan is **auto-approved instantly**
- 🧐 If the AI is **uncertain** → the case goes to a **Traffic Officer** for manual review
- 📲 The vehicle owner gets a **notification** when a challan is issued

> **No AI model files?** No problem! The server still starts and all management endpoints work. Only the live camera inference will return a 503 error.

---

## 🔄 How it Works

![Architecture](docs/architecture.png)

```
Traffic Camera Feed
       ↓
  AI Model (YOLO)
       ↓
  Confidence Score
       ↓
┌──────────────────────────────┐
│  confidence ≥ threshold ?    │
└──────────┬───────────────────┘
          YES                NO
           ↓                  ↓
     APPROVED            UNDER_REVIEW
  (Auto Challan)      (Officer Reviews)
       ↓                     ↓
  Notification         Officer Approves
  sent to user          or Declines
                             ↓
                        Notification
                        sent to user
```

---

## 👥 User Roles

![User Roles](docs/user_roles.png)

| Role | What they can do |
|------|-----------------|
| 🧑 **User** | View their challans, see notifications, pay fines |
| 👮 **Officer** | Review uncertain cases, approve or decline challans |
| 🛡️ **Admin** | Manage cameras/locations, update thresholds, view audit logs, see all violations |

---

## 📁 Project Structure

```
traffic-violation-backend/
│
├── single_app.py          ← 🐍 Entire backend in one file (FastAPI + SQLAlchemy)
├── traffic.db             ← 🗄️  SQLite database (auto-created on first run)
├── evidence_uploads/      ← 📂 Uploaded evidence images/videos stored here
├── docs/                  ← 🖼️  README images
│
├── frontend/              ← ⚛️  React frontend
│   ├── src/
│   │   └── App.jsx        ← Main UI (Login, Admin, Officer, User views)
│   └── package.json
│
├── .env                   ← 🔐 Environment variables (DB URL, model paths)
├── requirements.txt       ← 📦 Python dependencies
└── README.md              ← 📖 This file
```

---

## 🚀 Getting Started (Step-by-Step)

### Prerequisites

Make sure you have these installed:
- **Python 3.10+** → [Download](https://python.org/downloads)
- **Node.js 20.19+** → [Download](https://nodejs.org)
- **Git** → [Download](https://git-scm.com)

---

### Step 1 — Clone the Project

```bash
git clone https://github.com/your-username/traffic-violation-backend.git
cd traffic-violation-backend
```

---

### Step 2 — Set Up Python Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
.\venv\Scripts\Activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic python-multipart
pip install ultralytics opencv-python numpy easyocr torch torchvision
```

> **💡 Tip:** If you don't have GPU support, the above works on CPU too — just slower for inference.

---

### Step 3 — Configure Environment Variables

Create a `.env` file (or edit the existing one):

```env
# Database (SQLite by default — no setup needed!)
DATABASE_URL=sqlite+aiosqlite:///./traffic.db

# Optional: Path to YOLO model files (leave blank to skip AI inference)
HELMET_MODEL_PATH=helmet_model.pt
TRAFFIC_MODEL_PATH=traffic_model.pt
PLATE_MODEL_PATH=plate_model.pt
```

> **💡 Don't have model files?** Skip this — the server runs fine without them. Only `/api/inference/run` will return a 503 error.

---

### Step 4 — Start the Backend

```bash
uvicorn single_app:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
[INFO] Default thresholds seeded into system_settings.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ Visit **http://localhost:8000/docs** to see the interactive API documentation!

---

### Step 5 — Set Up the Frontend

```bash
cd frontend
npm install
npm run dev
```

✅ Visit **http://localhost:5173** to use the web interface!

---

### Step 6 — Log In

Use these demo credentials:

| Email | Password | Role |
|-------|----------|------|
| `admin@test.com` | `anything` | Admin |
| `officer@test.com` | `anything` | Officer |
| `user@test.com` | `anything` | User |

> **How login works:** The system auto-creates a user if the email doesn't exist. Role is determined by the keyword in the email (`admin`, `officer`, or default `user`).

---

### Step 7 — Test the Full Flow

```bash
# 1. Submit a violation (as admin)
curl -X POST http://localhost:8000/api/inference/result \
  -H "X-Role: ADMIN" \
  -H "X-User-Id: <your-admin-uuid>" \
  -H "Content-Type: application/json" \
  -d '{
    "violation_type": "NO_HELMET",
    "detection_confidence": 0.95,
    "is_uncertain": false,
    "plate_text_raw": "AP12AB1234",
    "occurred_at": "2026-03-09T10:00:00"
  }'

# Response: { "status": "APPROVED", "challan_id": "..." }

# 2. Submit a low-confidence violation → goes to officer review
curl -X POST http://localhost:8000/api/inference/result \
  -H "X-Role: ADMIN" ... \
  -d '{ "violation_type": "TRIPLE_RIDING", "detection_confidence": 0.45 ... }'

# Response: { "status": "UNDER_REVIEW", ... }
```

---

## 📚 Backend API Reference

### 🔐 Authentication
All endpoints (except `/health`) require these **request headers**:

| Header | Values | Description |
|--------|--------|-------------|
| `X-Role` | `ADMIN` / `OFFICER` / `USER` | Your role |
| `X-User-Id` | UUID string | Your user ID (from login) |

---

### Core Endpoints

| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/health` | GET | - | Server health check |
| `/api/login` | POST | - | Login (creates user if needed) |
| `/api/inference/result` | POST | Admin | Submit AI detection result → auto challan |
| `/api/inference/run` | POST | Admin | Run AI on uploaded image (needs model files) |

### Admin Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/dashboard` | GET | Stats: total violations, pending, approved |
| `/admin/settings` | GET | View all thresholds (`NO_HELMET`, `RED_LIGHT`, etc.) |
| `/admin/settings/{key}` | PUT | Update a threshold value live |
| `/admin/audit-logs` | GET | View all system actions (audit trail) |

### Camera & Location

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/locations` | GET | List all locations |
| `/locations` | POST | Add a new location |
| `/cameras` | GET | List all cameras |
| `/cameras` | POST | Add a new camera |
| `/cameras/{id}/status` | PATCH | Set camera to ACTIVE / INACTIVE / MAINTENANCE |

### Officer Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/officer/review-queue` | GET | Get all UNDER_REVIEW challans |
| `/officer/challans/{id}/approve` | POST | Approve a challan → sends notification |
| `/officer/challans/{id}/decline` | POST | Decline a challan → sends notification |

### User Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/user/challans` | GET | User's approved challans |
| `/user/notifications` | GET | User's IN_APP notifications |

### Evidence

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/violations/{id}/evidence` | POST | Upload image/video evidence |
| `/violations/{id}/evidence` | GET | List evidence for a violation |

---

## 🗄️ Database Schema

The system uses **12 tables**:

```
users                 → Stores admins, officers, and vehicle owners
vehicles              → Registered vehicles (linked to users)
locations             → GPS locations of cameras
cameras               → Camera registry with status
model_runs            → AI model version tracking
violations            → Every detected violation
evidence_assets       → Images/videos linked to violations
challans              → Issued challans with approve/under_review/declined status
challan_decisions     → Audit trail of officer decisions
notifications         → In-app / SMS / email notifications
audit_logs            → Every system action logged
system_settings       → Configurable thresholds (NO_HELMET → 0.75, etc.)
```

---

## ⚙️ Configuration

### Violation Thresholds

These control whether a violation is **auto-approved** or sent for **officer review**:

| Violation | Default Threshold | Meaning |
|-----------|-------------------|---------|
| `NO_HELMET` | `0.75` | AI must be 75%+ confident |
| `RED_LIGHT` | `0.80` | AI must be 80%+ confident |
| `WRONG_LANE` | `0.70` | AI must be 70%+ confident |
| `TRIPLE_RIDING` | `0.75` | AI must be 75%+ confident |

**Update a threshold live** (no restart required):
```bash
curl -X PUT "http://localhost:8000/admin/settings/NO_HELMET?value=0.85" \
  -H "X-Role: ADMIN" -H "X-User-Id: <uuid>"
```

### Using PostgreSQL (Production)

Change the `DATABASE_URL` in `.env`:
```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/traffic_db
```

---

## ❓ FAQ for Beginners

**Q: I don't have YOLO model files. Can I still run the project?**
> Yes! The server starts fine. Only `/api/inference/run` (live image detection) will return 503. All other endpoints — login, dashboards, officer review, evidence upload — work normally.

**Q: What is SQLite? Do I need to install it?**
> SQLite is a file-based database. No installation needed — it's built into Python. The database file `traffic.db` is auto-created when you first start the server.

**Q: The frontend says "0 violations". Is that normal?**
> Yes! The database is empty until you submit a violation via `POST /api/inference/result`.

**Q: How do I connect to a real database in production?**
> Set the `DATABASE_URL` environment variable to your PostgreSQL URL. See the [Configuration](#️-configuration) section.

**Q: How does vehicle-to-user matching work?**
> When a challan is created with a plate like `AP12AB1234`, the system looks up `vehicles.vehicle_number`. If found, `user_id` is automatically assigned to the challan and the user gets a notification.

**Q: Where is evidence stored?**
> Evidence files are saved in the `evidence_uploads/` folder next to `single_app.py`. For production, replace with S3 or another cloud storage.

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -m "Add new feature"`
4. Push and create a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

Built with ❤️ using FastAPI, React, SQLAlchemy, YOLO & EasyOCR

</div>
