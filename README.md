# AI-Powered Document Intake & Extraction Microservice

This microservice accepts exam / student PDFs and images, runs OCR to extract text,
parses key fields using regex, and stores the results in MongoDB.

## Tech Stack

- Python 3.11+
- FastAPI (async)
- MongoDB + Motor (async driver)
- Tesseract OCR via `pytesseract`
- `pdf2image` + `poppler` for PDF → image conversion
- Pydantic models for structured JSON responses

## Features

- `POST /upload`
  - Accepts `multipart/form-data` with a `file` field.
  - Supports PDF and common image formats.
  - Runs OCR asynchronously (via `asyncio.to_thread`).
  - Parses:
    - Name
    - Exam name
    - Roll number
    - Total / maximum marks
    - Question number, question text, and marks per question (when present)
  - Stores raw text + parsed fields in MongoDB.
  - Returns MongoDB `doc_id`.

- `GET /results/{doc_id}`
  - Fetches processed document by ID.
  - Returns raw OCR text and parsed fields as JSON.

## Running Locally

1. Install system dependencies:

   ```bash
   sudo apt-get update
   sudo apt-get install -y tesseract-ocr poppler-utils
