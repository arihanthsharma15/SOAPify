import httpx
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logger import get_logger
from app.models.models import SOAPNote
from app.schemas.transcript import TranscriptCreate
from app.services.rag_engine import (
    retrieve_patient_history,
    store_note_embedding,
)
from app.services.soap_validator import validate_soap_output

logger = get_logger(__name__)

# ==================================================
# LLM CALLS
# ==================================================

async def call_ollama(prompt: str) -> str:
    if not settings.OLLAMA_BASE_URL or not settings.OLLAMA_MODEL:
        raise RuntimeError("Ollama is not configured")

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_ctx": 2048,
                },
            },
        )
        response.raise_for_status()
        return response.json()["response"]


async def call_groq(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
            },
        )

    if response.status_code != 200:
        logger.error(f"GROQ ERROR {response.status_code} | {response.text}")
        raise RuntimeError("Groq LLM call failed")

    return response.json()["choices"][0]["message"]["content"]


async def call_llm(prompt: str) -> str:
    if settings.LLM_PROVIDER == "ollama":
        return await call_ollama(prompt)
    return await call_groq(prompt)

# ==================================================
# PROMPT (STRICT SOAP)
# ==================================================

def build_prompt(history: str, transcript: str) -> str:
    return f"""
You are a clinical medical scribe generating a SOAP note.

THIS SOAP NOTE IS ONLY FOR THE CURRENT VISIT.
PAST VISITS ARE PROVIDED FOR CONTEXT ONLY.

CRITICAL TEMPORAL RULES (NO EXCEPTIONS):
- Use CURRENT VISIT TRANSCRIPT as the ONLY source of truth.
- PREVIOUS MEDICAL HISTORY is for background understanding ONLY.
- DO NOT copy symptoms, vitals, plans, or findings from past visits.
- Past information may be referenced ONLY in ASSESSMENT if relevant
  (e.g., "known asthma", "previous exacerbation").
- NEVER repeat old vitals, complaints, or plans unless explicitly stated again.

ABSOLUTE RULES (NO EXCEPTIONS):
- Output plain text only.
- Do NOT use bullets, lists, markdown, or special formatting.
- Do NOT add reminders, explanations, disclaimers, or extra sections.
- Do NOT invent information.
- If information is truly absent, write exactly: Not mentioned.
- Investigations, tests, studies, or results MUST be included ONLY if explicitly stated.
- Output must begin directly with "SUBJECTIVE:".

SUBJECTIVE RULES:
- Include ONLY symptoms, complaints, and history stated IN THIS VISIT.
- Do NOT include prior visit symptoms unless repeated again.
- Do NOT include vitals or examination findings.
- If absent, write exactly: Not mentioned.

OBJECTIVE RULES (STRICT):
- Include ONLY vitals or findings measured IN THIS VISIT.
- Do NOT reuse vitals from past visits.
- If objective data exists today, OBJECTIVE MUST NOT be "Not mentioned".
- If absent today, write exactly: Not mentioned.

ASSESSMENT RULES:
- Clinical impression for THIS VISIT.
- You MAY reference past diagnoses for continuity (e.g., known asthma).
- Do NOT restate old resolved problems.

PLAN RULES:
- Include ONLY plans stated or implied IN THIS VISIT.
- Do NOT repeat previous plans unless explicitly continued.
- If absent, write exactly: Not mentioned.

FORMAT RULES (STRICT):
- Output ONLY these four sections in this exact order:
  SUBJECTIVE:
  OBJECTIVE:
  ASSESSMENT:
  PLAN:

========================
PREVIOUS MEDICAL HISTORY (REFERENCE ONLY):
{history}
========================

CURRENT VISIT TRANSCRIPT (SOURCE OF TRUTH):
{transcript}
========================
""".strip()

# ==================================================
# BACKGROUND TASK
# ==================================================

async def process_transcript_task(
    data: TranscriptCreate,
    doctor_id: int,
    soap_id: int,
):
    logger.info(
        f"TASK START | SOAP_ID={soap_id} | Patient={data.patient_name} | Age={data.age}"
    )

    db = SessionLocal()

    try:
        # 1️⃣ Fetch SOAP
        soap = db.query(SOAPNote).filter(SOAPNote.id == soap_id).first()
        if not soap:
            raise RuntimeError("SOAP note not found")

        transcript = soap.transcript
        patient_id = transcript.patient_id

        # 2️⃣ RAG retrieval
        history = retrieve_patient_history(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )

        # 3️⃣ Build prompt using REQUEST transcript (IMPORTANT)
        prompt = build_prompt(history, data.transcript_text)
        note = await call_llm(prompt)

        if "SUBJECTIVE:" in note:
            note = note[note.find("SUBJECTIVE:"):]

        valid, reason = validate_soap_output(note)

        # 4️⃣ Retry once if invalid
        if not valid:
            logger.warning(f"SOAP INVALID | RETRY | Reason={reason}")
            note = await call_llm(prompt)

            if "SUBJECTIVE:" in note:
                note = note[note.find("SUBJECTIVE:"):]

            valid, reason = validate_soap_output(note)

        status = "COMPLETED" if valid else "FAILED"

        # 5️⃣ Save result
        soap.content = note if valid else f"INVALID SOAP OUTPUT: {reason}"
        soap.status = status
        db.commit()

        # 6️⃣ Store embedding
        if status == "COMPLETED":
            store_note_embedding(
                doctor_id=doctor_id,
                patient_id=patient_id,
                soap_note=note,
                note_id=soap_id,
            )

        logger.info(f"TASK END | SOAP_ID={soap_id} | STATUS={status}")

    except Exception:
        logger.exception(f"TASK FAILED | SOAP_ID={soap_id}")
        db.rollback()
        failed = db.query(SOAPNote).filter(SOAPNote.id == soap_id).first()
        if failed:
            failed.status = "FAILED"
            failed.content = "Generation failed due to an internal error."
            db.commit()

    finally:
        db.close()
