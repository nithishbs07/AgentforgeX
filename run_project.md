# Run Project Guide

Follow these instructions to start the AgentForge-X project on Windows.

## 1. Start FastAPI Backend

Open a Command Prompt or PowerShell window and execute:

```cmd
cd /d D:\PROJECTS\agentforge-x\backend
..\backend\venv\Scripts\python -m uvicorn app.main:app --reload
```

*   **Endpoint**: `http://127.0.0.1:8000`
*   **Swagger API Docs**: `http://127.0.0.1:8000/docs`
*   **Readiness Endpoint**: `http://127.0.0.1:8000/monitoring/readiness`

---

## 2. Start Next.js Frontend

Open a separate Command Prompt or PowerShell window and execute:

```cmd
cd /d D:\PROJECTS\agentforge-x\frontend
npm run dev
```

*   **URL**: `http://127.0.0.1:3000` (or the dev URL printed by Next.js)
