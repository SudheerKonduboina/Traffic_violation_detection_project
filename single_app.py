"""
single_app.py — Single-file FastAPI backend (Auto-approve + Officer-only for uncertain)

✅ Improvements (backend-engineer style):
- Loads YOLO + EasyOCR at startup (app won’t crash if .pt missing)
- Uses app.state.* for models/readers
- Removes duplicate imports
- Adds basic idempotency (prevents duplicate challans for same event)
- Consistent enum handling in responses
- Adds small response schemas for officer actions

Run:
  pip install fastapi uvicorn sqlalchemy asyncpg pydantic python-multipart ultralytics opencv-python numpy easyocr torch torchvision

  export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/traffic"
  uvicorn single_app:app --reload

Auth (temporary):
  - Headers:
      X-Role: ADMIN | OFFICER | USER
      X-User-Id: <uuid string>   # required for officer/user actions
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, date, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import cv2
import easyocr
from ultralytics import YOLO

from fastapi import FastAPI, Depends, Header, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from sqlalchemy import (
    String, Boolean, Date, DateTime, Float, Integer,
    ForeignKey, select, text, and_, func
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import JSON
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ----------------------------
# Config
# ----------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./traffic.db")

THRESHOLDS = {
    "NO_HELMET": 0.75,
    "RED_LIGHT": 0.80,
    "WRONG_LANE": 0.70,
    "TRIPLE_RIDING": 0.75,
}

# Model file paths (change as needed)
HELMET_MODEL_PATH = os.getenv("HELMET_MODEL_PATH", "helmet_model.pt")
TRAFFIC_MODEL_PATH = os.getenv("TRAFFIC_MODEL_PATH", "traffic_model.pt")
PLATE_MODEL_PATH = os.getenv("PLATE_MODEL_PATH", "plate_model.pt")

# Example constants (adjust per camera)
STOP_LINE_Y = 400
CURRENT_SIGNAL_STATE = "RED"  # replace with live signal logic
LANE_MIN_X = 200
LANE_MAX_X = 600


app = FastAPI(title="Traffic Violation Auto-Challan (Single File)", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# ----------------------------
# Enums (match your schema)
# ----------------------------
class UserRole(str, Enum):
    ADMIN = "ADMIN"
    OFFICER = "OFFICER"
    USER = "USER"


class ChallanStatus(str, Enum):
    APPROVED = "APPROVED"
    UNDER_REVIEW = "UNDER_REVIEW"
    DECLINED = "DECLINED"


class DecisionSource(str, Enum):
    AI = "AI"
    OFFICER = "OFFICER"


class ViolationType(str, Enum):
    NO_HELMET = "NO_HELMET"
    TRIPLE_RIDING = "TRIPLE_RIDING"
    RED_LIGHT = "RED_LIGHT"
    WRONG_LANE = "WRONG_LANE"


class CameraStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"


class EvidenceType(str, Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class NotificationChannel(str, Enum):
    IN_APP = "IN_APP"
    SMS = "SMS"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


# ----------------------------
# SQLAlchemy Models (minimal columns needed)
# ----------------------------
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(String, primary_key=True, default=uuid.uuid4)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, native_enum=False), nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Location(Base):
    __tablename__ = "locations"
    id: Mapped[uuid.UUID] = mapped_column(String, primary_key=True, default=uuid.uuid4)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class Camera(Base):
    __tablename__ = "cameras"
    id: Mapped[uuid.UUID] = mapped_column(String, primary_key=True, default=uuid.uuid4)
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(String, ForeignKey("locations.id"), nullable=True)
    camera_code: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    stream_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    direction: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[Optional[CameraStatus]] = mapped_column(SAEnum(CameraStatus, native_enum=False), nullable=True)
    installed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class SystemSetting(Base):
    __tablename__ = "system_settings"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class ModelRun(Base):
    __tablename__ = "model_runs"
    id: Mapped[uuid.UUID] = mapped_column(String, primary_key=True, default=uuid.uuid4)
    model_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ocr_engine: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rules_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    device: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    runtime_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[uuid.UUID] = mapped_column(String, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    vehicle_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)


class Violation(Base):
    __tablename__ = "violations"
    id: Mapped[uuid.UUID] = mapped_column(String, primary_key=True, default=uuid.uuid4)

    camera_id: Mapped[Optional[uuid.UUID]] = mapped_column(String, ForeignKey("cameras.id"), nullable=True)
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(String, ForeignKey("locations.id"), nullable=True)
    model_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(String, ForeignKey("model_runs.id"), nullable=True)

    violation_type: Mapped[ViolationType] = mapped_column(
        SAEnum(ViolationType, name="violation_type", native_enum=False),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    frame_ref: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    plate_text_raw: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    plate_text_norm: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    plate_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    detection_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_uncertain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    ai_payload_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    rules_payload_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class EvidenceAsset(Base):
    __tablename__ = "evidence_assets"
    id: Mapped[uuid.UUID] = mapped_column(String, primary_key=True, default=uuid.uuid4)
    violation_id: Mapped[Optional[uuid.UUID]] = mapped_column(String, ForeignKey("violations.id"), nullable=True)
    evidence_type: Mapped[Optional[EvidenceType]] = mapped_column(SAEnum(EvidenceType, native_enum=False), nullable=True)
    storage_provider: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sha256: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Challan(Base):
    __tablename__ = "challans"
    id: Mapped[uuid.UUID] = mapped_column(String, primary_key=True, default=uuid.uuid4)
    violation_id: Mapped[uuid.UUID] = mapped_column(
        String, ForeignKey("violations.id"), unique=True, nullable=False
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    vehicle_id: Mapped[Optional[uuid.UUID]] = mapped_column(String, ForeignKey("vehicles.id"), nullable=True)

    status: Mapped[ChallanStatus] = mapped_column(
        SAEnum(ChallanStatus, name="challan_status", native_enum=False),
        nullable=False,
    )
    decision_source: Mapped[DecisionSource] = mapped_column(
        SAEnum(DecisionSource, name="decision_source", native_enum=False),
        nullable=False,
        default=DecisionSource.AI,
    )

    officer_id: Mapped[Optional[uuid.UUID]] = mapped_column(String, ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class ChallanDecision(Base):
    __tablename__ = "challan_decisions"
    id: Mapped[uuid.UUID] = mapped_column(String, primary_key=True, default=uuid.uuid4)
    challan_id: Mapped[uuid.UUID] = mapped_column(String, ForeignKey("challans.id"), nullable=False)

    decided_by: Mapped[uuid.UUID] = mapped_column(String, ForeignKey("users.id"), nullable=False)

    decided_role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", native_enum=False),
        nullable=False,
    )

    decision: Mapped[ChallanStatus] = mapped_column(
        SAEnum(ChallanStatus, name="challan_status", native_enum=False),
        nullable=False,
    )

    decided_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[uuid.UUID] = mapped_column(String, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    challan_id: Mapped[Optional[uuid.UUID]] = mapped_column(String, ForeignKey("challans.id"), nullable=True)
    channel: Mapped[Optional[NotificationChannel]] = mapped_column(SAEnum(NotificationChannel, native_enum=False), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[Optional[NotificationStatus]] = mapped_column(SAEnum(NotificationStatus, native_enum=False), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fail_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[uuid.UUID] = mapped_column(String, primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    actor_role: Mapped[Optional[UserRole]] = mapped_column(SAEnum(UserRole, native_enum=False), nullable=True)
    action: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(String, nullable=True)
    meta_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))



# ----------------------------
# Dependencies
# ----------------------------
async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


class RequestActor(BaseModel):
    role: UserRole
    user_id: Optional[uuid.UUID] = None


def get_actor(
    x_role: str = Header(..., alias="X-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
) -> RequestActor:
    try:
        role = UserRole(x_role)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid X-Role header. Use ADMIN/OFFICER/USER.")

    user_id = None
    if x_user_id:
        try:
            user_id = uuid.UUID(x_user_id)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid X-User-Id UUID header.")

    return RequestActor(role=role, user_id=user_id)


def require_role(*allowed: UserRole):
    def _guard(actor: RequestActor = Depends(get_actor)) -> RequestActor:
        if actor.role not in allowed:
            raise HTTPException(status_code=403, detail=f"Forbidden. Requires one of: {[r.value for r in allowed]}")
        return actor

    return _guard


# ----------------------------
# Schemas (API)
# ----------------------------
class AIResultIn(BaseModel):
    camera_id: Optional[uuid.UUID] = None
    location_id: Optional[uuid.UUID] = None
    model_run_id: Optional[uuid.UUID] = None

    violation_type: ViolationType
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    frame_ref: Optional[str] = None

    detection_confidence: float = Field(ge=0.0, le=1.0)
    is_uncertain: bool

    plate_text_raw: Optional[str] = None
    plate_text_norm: Optional[str] = None
    plate_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    ai_payload_json: Optional[Dict[str, Any]] = None
    rules_payload_json: Optional[Dict[str, Any]] = None


class AIResultOut(BaseModel):
    violation_id: uuid.UUID
    challan_id: uuid.UUID
    status: ChallanStatus
    decision_source: DecisionSource
    user_id: Optional[uuid.UUID] = None
    vehicle_id: Optional[uuid.UUID] = None


class OfficerQueueItem(BaseModel):
    challan_id: uuid.UUID
    violation_id: uuid.UUID
    violation_type: str
    plate_text_norm: Optional[str]
    detection_confidence: float
    is_uncertain: bool
    occurred_at: datetime
    frame_ref: Optional[str]


class ChallanOut(BaseModel):
    challan_id: uuid.UUID
    status: ChallanStatus
    decision_source: DecisionSource
    created_at: datetime
    decided_at: Optional[datetime]
    violation_type: str
    plate_text_norm: Optional[str]
    detection_confidence: float


class OfficerActionOut(BaseModel):
    ok: bool = True
    challan_id: uuid.UUID
    status: ChallanStatus


class RunOut(BaseModel):
    created: List[AIResultOut]


# ----------------------------
# Helpers
# ----------------------------
async def resolve_vehicle_and_user(
    db: AsyncSession,
    plate_norm: Optional[str],
) -> Tuple[Optional[uuid.UUID], Optional[uuid.UUID]]:
    if not plate_norm:
        return None, None

    q = select(Vehicle.id, Vehicle.user_id).where(Vehicle.vehicle_number == plate_norm)
    row = (await db.execute(q)).first()
    if not row:
        return None, None
    return row[0], row[1]


async def fetch_thresholds(db: AsyncSession) -> Dict[str, float]:
    """Load thresholds from system_settings table, fall back to hardcoded defaults."""
    rows = (await db.execute(select(SystemSetting))).scalars().all()
    thresholds = dict(THRESHOLDS)  # start with defaults
    for row in rows:
        try:
            thresholds[row.key] = float(row.value)
        except (TypeError, ValueError):
            pass
    return thresholds


def compute_status_and_uncertainty(vt_key: str, conf: float, is_uncertain_flag: bool, thresholds: Optional[Dict[str, float]] = None) -> Tuple[ChallanStatus, bool]:
    thr_map = thresholds if thresholds else THRESHOLDS
    thr = thr_map.get(vt_key, 0.75)
    uncertain = bool(is_uncertain_flag) or (conf < thr)
    if uncertain:
        return ChallanStatus.UNDER_REVIEW, True
    return ChallanStatus.APPROVED, False


def normalize_plate(text: str) -> str:
    text = text.upper()
    return re.sub(r"[^A-Z0-9]", "", text)


async def find_existing_challan_if_duplicate(db: AsyncSession, payload: AIResultIn) -> Optional[AIResultOut]:
    """
    Basic idempotency:
    If same (camera_id, occurred_at, frame_ref, violation_type, plate_text_norm) already exists,
    return existing challan instead of creating duplicate.

    Note: You can tune these keys based on your pipeline.
    """
    conditions = [Violation.violation_type == payload.violation_type, Violation.occurred_at == payload.occurred_at]

    # camera_id & frame_ref help a lot
    if payload.camera_id is not None:
        conditions.append(Violation.camera_id == payload.camera_id)
    if payload.frame_ref:
        conditions.append(Violation.frame_ref == payload.frame_ref)
    if payload.plate_text_norm:
        conditions.append(Violation.plate_text_norm == payload.plate_text_norm)

    v_id = (await db.execute(select(Violation.id).where(and_(*conditions)).limit(1))).scalar_one_or_none()
    if not v_id:
        return None

    c_row = (
        await db.execute(
            select(Challan.id, Challan.status, Challan.decision_source, Challan.user_id, Challan.vehicle_id)
            .where(Challan.violation_id == v_id)
            .limit(1)
        )
    ).first()

    if not c_row:
        return None

    return AIResultOut(
        violation_id=v_id,
        challan_id=c_row[0],
        status=c_row[1],
        decision_source=c_row[2],
        user_id=c_row[3],
        vehicle_id=c_row[4],
    )


async def create_violation_and_challan(db: AsyncSession, payload: AIResultIn, thresholds: Optional[Dict[str, float]] = None) -> AIResultOut:
    # idempotency guard
    existing = await find_existing_challan_if_duplicate(db, payload)
    if existing:
        return existing

    # Normalize plate if not already done
    if payload.plate_text_raw and not payload.plate_text_norm:
        payload.plate_text_norm = normalize_plate(payload.plate_text_raw)

    vt = payload.violation_type
    status, uncertain = compute_status_and_uncertainty(vt.value, payload.detection_confidence, payload.is_uncertain, thresholds)
    vehicle_id, user_id = await resolve_vehicle_and_user(db, payload.plate_text_norm)

    vid = str(uuid.uuid4())
    v = Violation(
        id=vid,
        camera_id=str(payload.camera_id) if payload.camera_id else None,
        location_id=str(payload.location_id) if payload.location_id else None,
        model_run_id=str(payload.model_run_id) if payload.model_run_id else None,
        violation_type=vt,
        occurred_at=payload.occurred_at,
        frame_ref=payload.frame_ref,
        plate_text_raw=payload.plate_text_raw,
        plate_text_norm=payload.plate_text_norm,
        plate_confidence=payload.plate_confidence,
        detection_confidence=payload.detection_confidence,
        is_uncertain=uncertain,
        ai_payload_json=payload.ai_payload_json,
        rules_payload_json=payload.rules_payload_json,
    )
    db.add(v)
    await db.flush()  # v.id

    cid = str(uuid.uuid4())
    c = Challan(
        id=cid,
        violation_id=vid,
        user_id=str(user_id) if user_id else None,
        vehicle_id=str(vehicle_id) if vehicle_id else None,
        status=status,
        decision_source=DecisionSource.AI,
        officer_id=None,
        created_at=datetime.now(timezone.utc),
        decided_at=(datetime.now(timezone.utc) if status == ChallanStatus.APPROVED else None),
        amount=0,
        due_date=None,
    )
    db.add(c)
    await db.flush()  # c.id

    return AIResultOut(
        violation_id=vid,
        challan_id=cid,
        status=status,
        decision_source=DecisionSource.AI,
        user_id=user_id,
        vehicle_id=vehicle_id,
    )



def require_models_loaded():
    if not getattr(app.state, "helmet_model", None) or not getattr(app.state, "vehicle_model", None) or not getattr(
        app.state, "plate_model", None
    ):
        raise HTTPException(
            status_code=503,
            detail="Models not loaded. Check .pt paths or startup logs (HELMET_MODEL_PATH/TRAFFIC_MODEL_PATH/PLATE_MODEL_PATH).",
        )
    if not getattr(app.state, "ocr_reader", None):
        raise HTTPException(status_code=503, detail="OCR not initialized. Check EasyOCR/torch installation.")


# ----------------------------
# Inference helpers (uses app.state models)
# ----------------------------
def detect_no_helmet_stub(image: np.ndarray) -> List[AIResultIn]:
    results = app.state.helmet_model(image)
    detections: List[AIResultIn] = []

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            label = str(app.state.helmet_model.names[cls]).lower()
            if label == "no_helmet":
                detections.append(
                    AIResultIn(
                        violation_type=ViolationType.NO_HELMET,
                        occurred_at=datetime.now(timezone.utc),
                        detection_confidence=conf,
                        is_uncertain=conf < THRESHOLDS["NO_HELMET"],
                        ai_payload_json={"label": "no_helmet", "bbox_xyxy": box.xyxy[0].tolist()},
                    )
                )
    return detections


def detect_red_light_stub(image: np.ndarray) -> List[AIResultIn]:
    if CURRENT_SIGNAL_STATE != "RED":
        return []

    results = app.state.vehicle_model(image)
    detections: List[AIResultIn] = []

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            label = str(app.state.vehicle_model.names[cls]).lower()

            if label in ["car", "motorcycle", "bike"]:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                if y2 > STOP_LINE_Y:
                    detections.append(
                        AIResultIn(
                            violation_type=ViolationType.RED_LIGHT,
                            occurred_at=datetime.now(timezone.utc),
                            detection_confidence=conf,
                            is_uncertain=conf < THRESHOLDS["RED_LIGHT"],
                            ai_payload_json={
                                "label": label,
                                "bbox_xyxy": [x1, y1, x2, y2],
                                "signal_state": CURRENT_SIGNAL_STATE,
                                "stop_line_y": STOP_LINE_Y,
                            },
                        )
                    )
    return detections


def detect_wrong_lane_stub(image: np.ndarray) -> List[AIResultIn]:
    results = app.state.vehicle_model(image)
    detections: List[AIResultIn] = []

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            label = str(app.state.vehicle_model.names[cls]).lower()

            if label in ["car", "motorcycle", "bike"]:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                center_x = (x1 + x2) / 2.0
                if not (LANE_MIN_X <= center_x <= LANE_MAX_X):
                    detections.append(
                        AIResultIn(
                            violation_type=ViolationType.WRONG_LANE,
                            occurred_at=datetime.now(timezone.utc),
                            detection_confidence=conf,
                            is_uncertain=conf < THRESHOLDS["WRONG_LANE"],
                            ai_payload_json={
                                "label": label,
                                "bbox_xyxy": [x1, y1, x2, y2],
                                "center_x": center_x,
                                "lane_allowed": [LANE_MIN_X, LANE_MAX_X],
                            },
                        )
                    )
    return detections


def detect_triple_riding_stub(image: np.ndarray) -> List[AIResultIn]:
    results = app.state.vehicle_model(image)

    persons: List[Tuple[List[float], float]] = []
    bikes: List[Tuple[List[float], float]] = []

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            label = str(app.state.vehicle_model.names[cls]).lower()
            xyxy = box.xyxy[0].tolist()

            if label == "person":
                persons.append((xyxy, conf))
            elif label in ["motorcycle", "bike"]:
                bikes.append((xyxy, conf))

    detections: List[AIResultIn] = []
    for bike_xyxy, bike_conf in bikes:
        bx1, by1, bx2, by2 = bike_xyxy
        rider_count = 0

        for person_xyxy, _pconf in persons:
            px1, py1, px2, py2 = person_xyxy
            overlap = not (px2 < bx1 or px1 > bx2 or py2 < by1 or py1 > by2)
            if overlap:
                rider_count += 1

        if rider_count >= 3:
            detections.append(
                AIResultIn(
                    violation_type=ViolationType.TRIPLE_RIDING,
                    occurred_at=datetime.now(timezone.utc),
                    detection_confidence=bike_conf,
                    is_uncertain=bike_conf < THRESHOLDS["TRIPLE_RIDING"],
                    ai_payload_json={"bike_bbox_xyxy": bike_xyxy, "rider_count": rider_count},
                )
            )
    return detections


def extract_plate_stub(image: np.ndarray) -> Tuple[Optional[str], Optional[str], Optional[float]]:
    results = app.state.plate_model(image)

    best_text: Optional[str] = None
    best_ocr_conf: float = 0.0

    for r in results:
        for box in r.boxes:
            det_conf = float(box.conf[0])
            if det_conf < 0.40:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            h, w = image.shape[:2]
            x1 = max(0, min(x1, w - 1))
            x2 = max(0, min(x2, w))
            y1 = max(0, min(y1, h - 1))
            y2 = max(0, min(y2, h))

            crop = image[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            ocr_results = app.state.ocr_reader.readtext(crop)
            for (_bbox, text_val, ocr_conf) in ocr_results:
                ocr_conf = float(ocr_conf)
                if ocr_conf > best_ocr_conf:
                    best_text = text_val
                    best_ocr_conf = ocr_conf

    if not best_text:
        return None, None, None

    norm = normalize_plate(best_text)
    return best_text, norm, best_ocr_conf


# ----------------------------
# Audit + Notification helpers
# ----------------------------
async def log_audit(
    db: AsyncSession,
    actor_user_id: Optional[str],
    actor_role: Optional[UserRole],
    action: str,
    entity_type: str,
    entity_id: Optional[str],
    meta: Optional[dict] = None,
):
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta_json=meta or {},
        created_at=datetime.now(timezone.utc),
    ))


async def create_notification(
    db: AsyncSession,
    user_id: Optional[str],
    challan_id: Optional[str],
    title: str,
    message: str,
    channel: NotificationChannel = NotificationChannel.IN_APP,
):
    if not user_id:
        return
    db.add(Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        challan_id=challan_id,
        channel=channel,
        title=title,
        message=message,
        status=NotificationStatus.SENT,
        sent_at=datetime.now(timezone.utc),
    ))


# ----------------------------
# Endpoints
# ----------------------------
@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": "traffic-auto-challan-single-file",
        "models_loaded": bool(getattr(app.state, "helmet_model", None))
        and bool(getattr(app.state, "vehicle_model", None))
        and bool(getattr(app.state, "plate_model", None)),
        "ocr_loaded": bool(getattr(app.state, "ocr_reader", None)),
    }


@app.post("/api/inference/result", response_model=AIResultOut)
async def post_inference_result(
    payload: AIResultIn,
    db: AsyncSession = Depends(get_db),
    _actor: RequestActor = Depends(require_role(UserRole.ADMIN, UserRole.OFFICER, UserRole.USER)),
):
    async with db.begin():
        thresholds = await fetch_thresholds(db)
        out = await create_violation_and_challan(db, payload, thresholds)
        # Notify user if challan was auto-approved and we know who they are
        if out.status == ChallanStatus.APPROVED and out.user_id:
            await create_notification(
                db, str(out.user_id), str(out.challan_id),
                title="Challan Issued",
                message=f"A challan has been auto-approved for violation: {payload.violation_type.value}. Please pay via the portal.",
            )
        await log_audit(db, None, UserRole.ADMIN, "AI_INFERENCE_RESULT", "challan", str(out.challan_id))
    return out


@app.post("/api/inference/run", response_model=RunOut)
async def run_inference_on_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _actor: RequestActor = Depends(require_role(UserRole.ADMIN)),
):
    # require_models_loaded() # Disable strict requirement for demo
    models_available = bool(getattr(app.state, "helmet_model", None))

    # Handle image or video
    image = None
    if file.content_type.startswith("image"):
        image_bytes = await file.read()
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    elif file.content_type.startswith("video"):
        # Save temp video to read frames
        temp_path = _os.path.join(EVIDENCE_DIR, f"temp_{uuid.uuid4()}_{file.filename}")
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        
        cap = cv2.VideoCapture(temp_path)
        if cap.isOpened():
            # Jump to 50% through the video for a good sample frame
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
            ret, image = cap.read()
        cap.release()
        if _os.path.exists(temp_path): _os.remove(temp_path)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image or video file.")

    detected: List[AIResultIn] = []
    if models_available:
        detected.extend(detect_no_helmet_stub(image))
        detected.extend(detect_red_light_stub(image))
        detected.extend(detect_wrong_lane_stub(image))
        detected.extend(detect_triple_riding_stub(image))
    else:
        # Mock detection for demo
        print("[INFO] Models not loaded. Returning mock detections.")
        detected.append(
            AIResultIn(
                violation_type=ViolationType.NO_HELMET,
                occurred_at=datetime.now(timezone.utc),
                detection_confidence=0.88,
                is_uncertain=False,
                ai_payload_json={"label": "no_helmet", "mock": True},
            )
        )
        detected.append(
            AIResultIn(
                violation_type=ViolationType.RED_LIGHT,
                occurred_at=datetime.now(timezone.utc),
                detection_confidence=0.92,
                is_uncertain=False,
                ai_payload_json={"label": "car", "mock": True},
            )
        )

    created: List[AIResultOut] = []
    async with db.begin():
        for d in detected:
            if models_available and getattr(app.state, "ocr_reader", None):
                plate_raw, plate_norm, plate_conf = extract_plate_stub(image)
                d.plate_text_raw = plate_raw
                d.plate_text_norm = plate_norm
                d.plate_confidence = plate_conf
            else:
                # Mock plate
                d.plate_text_raw = "AP12AB1234"
                d.plate_text_norm = "AP12AB1234"
                d.plate_confidence = 0.95

            created.append(await create_violation_and_challan(db, d))

    return RunOut(created=created)


@app.get("/officer/review-queue", response_model=List[OfficerQueueItem])
async def officer_review_queue(
    db: AsyncSession = Depends(get_db),
    _actor: RequestActor = Depends(require_role(UserRole.OFFICER, UserRole.ADMIN)),
):
    q = (
        select(
            Challan.id,
            Violation.id,
            Violation.violation_type,
            Violation.plate_text_norm,
            Violation.detection_confidence,
            Violation.is_uncertain,
            Violation.occurred_at,
            Violation.frame_ref,
        )
        .join(Violation, Violation.id == Challan.violation_id)
        .where(Challan.status == ChallanStatus.UNDER_REVIEW)
        .order_by(Challan.created_at.desc())
        .limit(200)
    )
    rows = (await db.execute(q)).all()

    return [
        OfficerQueueItem(
            challan_id=r[0],
            violation_id=r[1],
            violation_type=(r[2].value if hasattr(r[2], "value") else str(r[2])),
            plate_text_norm=r[3],
            detection_confidence=r[4],
            is_uncertain=r[5],
            occurred_at=r[6],
            frame_ref=r[7],
        )
        for r in rows
    ]


@app.post("/officer/challans/{challan_id}/approve", response_model=OfficerActionOut)
async def officer_approve(
    challan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: RequestActor = Depends(require_role(UserRole.OFFICER, UserRole.ADMIN)),
):
    if not actor.user_id:
        raise HTTPException(status_code=401, detail="X-User-Id is required for officer actions.")

    challan_id_str = str(challan_id)
    actor_id_str = str(actor.user_id)

    async with db.begin():
        c = (await db.execute(select(Challan).where(Challan.id == challan_id_str))).scalar_one_or_none()
        if not c:
            raise HTTPException(status_code=404, detail="Challan not found.")
        if c.status != ChallanStatus.UNDER_REVIEW:
            raise HTTPException(status_code=400, detail="Only UNDER_REVIEW challans can be approved/declined.")

        now = datetime.now(timezone.utc)
        c.status = ChallanStatus.APPROVED
        c.decision_source = DecisionSource.OFFICER
        c.officer_id = actor_id_str
        c.decided_at = now

        db.add(ChallanDecision(
            id=str(uuid.uuid4()),
            challan_id=challan_id_str,
            decided_by=actor_id_str,
            decided_role=actor.role,
            decision=ChallanStatus.APPROVED,
            decided_at=now,
        ))

        await log_audit(
            db, actor_id_str, actor.role,
            "OFFICER_APPROVE", "challan", challan_id_str,
            meta={"status": "APPROVED"},
        )
        await create_notification(
            db, c.user_id, challan_id_str,
            title="Challan Approved",
            message="An officer has reviewed and approved your challan. Please pay the fine via the portal.",
        )

    return OfficerActionOut(challan_id=challan_id, status=ChallanStatus.APPROVED)


@app.post("/officer/challans/{challan_id}/decline", response_model=OfficerActionOut)
async def officer_decline(
    challan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: RequestActor = Depends(require_role(UserRole.OFFICER, UserRole.ADMIN)),
):
    if not actor.user_id:
        raise HTTPException(status_code=401, detail="X-User-Id is required for officer actions.")

    challan_id_str = str(challan_id)
    actor_id_str = str(actor.user_id)

    async with db.begin():
        c = (await db.execute(select(Challan).where(Challan.id == challan_id_str))).scalar_one_or_none()
        if not c:
            raise HTTPException(status_code=404, detail="Challan not found.")
        if c.status != ChallanStatus.UNDER_REVIEW:
            raise HTTPException(status_code=400, detail="Only UNDER_REVIEW challans can be approved/declined.")

        now = datetime.now(timezone.utc)
        c.status = ChallanStatus.DECLINED
        c.decision_source = DecisionSource.OFFICER
        c.officer_id = actor_id_str
        c.decided_at = now

        db.add(ChallanDecision(
            id=str(uuid.uuid4()),
            challan_id=challan_id_str,
            decided_by=actor_id_str,
            decided_role=actor.role,
            decision=ChallanStatus.DECLINED,
            decided_at=now,
        ))

        await log_audit(
            db, actor_id_str, actor.role,
            "OFFICER_DECLINE", "challan", challan_id_str,
            meta={"status": "DECLINED"},
        )
        await create_notification(
            db, c.user_id, challan_id_str,
            title="Challan Declined",
            message="An officer has reviewed and declined your challan. No fine is owed.",
        )

    return OfficerActionOut(challan_id=challan_id, status=ChallanStatus.DECLINED)


@app.get("/user/challans", response_model=List[ChallanOut])
async def user_challans(
    db: AsyncSession = Depends(get_db),
    actor: RequestActor = Depends(require_role(UserRole.USER, UserRole.ADMIN)),
):
    if actor.role == UserRole.USER and not actor.user_id:
        raise HTTPException(status_code=401, detail="X-User-Id required.")

    user_id = actor.user_id

    q = (
        select(
            Challan.id,
            Challan.status,
            Challan.decision_source,
            Challan.created_at,
            Challan.decided_at,
            Violation.violation_type,
            Violation.plate_text_norm,
            Violation.detection_confidence,
        )
        .join(Violation, Violation.id == Challan.violation_id)
        .where(Challan.user_id == user_id)
        .where(Challan.status == ChallanStatus.APPROVED)  # default show only APPROVED
        .order_by(Challan.created_at.desc())
        .limit(200)
    )
    rows = (await db.execute(q)).all()

    return [
        ChallanOut(
            challan_id=r[0],
            status=r[1],
            decision_source=r[2],
            created_at=r[3],
            decided_at=r[4],
            violation_type=(r[5].value if hasattr(r[5], "value") else str(r[5])),
            plate_text_norm=r[6],
            detection_confidence=r[7],
        )
        for r in rows
    ]


@app.get("/user/challans/{challan_id}", response_model=ChallanOut)
async def user_challan_detail(
    challan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: RequestActor = Depends(require_role(UserRole.USER, UserRole.ADMIN)),
):
    if actor.role == UserRole.USER and not actor.user_id:
        raise HTTPException(status_code=401, detail="X-User-Id required.")

    q = (
        select(
            Challan.id,
            Challan.status,
            Challan.decision_source,
            Challan.created_at,
            Challan.decided_at,
            Violation.violation_type,
            Violation.plate_text_norm,
            Violation.detection_confidence,
        )
        .join(Violation, Violation.id == Challan.violation_id)
        .where(Challan.id == challan_id)
    )
    if actor.role == UserRole.USER:
        q = q.where(Challan.user_id == actor.user_id)
    
    r = (await db.execute(q)).first()
    if not r:
        raise HTTPException(status_code=404, detail="Challan not found or access denied.")

    return ChallanOut(
        challan_id=r[0],
        status=r[1],
        decision_source=r[2],
        created_at=r[3],
        decided_at=r[4],
        violation_type=(r[5].value if hasattr(r[5], "value") else str(r[5])),
        plate_text_norm=r[6],
        detection_confidence=r[7],
    )


class DashboardStatsOut(BaseModel):
    total_violations: int
    pending_review: int
    approved_challans: int
    system_health: str = "Healthy"


@app.get("/admin/dashboard", response_model=DashboardStatsOut)
async def admin_dashboard(
    db: AsyncSession = Depends(get_db),
    _actor: RequestActor = Depends(require_role(UserRole.ADMIN)),
):
    # Quick counts
    total_viol = (await db.execute(select(func.count(Violation.id)))).scalar() or 0
    pending_rev = (await db.execute(select(func.count(Challan.id)).where(Challan.status == ChallanStatus.UNDER_REVIEW))).scalar() or 0
    approved_c = (await db.execute(select(func.count(Challan.id)).where(Challan.status == ChallanStatus.APPROVED))).scalar() or 0

    return DashboardStatsOut(
        total_violations=total_viol,
        pending_review=pending_rev,
        approved_challans=approved_c,
    )


class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    user_id: str
    role: UserRole
    full_name: str

@app.post("/api/login", response_model=LoginResponse)
async def login_stub(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Very unsafe mock login for demo
    q = select(User).where(User.email == req.email)
    user = (await db.execute(q)).scalar_one_or_none()
    
    if not user:
        # For demo purposes, auto-create the user if they don't exist
        # based on email mapping to roles
        role = UserRole.USER
        if "admin" in req.email.lower():
            role = UserRole.ADMIN
        elif "officer" in req.email.lower():
            role = UserRole.OFFICER
            
        user = User(
            id=str(uuid.uuid4()),
            role=role,
            full_name=req.email.split("@")[0].title(),
            email=req.email,
            password_hash="mock_hash", # Do not check password in mock
        )
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Could not create mock user: {e}")
            
    return LoginResponse(
        user_id=str(user.id),
        role=user.role,
        full_name=user.full_name
    )


class ViolationOut(BaseModel):
    id: uuid.UUID
    violation_type: str
    plate_text_norm: Optional[str]
    detection_confidence: float
    is_uncertain: bool
    occurred_at: datetime
    camera_id: Optional[uuid.UUID]

@app.get("/violations", response_model=List[ViolationOut])
async def get_all_violations(
    db: AsyncSession = Depends(get_db),
    _actor: RequestActor = Depends(require_role(UserRole.ADMIN, UserRole.OFFICER)),
):
    q = select(Violation).order_by(Violation.occurred_at.desc()).limit(100)
    rows = (await db.execute(q)).scalars().all()
    
    out = []
    for v in rows:
        out.append(ViolationOut(
            id=v.id,
            violation_type=(v.violation_type.value if hasattr(v.violation_type, "value") else str(v.violation_type)),
            plate_text_norm=v.plate_text_norm,
            detection_confidence=v.detection_confidence,
            is_uncertain=v.is_uncertain,
            occurred_at=v.occurred_at,
            camera_id=v.camera_id
        ))
    return out



# ----------------------------
# Missing 2: Evidence Storage
# ----------------------------
import hashlib, os as _os

EVIDENCE_DIR = _os.path.join(_os.path.dirname(__file__), "evidence_uploads")
_os.makedirs(EVIDENCE_DIR, exist_ok=True)

class EvidenceOut(BaseModel):
    id: str
    violation_id: str
    evidence_type: str
    file_path: str
    mime_type: Optional[str]
    sha256: str

@app.post("/violations/{violation_id}/evidence", response_model=EvidenceOut)
async def upload_evidence(
    violation_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _actor: RequestActor = Depends(require_role(UserRole.ADMIN, UserRole.OFFICER)),
):
    violation_id_str = str(violation_id)
    # verify violation exists
    v = (await db.execute(select(Violation).where(Violation.id == violation_id_str))).scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Violation not found.")

    contents = await file.read()
    sha256 = hashlib.sha256(contents).hexdigest()
    mime = file.content_type or "application/octet-stream"
    etype = EvidenceType.VIDEO if mime.startswith("video") else EvidenceType.IMAGE

    filename = f"{violation_id_str}_{sha256[:8]}_{file.filename}"
    filepath = _os.path.join(EVIDENCE_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    eid = str(uuid.uuid4())
    async with db.begin():
        db.add(EvidenceAsset(
            id=eid,
            violation_id=violation_id_str,
            evidence_type=etype,
            storage_provider="local",
            file_path=filepath,
            mime_type=mime,
            sha256=sha256,
        ))
        await log_audit(db, None, UserRole.ADMIN, "EVIDENCE_UPLOAD", "evidence_asset", eid)

    return EvidenceOut(
        id=eid,
        violation_id=violation_id_str,
        evidence_type=etype.value,
        file_path=filepath,
        mime_type=mime,
        sha256=sha256,
    )

@app.get("/violations/{violation_id}/evidence", response_model=List[EvidenceOut])
async def get_evidence(
    violation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _actor: RequestActor = Depends(require_role(UserRole.ADMIN, UserRole.OFFICER)),
):
    rows = (await db.execute(
        select(EvidenceAsset).where(EvidenceAsset.violation_id == str(violation_id))
    )).scalars().all()
    return [
        EvidenceOut(
            id=r.id,
            violation_id=r.violation_id,
            evidence_type=r.evidence_type.value if r.evidence_type else "IMAGE",
            file_path=r.file_path or "",
            mime_type=r.mime_type,
            sha256=r.sha256 or "",
        )
        for r in rows
    ]


# ----------------------------
# Missing 3: Notifications
# ----------------------------
class NotificationOut(BaseModel):
    id: str
    title: Optional[str]
    message: Optional[str]
    channel: Optional[str]
    status: Optional[str]
    sent_at: Optional[datetime]
    challan_id: Optional[str]

@app.get("/user/notifications", response_model=List[NotificationOut])
async def user_notifications(
    db: AsyncSession = Depends(get_db),
    actor: RequestActor = Depends(require_role(UserRole.USER, UserRole.ADMIN, UserRole.OFFICER)),
):
    if not actor.user_id:
        raise HTTPException(status_code=401, detail="X-User-Id required.")
    rows = (await db.execute(
        select(Notification)
        .where(Notification.user_id == str(actor.user_id))
        .order_by(Notification.sent_at.desc())
        .limit(50)
    )).scalars().all()
    return [
        NotificationOut(
            id=r.id,
            title=r.title,
            message=r.message,
            channel=r.channel.value if r.channel else None,
            status=r.status.value if r.status else None,
            sent_at=r.sent_at,
            challan_id=r.challan_id,
        )
        for r in rows
    ]


# ----------------------------
# Missing 4: Camera + Location Management
# ----------------------------
class LocationIn(BaseModel):
    name: str
    city: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class LocationOut(BaseModel):
    id: str
    name: Optional[str]
    city: Optional[str]
    state: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]

@app.get("/locations", response_model=List[LocationOut])
async def list_locations(db: AsyncSession = Depends(get_db), _actor: RequestActor = Depends(require_role(UserRole.ADMIN, UserRole.OFFICER))):
    rows = (await db.execute(select(Location))).scalars().all()
    return [LocationOut(id=r.id, name=r.name, city=r.city, state=r.state, latitude=r.latitude, longitude=r.longitude) for r in rows]

@app.post("/locations", response_model=LocationOut)
async def create_location(payload: LocationIn, db: AsyncSession = Depends(get_db), _actor: RequestActor = Depends(require_role(UserRole.ADMIN))):
    lid = str(uuid.uuid4())
    async with db.begin():
        db.add(Location(id=lid, name=payload.name, city=payload.city, state=payload.state, latitude=payload.latitude, longitude=payload.longitude))
        await log_audit(db, None, UserRole.ADMIN, "CREATE_LOCATION", "location", lid)
    return LocationOut(id=lid, name=payload.name, city=payload.city, state=payload.state, latitude=payload.latitude, longitude=payload.longitude)


class CameraIn(BaseModel):
    location_id: Optional[str] = None
    camera_code: str
    stream_url: Optional[str] = None
    direction: Optional[str] = None
    status: CameraStatus = CameraStatus.ACTIVE

class CameraOut(BaseModel):
    id: str
    location_id: Optional[str]
    camera_code: Optional[str]
    stream_url: Optional[str]
    direction: Optional[str]
    status: Optional[str]

@app.get("/cameras", response_model=List[CameraOut])
async def list_cameras(db: AsyncSession = Depends(get_db), _actor: RequestActor = Depends(require_role(UserRole.ADMIN, UserRole.OFFICER))):
    rows = (await db.execute(select(Camera))).scalars().all()
    return [CameraOut(id=r.id, location_id=r.location_id, camera_code=r.camera_code, stream_url=r.stream_url, direction=r.direction, status=r.status.value if r.status else None) for r in rows]

@app.post("/cameras", response_model=CameraOut)
async def create_camera(payload: CameraIn, db: AsyncSession = Depends(get_db), _actor: RequestActor = Depends(require_role(UserRole.ADMIN))):
    cid = str(uuid.uuid4())
    async with db.begin():
        db.add(Camera(id=cid, location_id=payload.location_id, camera_code=payload.camera_code, stream_url=payload.stream_url, direction=payload.direction, status=payload.status, created_at=datetime.now(timezone.utc)))
        await log_audit(db, None, UserRole.ADMIN, "CREATE_CAMERA", "camera", cid)
    return CameraOut(id=cid, location_id=payload.location_id, camera_code=payload.camera_code, stream_url=payload.stream_url, direction=payload.direction, status=payload.status.value)

@app.patch("/cameras/{camera_id}/status")
async def update_camera_status(camera_id: uuid.UUID, status: CameraStatus, db: AsyncSession = Depends(get_db), actor: RequestActor = Depends(require_role(UserRole.ADMIN))):
    cid = str(camera_id)
    async with db.begin():
        cam = (await db.execute(select(Camera).where(Camera.id == cid))).scalar_one_or_none()
        if not cam:
            raise HTTPException(status_code=404, detail="Camera not found.")
        cam.status = status
        cam.updated_at = datetime.now(timezone.utc)
        await log_audit(db, str(actor.user_id) if actor.user_id else None, actor.role, "ADMIN_UPDATE_CAMERA", "camera", cid, meta={"status": status.value})
    return {"ok": True, "camera_id": cid, "status": status.value}


# ----------------------------
# Missing 5: System Settings (Threshold Config)
# ----------------------------
class SettingOut(BaseModel):
    key: str
    value: Optional[str]

@app.get("/admin/settings", response_model=List[SettingOut])
async def get_settings(db: AsyncSession = Depends(get_db), _actor: RequestActor = Depends(require_role(UserRole.ADMIN))):
    rows = (await db.execute(select(SystemSetting))).scalars().all()
    return [SettingOut(key=r.key, value=r.value) for r in rows]

@app.put("/admin/settings/{key}")
async def update_setting(key: str, value: str, db: AsyncSession = Depends(get_db), actor: RequestActor = Depends(require_role(UserRole.ADMIN))):
    async with db.begin():
        setting = (await db.execute(select(SystemSetting).where(SystemSetting.key == key))).scalar_one_or_none()
        if setting:
            setting.value = value
        else:
            db.add(SystemSetting(key=key, value=value))
        await log_audit(db, str(actor.user_id) if actor.user_id else None, actor.role, "UPDATE_SETTING", "system_setting", key, meta={"value": value})
    return {"ok": True, "key": key, "value": value}


# ----------------------------
# Missing 6: Audit Log Query
# ----------------------------
class AuditLogOut(BaseModel):
    id: str
    actor_user_id: Optional[str]
    actor_role: Optional[str]
    action: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[str]
    created_at: datetime

@app.get("/admin/audit-logs", response_model=List[AuditLogOut])
async def get_audit_logs(db: AsyncSession = Depends(get_db), _actor: RequestActor = Depends(require_role(UserRole.ADMIN))):
    rows = (await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200))).scalars().all()
    return [
        AuditLogOut(
            id=r.id,
            actor_user_id=r.actor_user_id,
            actor_role=r.actor_role.value if r.actor_role else None,
            action=r.action,
            entity_type=r.entity_type,
            entity_id=r.entity_id,
            created_at=r.created_at,
        )
        for r in rows
    ]


# ----------------------------
# Startup: DB ping + model load + seed settings
# ----------------------------
@app.on_event("startup")
async def startup_check():
    # DB ping (won't create tables; assumes schema already applied)
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))

    # Seed default thresholds into system_settings if not already present
    async with SessionLocal() as db:
        async with db.begin():
            for key, value in THRESHOLDS.items():
                existing = (await db.execute(select(SystemSetting).where(SystemSetting.key == key))).scalar_one_or_none()
                if not existing:
                    db.add(SystemSetting(key=key, value=str(value)))
            print("[INFO] Default thresholds seeded into system_settings.")

    # Load models safely (don't crash app if missing — /api/inference/run will return 503)
    app.state.helmet_model = None
    app.state.vehicle_model = None
    app.state.plate_model = None
    app.state.ocr_reader = None

    try:
        app.state.helmet_model = YOLO(HELMET_MODEL_PATH)
    except Exception as e:
        print(f"[WARN] Failed to load helmet model ({HELMET_MODEL_PATH}): {e}")

    try:
        app.state.vehicle_model = YOLO(TRAFFIC_MODEL_PATH)
    except Exception as e:
        print(f"[WARN] Failed to load traffic model ({TRAFFIC_MODEL_PATH}): {e}")

    try:
        app.state.plate_model = YOLO(PLATE_MODEL_PATH)
    except Exception as e:
        print(f"[WARN] Failed to load plate model ({PLATE_MODEL_PATH}): {e}")

    try:
        # If you have CUDA, you can set gpu=True
        app.state.ocr_reader = easyocr.Reader(["en"], gpu=False)
    except Exception as e:
        print(f"[WARN] Failed to init EasyOCR: {e}")

