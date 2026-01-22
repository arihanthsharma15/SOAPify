# SOAPify 🩺

> **TL;DR**  
> SOAPify is a production-grade, async AI system that converts raw doctor–patient conversations into validated SOAP notes using strict prompt discipline, retrieval-augmented generation (RAG), and secure multi-user isolation.

SOAPify is an AI-powered clinical scribe designed around **real-world clinical workflows**, not toy demos.  
It focuses on **correctness, reliability, data isolation, and system design** — not just calling an LLM.

---

## 🚀 Live Demo

- **Frontend (Streamlit):** https://soapify-scribe.streamlit.app/  
- **Backend API:** https://soapify-backend.onrender.com  

---

## ✨ Key Features

### 🧠 AI-Powered SOAP Generation
- Converts free-form clinical transcripts into **strict SOAP format**
- Enforces clinical discipline:
  - No hallucinated vitals
  - No invented diagnoses
  - Explicit handling of missing information (`Not mentioned`)

---

### 🔁 Retrieval-Augmented Generation (RAG)
- Retrieves **only previous SOAP notes of the same patient**
- Injects **relevant past medical history** into the prompt
- RAG retrieval is scoped by **doctor_id + patient_id**
- Prevents **cross-patient and cross-doctor data leakage**

---

### ⚡ Asynchronous & Scalable
- SOAP generation runs as **background tasks** (non-blocking)
- Frontend polls status:
  - `PROCESSING → COMPLETED / FAILED`
- Supports **multiple doctors generating notes concurrently**

---

### 🔐 Secure Authentication & Isolation
- JWT-based login & signup
- Doctor-scoped data isolation
- Each doctor can access **only their own patients and notes**

---

### ✍️ Human-in-the-Loop Editing
- Generated SOAP notes can be reviewed and edited
- Updates are saved back to the database
- Supports real clinical review workflows

---

### 📊 Interactive Dashboard
- Sidebar dashboard showing recent SOAP notes
- Click to view past notes
- Create new SOAP notes without logout or refresh

---

## 🏗️ System Architecture




┌──────────────┐ ┌──────────────────┐ ┌─────────────────┐
│ Streamlit │ ---> │ FastAPI API │ ---> │ PostgreSQL DB │
│ Frontend │ │ (Async + JWT) │ │ (Neon Cloud) │
└──────────────┘ └──────────────────┘ └─────────────────┘
│ │
│ ▼
│ ┌─────────────────┐
│ │ RAG Engine │
│ │ (ChromaDB) │
│ └─────────────────┘
│ │
▼ ▼
┌──────────────────────────────────────────┐
│ LLM Inference Layer │
│ • Ollama (local development) │
│ • Groq API (production inference) │
└──────────────────────────────────────────┘



---

## 🧩 Tech Stack

### Backend
- FastAPI — async REST API
- PostgreSQL (Neon) — relational database
- SQLAlchemy — ORM
- JWT (python-jose) — authentication
- BackgroundTasks — async SOAP generation

### AI / RAG
- Groq API — production LLM inference
- Ollama — local development & testing
- ChromaDB — vector database for RAG
- Sentence Transformers — embeddings

### Frontend
- Streamlit — UI & dashboard
- Session State — auth & navigation control

### Infrastructure
- Render — backend deployment
- Streamlit Cloud — frontend hosting
- Docker — local development

---

## 🧠 Prompt Engineering (Key Differentiator)

SOAPify uses a **strict, rule-based clinical prompt**:

- Exact SOAP section ordering enforced
- Explicit rules for SUBJECTIVE vs OBJECTIVE separation
- No assumptions or inferred diagnoses
- Validation layer rejects malformed SOAP output

This prompt discipline makes the system **interview-ready and industry-grade**.

---

## 🔄 Application Flow

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

---

## 🚧 Why This Problem Is Non-Trivial

- Clinical notes cannot tolerate hallucinations
- LLM latency breaks synchronous APIs
- RAG systems are prone to cross-user data leakage
- Doctors need editable, auditable outputs

SOAPify addresses these challenges with **guardrails, async design, and strict isolation**.

---

## 🧪 What This Project Demonstrates

- Real-world AI system design (not toy demos)
- Handling LLM latency and failures
- Preventing data leakage in RAG pipelines
- Clean separation of concerns (UI, API, AI, DB)
- Production deployment & debugging experience

---

## 📌 Planned Enhancements

- Rate limiting & API key scopes
- Role-based access (admin / reviewer)
- Export SOAP notes as PDF
- Structured medical coding (ICD / SNOMED)
- Audit logs for clinical compliance

---

This project was built to reflect **how real AI products are engineered**, not just how models are called.
