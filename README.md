# CareerPilotAI

An AI-Powered Career Guidance Platform that helps job seekers improve their resumes, discover relevant jobs through semantic search, prepare for interviews, and receive personalized career guidance using Large Language Models.

## Overview

CareerPilotAI is a full-stack web application designed to assist users throughout their career journey. The platform combines AI, semantic search, OCR, and resume analysis into a single system.

Unlike traditional career platforms, CareerPilotAI uses semantic embeddings to recommend jobs based on meaning rather than simple keyword matching.

## Features
### Authentication
JWT Authentication
Secure Login & Registration
Protected Routes
Password Hashing
### Resume Management
Upload Resume
PDF Support
DOCX Support
Resume History
Delete Resume
### OCR Support

Automatically detects scanned PDFs.

PDF
│
├── Text-based PDF
│      ↓
│   pdfplumber
│
└── Scanned PDF
       ↓
    EasyOCR
### AI Resume Analysis

Generates:

Executive Summary
ATS Score
Skills
Experience
Education
Strengths
Weaknesses
Career Suggestions
Improvement Areas
### Semantic Job Recommendations

Unlike keyword search, CareerPilotAI uses semantic embeddings.

Pipeline:

Resume
      ↓
Resume Analysis
      ↓
Embedding Generation
      ↓
Similarity Search
      ↓
Top Matching Jobs
      ↓
AI Enhancement
      ↓
Recommendations
### AI Career Mentor
Personalized career guidance
Resume-aware conversations
Markdown support
Conversation history
### Mock Interview

Supports:

Technical
HR
Behavioral
Mixed

Difficulty:

Easy
Medium
Hard

Features:

AI-generated questions
AI answer evaluation
Final report generation
PDF download
## Technology Stack
### Frontend
HTML5
CSS3
Tailwind CSS (CDN)
Vanilla JavaScript (ES6)
Font Awesome
Google Fonts (Inter)
### Backend
Python
FastAPI
SQLAlchemy
Pydantic
JWT Authentication
bcrypt / passlib
SQLite (Development)
### AI & Machine Learning
OpenRouter
Semantic Embeddings
Similarity Search
OCR (EasyOCR)
### Resume Processing
pdfplumber
python-docx
EasyOCR
### PDF Generation
ReportLab
## Architecture
### Frontend
     │
     ▼
API Layer
     │
     ▼
FastAPI Backend
     │
     ▼
Business Services
     │
     ├────────── Database
     │
     ├────────── AI
     │
     └────────── Similarity Engine
### Backend Architecture
Router
    │
    ▼
Service
    │
    ▼
Repository
    │
    ▼
Database

Business logic resides exclusively in the Service layer.

## Project Structure
CareerPilotAI/

backend/
│
├── app/
│   ├── auth/
│   ├── users/
│   ├── resumes/
│   ├── resume_analysis/
│   ├── jobs/
│   ├── career_chatbot/
│   ├── interviews/
│   ├── similarity/
│   ├── ocr/
│   ├── extractions/
│   ├── db/
│   └── core/
│
├── alembic/
└── requirements.txt

frontend/
│
├── css/
├── js/
├── pages/
├── assets/
└── index.html
## Semantic Recommendation Engine

CareerPilotAI does not use:

Keyword Search
TF-IDF
Regular Expressions

Instead it performs:

Resume

↓

Embedding

↓

Vector Similarity

↓

Ranking

↓

AI Explanation

This enables more intelligent recommendations by understanding semantic meaning instead of relying on exact keyword matches.

## OCR Workflow
Upload Resume

↓

PDF

↓

Has Selectable Text?

YES ─────────► Extract Text

NO

↓

EasyOCR

↓

Extract Text

↓

Resume Analysis
## Interview Workflow
Create Interview

↓

Generate Questions

↓

Submit Answers

↓

AI Evaluation

↓

Generate Final Report

↓

Download PDF
## Performance Optimizations
Server-side pagination for job listings
Centralized API layer
JWT authentication
Cached resume analyses
Cached interview reports
Modular backend architecture
Semantic similarity search
## Security
JWT Authentication
Password Hashing
Input Validation
Protected Endpoints
Pydantic Validation
Backend Authorization

## Installation and Local Setup

Follow these steps to run CareerPilotAI locally. The commands below use **Windows PowerShell**.

### Prerequisites

- Git
- Python installed and available as `python`
- A database configured for this project
- An API key from an AI provider that supports an OpenAI-compatible chat-completions API, such as OpenRouter
- Internet access for configured AI services and CDN-hosted frontend assets

### 1. Clone the repository

```powershell
git clone https://github.com/MustafaKhan08/CareerPilotAI.git
cd CareerPilotAI
```

### 2. Configure environment variables

If `backend/.env.example` exists, copy it:

```powershell
Copy-Item backend/.env.example backend/.env
```

If it does not exist, create `backend/.env` manually using the variable names required by `backend/app/core/config.py`.

#### Configure an AI provider (example: OpenRouter)

Create an API key with your chosen provider. For OpenRouter, configure the following in `backend/.env`:

```env
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEYS=your_openrouter_api_key
AI_MODELS="provider/model-name"
```

Replace `your_openrouter_api_key` with your own key and `provider/model-name` with an exact model ID available to your account. Check the provider's current documentation for the correct base URL, model ID, supported parameters, quotas, and pricing.

You may use another provider if it supports an OpenAI-compatible chat-completions endpoint. Set `OPENROUTER_BASE_URL` to that provider's API base URL, `OPENROUTER_API_KEYS` to its API key, and `AI_MODELS` to the provider's exact model ID. These are the environment-variable names used by the current project configuration; they do not require you to use OpenRouter.

If your configured application uses separate embedding credentials, keep those settings configured as required by `backend/app/core/config.py`. Changing the chat provider does **not** automatically change the embedding provider.

**Security:** Keep API keys in the backend `.env` file. Never place them in frontend JavaScript, commit them to Git, or include real credentials in screenshots or issue reports.

### 3. Install backend dependencies

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, follow your system's execution-policy guidance or invoke the virtual environment's Python executable directly.

### 4. Prepare the database

Make sure your configured database is available and the database URL in `backend/.env` is correct.

If this project version uses Alembic migrations, run this command **from the `backend` directory**:

```powershell
alembic upgrade head
```

Run migrations only after configuring the database connection. If your current setup initializes the database another way, follow the method implemented in the repository.

### 5. Start the backend

From the `backend` directory, with `.venv` activated:

```powershell
uvicorn app.main:app --reload
```

When startup succeeds, open:

- API: `http://127.0.0.1:8000`
- Swagger API documentation: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Keep this terminal open. Fix any startup traceback or configuration error before continuing.

### 6. Start the frontend

Open a **second terminal**. From the repository root:

```powershell
cd frontend
python -m http.server 5500
```

Open `http://localhost:5500` in your browser. The project structure lists `frontend/index.html` as the main entry page.

Keep the frontend terminal open too. The frontend uses HTML, CSS, and vanilla JavaScript, so the documented setup does not require a Node/npm build step.

### 7. Verify the setup

1. Open `http://127.0.0.1:8000/docs` and confirm that FastAPI is running.
2. Open `http://localhost:5500` and confirm that the frontend loads.
3. Test a feature that calls the AI provider.
4. If AI requests fail, verify the base URL, API key, exact model ID, provider access/quota, and backend logs.
5. If browser requests fail, check the frontend API base URL and the backend CORS configuration.

### Troubleshooting

| Problem | What to check |
|---|---|
| Backend fails to start | Read the complete traceback; check imports, dependencies, `.env` values, and database connectivity. |
| API key/model configuration error | Confirm variable names match `backend/app/core/config.py` and that the key and model values are not blank. |
| AI provider returns an error | Check the provider URL, model ID, account access, quota, and supported request parameters. |
| Frontend cannot call the API | Confirm both servers are running, the API base URL is correct, and CORS permits the frontend origin. |
| Migration fails | Check database availability, connection settings, and that the command is run from `backend`. |
| Port is already in use | Stop the process using the port or choose another port and update the relevant configuration. |

## Future Improvements

- Cloud deployment
- Multi-language support
- Analytics dashboard
- Advanced filtering
- **Voice-to-text interview responses** for answering interview questions verbally.
- **Timed mock interviews** with countdown timers and time limits for realistic interview practice.
- **AI-assisted job applications** that generate tailored application drafts based on the user's resume and target job description.
- **Weakness-focused application optimization** that addresses skill gaps and weaknesses identified in the resume analysis, while accurately highlighting the user's relevant strengths and experience.
- **Job Match Explanation:** Explain why a job matches the user's resume by highlighting matching skills, relevant experience, and missing requirements.
- **Skill Gap Analyzer:** Identify the skills a user needs to develop for a target job and recommend relevant courses and learning resources.
- **AI Resume Improvement Editor:** Suggest improved resume bullet points and compare the original content with AI-enhanced versions tailored to a target job.
- **Improved UI with dark/light theme toggle option**
- **Cleaner and more professional UI**
## Screenshots

Add screenshots here after deployment.

Example:

Login

Dashboard

Resume Analysis

Jobs

Career Mentor

Interview

PDF Report
## Author

Mustafa Khan

Diploma Major Project

Computer Engineering

## License

This project is developed for educational purposes as part of a diploma project.
