# CareerPilotAI

**An AI-powered career guidance platform** that helps job seekers
analyze resumes, discover relevant jobs through semantic similarity,
prepare for interviews, and receive personalized career guidance.

CareerPilotAI combines a browser-based frontend, a FastAPI backend, a
relational database, AI-powered resume analysis, OCR-based text
extraction, and embedding-based job recommendations.

> **Project status:** Diploma major project. Features and setup details
> should be verified against the current codebase before production
> deployment.

## Table of Contents

-   [Features](#features)
-   [Technology Stack](#technology-stack)
-   [Architecture](#architecture)
-   [Project Structure](#project-structure)
-   [Configuration](#configuration)
-   [Local Setup on Windows](#local-setup-on-windows)
-   [API Documentation](#api-documentation)
-   [Security Notes](#security-notes)
-   [Troubleshooting](#troubleshooting)
-   [Planned Improvements](#planned-improvements)
-   [Author](#author)
-   [License](#license)

## Features

### Authentication and User Accounts

-   User registration and login
-   JWT-based authentication
-   Password hashing and protected endpoints

### Resume Management and Analysis

-   Upload and manage resumes
-   PDF and DOCX processing
-   Resume history and deletion
-   AI-generated resume analysis, including an ATS score, summary,
    skills, strengths, weaknesses, and improvement suggestions

### OCR and Resume Text Extraction

The application supports two extraction paths: - Text-based PDFs:
extract selectable text using `pdfplumber` - Scanned PDFs: use EasyOCR
for OCR-based text extraction

### Semantic Job Recommendations

The recommendation workflow uses text embeddings and similarity ranking
to find jobs that are semantically relevant to a resume, rather than
relying only on exact keyword matches.

High-level workflow:

1.  Process the resume.
2.  Generate or retrieve embeddings.
3.  Compare resume and job representations.
4.  Rank relevant jobs.
5.  Present recommendations and supporting AI-generated explanations
    where implemented.

### AI Career Mentor

-   Personalized career guidance
-   Resume-aware conversations
-   Conversation history and Markdown support, where enabled by the
    current implementation

### Mock Interviews

The interview module is designed to support: - Technical, HR,
behavioral, and mixed interview types - Easy, medium, and hard
difficulty levels - AI-generated questions and answer evaluation - Final
interview reports and PDF downloads

The exact options available depend on the current application
implementation and configured AI provider.

## Technology Stack

### Frontend

-   HTML5
-   CSS3
-   Vanilla JavaScript (ES6)
-   Tailwind CSS via CDN
-   Font Awesome
-   Google Fonts (Inter)

### Backend

-   Python
-   FastAPI
-   SQLAlchemy
-   Pydantic and Pydantic Settings
-   Uvicorn
-   Alembic for database migrations
-   JWT-related libraries (`python-jose`)
-   Password-hashing libraries (`passlib`, `bcrypt`, and `pwdlib` are
    present in the dependency list)

### AI, Embeddings, and Document Processing

-   OpenRouter-compatible chat-completions API configuration
-   NVIDIA embedding API configuration
-   EasyOCR
-   `pdfplumber`
-   `python-docx`
-   ReportLab for PDF generation

### Database

-   SQLAlchemy database access
-   PostgreSQL driver packages (`psycopg` and `psycopg-binary`) are
    included
-   The application reads its database connection from `DATABASE_URL`

The actual database engine is determined by the configured
`DATABASE_URL`. This README does not assume that a particular local or
hosted database has already been provisioned.

## Architecture

### High-Level Request Flow

``` text
Browser frontend
      |
      v
Frontend API layer
      |
      v
FastAPI application
      |
      v
Routers / API endpoints
      |
      v
Application services
      |
      +------------------+
      |                  |
      v                  v
Database layer       AI / OCR / Embeddings
      |                  |
      v                  v
Relational DB        External provider APIs
```

The precise module boundaries and data flow should be read alongside the
current source code.

### Resume Analysis Workflow

``` text
Resume upload
     |
     v
PDF / DOCX processing
     |
     +--> Selectable PDF text --> pdfplumber
     |
     +--> Scanned PDF ---------> EasyOCR
     |
     v
Extracted resume text
     |
     v
AI resume analysis
     |
     v
ATS score, summary, skills, strengths,
weaknesses, and improvement suggestions
```

### Semantic Recommendation Workflow

``` text
Resume and job data
       |
       v
Embedding generation / retrieval
       |
       v
Similarity calculation and ranking
       |
       v
Relevant job recommendations
       |
       v
Optional AI-generated explanations
```

## Project Structure

The following is a representative structure based on the project
documentation. Folder contents may change as the project evolves.

``` text
CareerPilotAI/
├── backend/
│   ├── app/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── resumes/
│   │   ├── resume_analysis/
│   │   ├── jobs/
│   │   ├── career_chatbot/
│   │   ├── interviews/
│   │   ├── similarity/
│   │   ├── ocr/
│   │   ├── extractions/
│   │   ├── db/
│   │   └── core/
│   ├── alembic/
│   ├── alembic.ini
│   └── requirements.txt
└── frontend/
    ├── assets/
    ├── components/
    ├── css/
    ├── js/
    ├── pages/
    └── index.html
```

## Configuration

The backend uses Pydantic Settings and loads environment variables from
a `.env` file. The configuration declares the following settings.

Create `backend/.env` and provide values appropriate for your
environment. **Never commit the real `.env` file or publish API keys,
passwords, or JWT secrets.**

### Required settings

At minimum, the supplied configuration declares these settings as
required:

``` env
DATABASE_URL=your_database_connection_url

SECRET_KEY=replace_with_a_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEYS=your_openrouter_api_key
AI_MODELS=provider/model-name

AI_TEMPERATURE=0.2
AI_MAX_TOKENS=2048
AI_MAX_RETRIES=3

AI_TIMEOUT=60
AI_CONNECT_TIMEOUT=10
AI_WRITE_TIMEOUT=30
AI_POOL_TIMEOUT=10
AI_MAX_CONNECTIONS=20
AI_MAX_KEEPALIVE=10
AI_BACKOFF_BASE_SECONDS=1

NVIDIA_PRIMARY_API_KEY=your_nvidia_api_key
NVIDIA_FALLBACK_API_KEY=your_nvidia_fallback_api_key
```

The numeric values above are examples, not verified production defaults.
Use values appropriate to the current code and provider limits. Confirm
all required settings and accepted values against
`backend/app/core/config.py` before starting the application.

`OPENROUTER_API_KEYS` and `AI_MODELS` accept comma-separated lists in
the current configuration. The embedding configuration uses NVIDIA by
default and includes configurable primary and fallback models.

### Optional email and frontend settings

``` env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=
SMTP_PASSWORD=
FRONTEND_BASE_URL=http://localhost:5500
EMAIL_DEV_MODE=false

OPENROUTER_SITE_URL=
OPENROUTER_SITE_NAME=
```

Only configure email credentials if you use the email functionality. For
deployment, set `FRONTEND_BASE_URL` to the actual frontend origin and
configure the email development mode deliberately.

> **Important:** The settings above document names declared by the
> supplied configuration file. Check the actual `.env` loading location
> and required values in the current repository. Do not copy placeholder
> values into a production environment.

## Local Setup on Windows

These instructions assume Windows PowerShell, Python, and a database
that is already configured for the project.

### 1. Clone the repository

Replace the URL below with the actual GitHub repository URL after
publishing the project.

``` powershell
git clone https://github.com/YOUR_GITHUB_USERNAME/CareerPilotAI.git
cd CareerPilotAI
```

### 2. Create and activate a virtual environment

``` powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, follow your system's execution-policy
guidance or invoke the virtual environment's Python executable directly.

### 3. Configure environment variables

Create `backend/.env` using the variable names in the Configuration
section and the actual requirements of `backend/app/core/config.py`.

Before proceeding, make sure: - `DATABASE_URL` points to the intended
database. - JWT settings are set to secure values. - AI provider keys
and model IDs are valid. - NVIDIA embedding credentials are configured
if the embedding functionality is used. - Optional email settings are
configured only if needed.

### 4. Apply database migrations

The repository includes Alembic configuration. From the `backend`
directory, run:

``` powershell
alembic upgrade head
```

Run this only after confirming that the Alembic environment is
configured to load the intended database URL. Back up important data
before applying migrations, especially when using a database that
already contains project data.

### 5. Start the backend

From the `backend` directory with the virtual environment activated:

``` powershell
uvicorn app.main:app --reload
```

If startup succeeds, the default local URLs are:

-   API: `http://127.0.0.1:8000`
-   Swagger UI: `http://127.0.0.1:8000/docs`
-   ReDoc: `http://127.0.0.1:8000/redoc`

If the application entry point or configuration differs in your
checked-out version, follow the current source code and startup logs.

### 6. Start the frontend

Open a second PowerShell terminal from the repository root:

``` powershell
cd frontend
python -m http.server 5500
```

Then open `http://localhost:5500` in your browser. The frontend uses
HTML, CSS, and vanilla JavaScript; the documented setup does not require
a Node/npm build step.

Make sure the frontend API base URL and backend CORS configuration
permit local frontend requests.

### 7. Verify the application

1.  Confirm the backend starts without errors.
2.  Open the API documentation at `http://127.0.0.1:8000/docs`.
3.  Open the frontend at `http://localhost:5500`.
4.  Test registration and login.
5.  Upload a test resume and verify text extraction and analysis.
6.  Test job recommendations, career guidance, and mock interviews if
    those services are configured.
7.  Review browser DevTools and backend logs for failed requests.

## API Documentation

When the backend is running, FastAPI's interactive API documentation is
available at:

-   Swagger UI: `http://127.0.0.1:8000/docs`
-   ReDoc: `http://127.0.0.1:8000/redoc`

The exact endpoints and request schemas are defined by the running
backend.

## Security Notes

-   Keep `.env` files, API keys, SMTP passwords, database credentials,
    and JWT secrets out of Git.
-   Use a strong, unique `SECRET_KEY` outside local development.
-   Do not commit real resumes, user data, database dumps, logs
    containing personal information, or generated secrets.
-   Configure CORS for only the frontend origins that need access.
-   Use HTTPS and secure deployment environment variables in production.
-   Review upload validation, file-size limits, authorization checks,
    and error responses before public deployment.
-   If a credential was committed or exposed, rotate it. Adding it to
    `.gitignore` does not remove it from Git history.

## Troubleshooting

  -----------------------------------------------------------------------
  Problem                             What to check
  ----------------------------------- -----------------------------------
  Backend fails to start              Read the complete traceback; verify
                                      dependencies, imports, required
                                      environment variables, and database
                                      connectivity.

  Settings validation error           Check that every required setting
                                      in `config.py` is present and
                                      correctly named in `.env`.

  AI provider request fails           Verify provider URL, API key, model
                                      ID, account access, quota, and
                                      supported request parameters.

  Embedding request fails             Verify NVIDIA API credentials,
                                      endpoint, model configuration, and
                                      provider access.

  Frontend cannot call the API        Check that both servers are
                                      running, the frontend API base URL
                                      is correct, and backend CORS
                                      permits the frontend origin.

  Alembic migration fails             Verify the database URL, migration
                                      environment, migration files, and
                                      that the command is run from the
                                      correct directory.

  Port is already in use              Stop the process using the port or
                                      choose another port and update the
                                      relevant configuration.

  OCR processing fails                Check the OCR dependencies,
                                      supported input format, available
                                      system resources, and backend logs.
  -----------------------------------------------------------------------

## Planned Improvements

The original project documentation lists the following as future
improvements. They should be treated as planned work, not as implemented
features, unless the current code confirms otherwise:

-   Cloud deployment
-   Multi-language support
-   Expanded analytics and filtering
-   AI-assisted job application drafts
-   Weakness-focused application optimization
-   Job-match explanations
-   Skill-gap analysis with learning resources
-   Dark/light theme toggle and further UI refinement

## Screenshots

Add current screenshots of the working application here, for example:

-   Login and registration
-   Dashboard
-   Resume analysis
-   Job recommendations
-   Career mentor
-   Mock interview
-   Interview report PDF

Use screenshots that do not expose personal data, API keys, tokens, or
other secrets.

## Author

**Mustafa Khan**\
Diploma ITR Project --- Computer Engineering

## License

This project was developed for educational purposes as part of a diploma
major project. No formal open-source license is specified here. If you
want others to reuse, modify, or distribute the code, choose and add an
appropriate license file.
