# SOAPify Frontend Dashboard (React + Tailwind)

Dark-themed React dashboard connected to SOAPify backend features:

- Register/Login
- Current user profile
- Generate SOAP note
- Poll note status
- Update SOAP note
- Dashboard data list
- Patient history

## Setup

1. Copy environment file and set backend URL:

```bash
cp .env.example .env
```

2. Install dependencies:

```bash
npm install
```

3. Start dev server:

```bash
npm run dev
```

Backend default URL is `http://localhost:8000` unless overridden via `VITE_API_BASE_URL`.
