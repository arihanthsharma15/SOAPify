# SOAPify

> SOAPify is a production-oriented, async AI system that converts raw doctor-patient conversations into validated SOAP notes using strict prompt discipline, retrieval-augmented generation (RAG), and secure multi-user isolation.

SOAPify is an AI-powered clinical scribe designed around real-world clinical workflows.
It focuses on correctness, reliability, data isolation, and system design.

## Monorepo Structure

- `soapify-backend/` - FastAPI backend
- `soapify-frontend/` - React + Tailwind frontend

## Live Demo

- Frontend (React + Tailwind): https://soa-pify.vercel.app
- Backend API: https://soapify-production.up.railway.app

## Deployment Notes

- Frontend is deployed on Vercel as a static Vite app.
- Backend is deployed on Railway.
- Backend health endpoint: `/health`

## Key Features

### AI-Powered SOAP Generation
- Converts free-form clinical transcripts into strict SOAP format
- Enforces clinical discipline:
  - No hallucinated vitals
  - No invented diagnoses
  - Explicit handling of missing information (`Not mentioned`)

### Retrieval-Augmented Generation (RAG)
- Retrieves only previous SOAP notes of the same patient
- Injects relevant past medical history into the prompt
- RAG retrieval is scoped by `doctor_id + patient_id`
- Prevents cross-patient and cross-doctor data leakage

### Asynchronous & Scalable
- SOAP generation runs as background tasks (non-blocking)
- Frontend polls status:
  - `PROCESSING -> COMPLETED / FAILED`
- Supports multiple doctors generating notes concurrently

### Secure Authentication & Isolation
- JWT-based login & signup
- Doctor-scoped data isolation
- Each doctor can access only their own patients and notes

### Human-in-the-Loop Editing
- Generated SOAP notes can be reviewed and edited by the clinician
- Updates are saved back to the database
- Supports real clinical review workflows

Clinical documentation is a high-stakes domain where AI outputs cannot be blindly trusted.
SOAPify intentionally keeps a human-in-the-loop, ensuring the final clinical note is always reviewed and approved by a doctor before use.

### Interactive Dashboard
- Sidebar dashboard showing recent SOAP notes
- Click to view past notes
- Create new SOAP notes without logout or refresh

## Architectural Diagram

![SOAPify Architecture Diagram](./image.png)




## Architectural Style: Modular Monolith

SOAPify is intentionally designed as a modular monolith, not a microservices setup.

### Why Modular Monolith?
- Early-stage systems benefit from simplicity and debuggability
- Avoids premature microservice complexity
- Enables clear domain boundaries with shared infrastructure

### Module Boundaries
- Auth Module - authentication & authorization
- User Module - doctor accounts & identity
- Notes Module - transcripts, SOAP notes, edits
- RAG Module - patient history retrieval & embeddings
- LLM Module - model orchestration (Ollama / Groq)

Modules communicate via explicit interfaces, not shared globals.

## Tech Stack

### Backend
- FastAPI - async REST API
- Layered Modular Monolith architecture (domain boundaries enforced at service & API layers)
- PostgreSQL (Neon/local) - relational database
- SQLAlchemy - ORM
- JWT (python-jose) - authentication
- BackgroundTasks - async SOAP generation

### AI / RAG
- Groq API - production LLM inference
- Ollama - local development/testing fallback
- ChromaDB - vector database for RAG
- Sentence Transformers - embeddings

### Frontend
- React (Vite) - SPA dashboard
- Tailwind CSS - styling system
- Fetch API + JWT Bearer auth - API integration

### Infrastructure
- Railway - backend deployment
- Vercel - frontend deployment
- Docker + Docker Compose - local development

## Prompt Engineering

SOAPify uses a strict, rule-based clinical prompt:
- Exact SOAP section ordering enforced
- Explicit rules for SUBJECTIVE vs OBJECTIVE separation
- No assumptions or inferred diagnoses
- Validation layer rejects malformed SOAP output

## Application Flow

1. Doctor logs in / signs up
2. Past SOAP notes load in the dashboard
3. Doctor submits a new clinical transcript
4. Backend:
   - Saves transcript
   - Fetches patient history (RAG)
   - Calls LLM asynchronously
   - Validates SOAP output
   - Stores SOAP note + embeddings
5. Frontend polls status and displays SOAP note
6. Doctor edits or creates follow-up notes

## Why This Problem Is Non-Trivial

- Clinical notes cannot tolerate hallucinations
- LLM latency breaks synchronous APIs
- RAG systems are prone to cross-user data leakage
- Doctors need editable, auditable outputs

SOAPify addresses these challenges with guardrails, async design, and strict isolation.

## What This Project Demonstrates

- Real-world AI system design (not toy demos)
- Handling LLM latency and failures
- Preventing data leakage in RAG pipelines
- Clean separation of concerns (UI, API, AI, DB)
- Production deployment & debugging experience

## Planned Enhancements

- Rate limiting & API key scopes
- Role-based access (admin / reviewer)
- Export SOAP notes as PDF
- Structured medical coding (ICD / SNOMED)
- Audit logs for clinical compliance

## Running Locally

### Backend (`soapify-backend`)

1. Create and activate venv:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set env vars (`.env`) at minimum:
- `DATABASE_URL`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `LLM_PROVIDER`
- `GROQ_API_KEY` (if using Groq)
- `GROQ_MODEL`
- `CHROMA_PERSIST_DIR`

4. Run API:
```bash
python -m uvicorn app.main:app --reload
```

### Frontend (`soapify-frontend`)

1. Install dependencies:
```bash
npm install
```

2. Set env:
```bash
cp .env.example .env
```
Set:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

3. Run app:
```bash
npm run dev
```

## Production Config

### Railway (Backend)
- Root Directory: `soapify-backend`
- Build Command: `pip install -r requirements.txt`
- Start Command:
```bash
sh -c 'uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}'
```
- Healthcheck Path: `/health`
- Keep `Serverless` OFF (recommended for this workload)

Required Railway variables:
- `DATABASE_URL`
- `SECRET_KEY`
- `ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=1440`
- `LLM_PROVIDER=groq`
- `GROQ_API_KEY`
- `GROQ_MODEL=llama-3.1-8b-instant`
- `CHROMA_PERSIST_DIR=/tmp/soapify-chroma`

### Vercel (Frontend)
- Root Directory: `soapify-frontend`
- Framework: Vite
- Build Command: `npm run build`
- Output Directory: `dist`

Required Vercel variable:
```env
VITE_API_BASE_URL=https://soapify-production.up.railway.app
```
