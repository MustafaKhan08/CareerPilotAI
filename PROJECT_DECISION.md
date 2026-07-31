# CareerPilotAI - Project Decisions

**Version:** 1.0.0

**Last Updated:** 27 July 2026

---

# Project Vision

CareerPilotAI is an AI-first Career Platform designed as a startup-style MVP rather than a traditional college project.

The goal is to build an intelligent platform that helps users improve their careers using AI-powered analysis and recommendations instead of relying on traditional keyword-based systems.

The platform will allow users to:

- Upload resumes
- Receive AI-powered resume analysis
- Calculate ATS scores
- Find relevant job opportunities
- Perform semantic job matching
- Identify skill gaps
- Receive personalized course recommendations
- Generate AI-powered interview questions
- Generate AI career roadmaps
- Receive personalized career guidance

---

# Technology Decisions

## Frontend

- React
- Vite
- Tailwind CSS
- Axios

### Reason

React provides a modern component-based architecture, excellent ecosystem support, and integrates well with FastAPI.

---

## Backend

- FastAPI
- SQLAlchemy

### Reason

FastAPI offers:

- High performance
- Asynchronous support
- Easy REST API development
- Excellent AI integration
- Automatic API documentation

---

## Database

- PostgreSQL

### Reason

PostgreSQL is reliable, scalable, and supports extensions such as pgvector, making it suitable for semantic search and AI-based applications.

---

## AI

- Ollama
- Local Large Language Model (Model to be finalized later)

### Reason

Using a local LLM provides:

- Privacy
- No API costs
- Offline capability
- Full control over AI inference

---

## Semantic Search

- Embeddings
- pgvector (planned)

### Reason

Semantic search provides significantly better matching than traditional keyword searches by understanding the meaning behind text.

---

## Version Control

- Git
- GitHub

### Reason

Maintain version history, collaboration, and project backup.

---

# Architecture Decisions

## AI-First Architecture

### Decision

CareerPilotAI will follow an AI-first architecture.

### Explanation

Whenever practical, AI will be responsible for understanding user input instead of relying on manually written rules.

Examples include:

- Resume understanding
- Skill extraction
- Skill normalization
- Semantic search
- Resume feedback
- Interview generation
- Career guidance

---

## Modular Architecture

The project will follow a modular architecture where each feature is separated into independent modules.

Examples include:

- Authentication
- Resume Analysis
- Job Matching
- Course Recommendation
- Interview Generation
- Career Roadmap

This improves maintainability and scalability.

---

# AI Decisions

## No Hardcoded Alias Dictionary

### Decision

The project will not maintain manual mappings such as:

- JS → JavaScript
- Postgres → PostgreSQL
- Node → Node.js

### Reason

The AI model will normalize user input before searching the database.

This makes the system:

- More flexible
- Easier to maintain
- More intelligent
- Better at handling unknown variations

---

## Semantic Matching

### Decision

Semantic matching will be a core feature of CareerPilotAI.

### Explanation

Instead of matching exact words, the system will compare meanings.

Examples:

- JavaScript ≈ JS
- PostgreSQL ≈ Postgres
- Containerization ≈ Docker

This allows more accurate job and skill recommendations.

---

## Interview Question Generation

### Decision

Interview questions will be generated dynamically using AI.

### Reason

Static interview datasets were intentionally removed because AI-generated questions can be personalized based on:

- Resume
- Job description
- Existing skills
- Missing skills
- Experience level

---

## AI Responsibilities

The AI system will be responsible for:

- Resume parsing
- Skill extraction
- Skill normalization
- Resume analysis
- Semantic understanding
- Job matching explanations
- ATS feedback
- Course recommendation explanations
- Career guidance
- Interview question generation
- Career roadmap generation

---

# Backend Responsibilities

The backend will manage:

- User authentication
- Authorization
- Database operations
- CRUD APIs
- Resume storage
- Job retrieval
- Course retrieval
- ATS score calculation
- User history

The backend is responsible for system logic, while AI is responsible for reasoning and understanding.

---

# Dataset Decisions

The following datasets have been finalized for the project:

## 1. Job Postings Dataset

Purpose:

- Job recommendations
- Job search
- ATS comparison

---

## 2. Resume Dataset

Purpose:

- Resume parsing
- Resume analysis
- ATS matching

---

## 3. Skills Dataset

Purpose:

- Skill normalization
- Skill categorization
- Skill gap analysis

---

## 4. Online Courses Dataset

Purpose:

- Course recommendations
- Learning roadmap generation

---

## Removed Dataset

Interview Questions Dataset

### Reason

Interview questions will instead be generated dynamically by AI.

---

# Semantic Search Workflow

The planned semantic search pipeline is:

User Resume / Query

↓

AI Understanding

↓

Embedding Generation

↓

Vector Search

↓

Top Matching Jobs

↓

ATS Analysis

↓

AI Explanation

---

# Development Principles

The following rules should be followed throughout development.

## Architecture

- Maintain a modular project structure.
- Keep frontend and backend separated.
- Follow REST API principles.
- Keep database schema normalized.

---

## AI

- Prefer AI reasoning over manual rules whenever practical.
- Avoid unnecessary hardcoded mappings.
- Use semantic search wherever possible.
- Generate explanations using AI.

---

## Code Quality

- Write modular code.
- Avoid duplicate logic.
- Keep functions focused on a single responsibility.
- Use meaningful naming conventions.
- Keep the project scalable.

---

## Git

- Make frequent commits.
- Use descriptive commit messages.
- Keep the main branch stable.

---

# Future Enhancements

The following features are outside the current 10-day scope but may be implemented in future versions:

- Company recommendations
- Salary prediction
- Resume version comparison
- AI mock interviews
- Cover letter generation
- Recruiter dashboard
- Admin dashboard
- Multi-language support
- Email notifications
- Cloud deployment
- Analytics dashboard

---

# Project Goal

Build a production-style AI Career Platform using:

- React
- FastAPI
- PostgreSQL
- Ollama
- Semantic Search
- Local Large Language Models

The project should prioritize intelligent AI-assisted career guidance while maintaining a clean, scalable, and production-ready architecture.