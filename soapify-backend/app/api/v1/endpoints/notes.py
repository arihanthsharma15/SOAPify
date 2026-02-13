from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import re

from app.core.database import get_db
from app.core.logger import get_logger
from app.api.deps import get_current_user
from app.models import models
from app.schemas.transcript import TranscriptCreate
from app.services.llm_engine import process_transcript_task


logger = get_logger(__name__)
router = APIRouter()


# -------------------------
# Transcript Sanitization
# -------------------------
def sanitize_transcript(raw_text: str) -> str:
    if not raw_text or not raw_text.strip():
        return "No transcript provided."

    text_data = raw_text.strip()
    text_data = text_data.replace("\r\n", "\n").replace("\r", "\n")
    text_data = re.sub(r"\n\s*\n+", "\n", text_data)
    text_data = re.sub(r"[ \t]+", " ", text_data)

    replacements = {
        r"\bPt\b:?": "Patient:",
        r"\bDr\b:?": "Doctor:",
        r"\bHx\b": "History",
        r"\bC\/O\b": "Complains of",
    }

    for pattern, replacement in replacements.items():
        text_data = re.sub(pattern, replacement, text_data, flags=re.IGNORECASE)

    return text_data


# -------------------------
# Generate SOAP Note
# -------------------------
@router.post("/Generate")
def generate_soap_notes(
    request: TranscriptCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        if request.age is None:
            raise HTTPException(
                status_code=400,
                detail="Age is required.",
            )

        clean_text = sanitize_transcript(request.transcript_text)

        # 1️⃣ Fetch or create patient (doctor-scoped)
        patient = (
            db.query(models.Patient)
            .filter(
                models.Patient.doctor_id == current_user.id,
                models.Patient.name == request.patient_name,
                models.Patient.age == request.age,
            )
            .first()
        )

        if not patient:
            patient = models.Patient(
                doctor_id=current_user.id,
                name=request.patient_name,
                age=request.age,
                gender=getattr(request, "gender", None),
            )
            db.add(patient)
            db.flush()

        # 2️⃣ Create transcript
        transcript = models.Transcript(
            doctor_id=current_user.id,
            patient_id=patient.id,
            text=clean_text,
        )
        db.add(transcript)
        db.flush()

        # 3️⃣ Doctor-wise SOAP number (transaction safe)
        last_number = (
            db.query(func.max(models.SOAPNote.doctor_soap_number))
            .filter(models.SOAPNote.doctor_id == current_user.id)
            .scalar()
        )       

        next_number = (last_number or 0) + 1

        # 4️⃣ SOAP placeholder
        soap_note = models.SOAPNote(
            transcript_id=transcript.id,
            doctor_id=current_user.id, 
            doctor_soap_number=next_number,
            status="PROCESSING",
            content="AI is generating your note. Please wait...",
        )
        db.add(soap_note)
        db.commit()
        db.refresh(soap_note)

        # 5️⃣ Background LLM processing
        background_tasks.add_task(
            process_transcript_task,
            request,
            current_user.id,
            soap_note.id,
        )

        return {
            "id": soap_note.id,
            "soap_number": soap_note.doctor_soap_number,
            "patient_name": patient.name,
            "status": soap_note.status,
            "message": "Note generation started.",
        }

    except Exception:
        db.rollback()
        logger.exception("SOAP generation failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit transcript",
        )


# -------------------------
# SOAP Status
# -------------------------
@router.get("/Status/{note_id}")
def get_note_status(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    note = (
        db.query(models.SOAPNote)
        .join(models.Transcript)
        .filter(
            models.SOAPNote.id == note_id,
            models.Transcript.doctor_id == current_user.id,
        )
        .first()
    )

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return {
        "id": note.id,
        "soap_number": note.doctor_soap_number,
        "status": note.status,
        "content": note.content,
    }


# -------------------------
# Update SOAP
# -------------------------
@router.put("/Update/{note_id}")
def update_soap_note(
    note_id: int,
    updated_content: str = Body(embed=True),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    note = (
        db.query(models.SOAPNote)
        .join(models.Transcript)
        .filter(
            models.SOAPNote.id == note_id,
            models.Transcript.doctor_id == current_user.id,
        )
        .first()
    )

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.content = updated_content
    db.commit()

    return {"status": "success", "message": "Note updated successfully"}


# -------------------------
# Dashboard
# -------------------------
@router.get("/DashboardData")
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = text("""
        SELECT
            s.id AS note_id,
            s.doctor_soap_number,
            p.id AS patient_id,
            p.name AS patient_name,
            s.status,
            s.created_at
        FROM soap_notes s
        JOIN transcripts t ON s.transcript_id = t.id
        JOIN patients p ON t.patient_id = p.id
        WHERE t.doctor_id = :doc_id
        ORDER BY s.doctor_soap_number DESC
    """)

    rows = db.execute(query, {"doc_id": current_user.id}).fetchall()

    return [
        {
            "note_id": r.note_id,
            "soap_number": r.doctor_soap_number,
            "patient_id": r.patient_id,
            "patient_name": r.patient_name,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in rows
    ]


# -------------------------
# Patient History (Doctor + Patient scoped)
# -------------------------
@router.get("/PatientHistory/{patient_id}")
def get_patient_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = text("""
        SELECT s.doctor_soap_number, s.content, s.created_at
        FROM soap_notes s
        JOIN transcripts t ON s.transcript_id = t.id
        WHERE t.patient_id = :pid
          AND t.doctor_id = :doc_id
        ORDER BY s.doctor_soap_number DESC
    """)

    rows = db.execute(
        query,
        {"pid": patient_id, "doc_id": current_user.id},
    ).fetchall()

    return [
        {
            "soap_number": r.doctor_soap_number,
            "content": r.content,
            "date": r.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for r in rows
    ]
