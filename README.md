# Job Search AI Agent

A lightweight job-search assistant. Upload a PDF or TXT resume to extract skills, find live roles in the selected location, rank them by role and skill match, check a specific job description, and create a cover-letter draft. It uses transparent keyword and alias matching—no external AI model is required.

## Run

Start the backend:

```powershell
cd "C:\Users\armil\Downloads\Job Search AI Agent\backend"
..\venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

In a second terminal, start the frontend:

```powershell
cd "C:\Users\armil\Downloads\Job Search AI Agent\frontend"
npm run dev
```

Open http://127.0.0.1:5173.

## Direct India job cards (optional)

The included public feeds mostly contain remote and international roles. To show individual, live India listings directly in the app, create `backend/.env` from `backend/.env.example` and add free Adzuna API credentials:

```text
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

Restart the backend after adding the credentials. Searches such as `AI Engineer` in `Hyderabad` will then return Adzuna job cards directly in the results list.
