CareerPilotAI

An AI-Powered Career Guidance Platform that helps job seekers improve their resumes, discover relevant jobs through semantic search, prepare for interviews, and receive personalized career guidance using Large Language Models.

Overview

CareerPilotAI is a full-stack web application designed to assist users throughout their career journey. The platform combines AI, semantic search, OCR, and resume analysis into a single system.

Unlike traditional career platforms, CareerPilotAI uses semantic embeddings to recommend jobs based on meaning rather than simple keyword matching.

Features
Authentication
JWT Authentication
Secure Login & Registration
Protected Routes
Password Hashing
Resume Management
Upload Resume
PDF Support
DOCX Support
Resume History
Delete Resume
OCR Support

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
AI Resume Analysis

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
Semantic Job Recommendations

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
AI Career Mentor
Personalized career guidance
Resume-aware conversations
Markdown support
Conversation history
Mock Interview

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
Technology Stack
Frontend
HTML5
CSS3
Tailwind CSS (CDN)
Vanilla JavaScript (ES6)
Font Awesome
Google Fonts (Inter)
Backend
Python
FastAPI
SQLAlchemy
Pydantic
JWT Authentication
bcrypt / passlib
SQLite (Development)
AI & Machine Learning
OpenRouter
Semantic Embeddings
Similarity Search
OCR (EasyOCR)
Resume Processing
pdfplumber
python-docx
EasyOCR
PDF Generation
ReportLab
Architecture
Frontend
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
Backend Architecture
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

Project Structure
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
Semantic Recommendation Engine

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

OCR Workflow
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
Interview Workflow
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
Performance Optimizations
Server-side pagination for job listings
Centralized API layer
JWT authentication
Cached resume analyses
Cached interview reports
Modular backend architecture
Semantic similarity search
Security
JWT Authentication
Password Hashing
Input Validation
Protected Endpoints
Pydantic Validation
Backend Authorization
Installation
Clone Repository
git clone https://github.com/<your-username>/CareerPilotAI.git
cd CareerPilotAI
Configure Environment

Copy:

backend/.env.example

to:

backend/.env

Fill in the required credentials.

Install Backend Dependencies
cd backend
pip install -r requirements.txt
Run Database Migrations
alembic upgrade head
Start Backend
uvicorn app.main:app --reload
Open Swagger
http://localhost:8000/docs
Future Improvements
Email verification
Resume version comparison
Cloud deployment
Multi-language support
Company-specific interview preparation
Analytics dashboard
Advanced filtering
Screenshots

Add screenshots here after deployment.

Example:

Login

Dashboard

Resume Analysis

Jobs

Career Mentor

Interview

PDF Report
Author

Mustafa Khan

Diploma Major Project

Computer Engineering

License

This project is developed for educational purposes as part of a diploma major project.