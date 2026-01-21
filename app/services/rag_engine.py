import chromadb
from datetime import datetime

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# ==================================================
# ChromaDB Setup
# ==================================================

client = chromadb.PersistentClient(
    path=settings.CHROMA_PERSIST_DIR
)

collection = client.get_or_create_collection(
    name="medical_notes"
)

# ==================================================
# Patient Identity (STRICT)
# doctor_id + patient_id = UNIQUE FOREVER
# ==================================================

def build_patient_key(doctor_id: int, patient_id: int) -> str:
    return f"{doctor_id}_{patient_id}"

# ==================================================
# Store SOAP Note Embedding
# ==================================================

def store_note_embedding(
    doctor_id: int,
    patient_id: int,
    soap_note: str,
    note_id: int,
):
    patient_key = build_patient_key(doctor_id, patient_id)

    logger.info(
        f"RAG | STORE START | PatientKey={patient_key} | NoteID={note_id}"
    )

    # Safety: do NOT store invalid outputs
    if "INVALID SOAP OUTPUT" in soap_note:
        logger.info(
            f"RAG | STORE SKIPPED | INVALID SOAP | NoteID={note_id}"
        )
        return

    document_text = f"""
Visit Date: {datetime.utcnow().strftime('%Y-%m-%d')}
Doctor ID: {doctor_id}
Patient ID: {patient_id}

SOAP NOTE:
{soap_note}
""".strip()

    collection.add(
        documents=[document_text],
        metadatas=[{
            "patient_key": patient_key,
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "note_id": note_id,
        }],
        ids=[str(note_id)],
    )

    logger.info(
        f"RAG | STORE SUCCESS | PatientKey={patient_key} | NoteID={note_id}"
    )

# ==================================================
# Retrieve Patient Medical History
# ==================================================

def retrieve_patient_history(
    doctor_id: int,
    patient_id: int,
    n_results: int = 2,
) -> str:
    patient_key = build_patient_key(doctor_id, patient_id)

    logger.info(
        f"RAG | RETRIEVE START | PatientKey={patient_key}"
    )

    try:
        results = collection.query(
            query_texts=[f"Medical history for patient {patient_key}"],
            where={"patient_key": patient_key},
            n_results=n_results,
        )

        documents = results.get("documents", [])

        if documents and documents[0]:
            logger.info(
                f"RAG | HISTORY FOUND | PatientKey={patient_key} | Notes={len(documents[0])}"
            )
            return "\n---\n".join(documents[0])

        logger.info(
            f"RAG | NO HISTORY | PatientKey={patient_key}"
        )
        return "No previous medical history available."

    except Exception:
        logger.exception(
            f"RAG | ERROR | PatientKey={patient_key}"
        )
        return "No previous medical history available."
