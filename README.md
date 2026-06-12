# Financial Transactions Analyzer

## Overview
Backend service that processes uploaded transaction CSV files, detects anomalies, categorizes merchants, and generates spending summaries.

## Tech Stack
- FastAPI
- PostgreSQL
- Redis
- Celery
- Docker
- Pandas
- Gemini API

## Setup

### Clone Repository
git clone <repo-url>

### Start Services
docker compose up --build

## Environment Variables

DATABASE_URL=
REDIS_URL=
GEMINI_API_KEY=

## API Endpoints

POST /jobs/upload
GET /jobs/{job_id}/status
GET /jobs/{job_id}/results
GET /jobs

## Running Tests

pytest

## Architecture

CSV Upload
    ↓
FastAPI
    ↓
Celery + Redis
    ↓
Data Processing
    ↓
PostgreSQL

## Assumptions

- Missing categories are filled automatically.
- Gemini is optional.
- Fallback category is "Other".
