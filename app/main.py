from datetime import datetime
from typing import Literal

from bson import ObjectId
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorCollection

from .db import get_collection
from .ocr import ocr_file
from .parser import parse_text_to_fields
from .schemas import UploadResponse, DocumentInDB, ErrorResponse

app = FastAPI(
    title="AI-Powered Document Intake & Extraction Microservice",
    description=(
        "Accepts exam/student PDFs/images, runs OCR, parses key fields "
        "(Name, questions, marks, etc.) and stores them in MongoDB."
    ),
    version="1.0.0",
)

# (Optional) Allow all origins during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _detect_file_type(content_type: str) -> Literal["pdf", "image"]:
    if "pdf" in content_type.lower():
        return "pdf"
    if any(img in content_type.lower() for img in ["image", "png", "jpeg", "jpg", "tiff"]):
        return "image"
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported content type: {content_type}",
    )


@app.post(
    "/upload",
    response_model=UploadResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF or image.
    - Detect file type
    - Run OCR asynchronously
    - Parse key fields with regex
    - Store raw + parsed data in MongoDB
    """
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing content type on uploaded file.",
        )

    file_type = _detect_file_type(file.content_type)
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded.",
        )

    # 1. OCR
    try:
        raw_text = await ocr_file(file_bytes=file_bytes, file_type=file_type)
    except Exception as exc:  # noqa: BLE001 - broad for demo clarity
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR failed: {exc}",
        ) from exc

    # 2. Parse text → structured fields
    parsed_fields = parse_text_to_fields(raw_text)

    # 3. Insert into MongoDB
    collection: AsyncIOMotorCollection = get_collection()

    doc = {
        "filename": file.filename,
        "content_type": file.content_type,
        "created_at": datetime.utcnow(),
        "raw_text": raw_text,
        "parsed": parsed_fields.model_dump(),
    }

    result = await collection.insert_one(doc)
    return UploadResponse(doc_id=str(result.inserted_id))


@app.get(
    "/results/{doc_id}",
    response_model=DocumentInDB,
    responses={404: {"model": ErrorResponse}},
)
async def get_results(doc_id: str):
    """
    Fetch processed document (raw text + parsed fields)
    by MongoDB ObjectId.
    """
    try:
        oid = ObjectId(doc_id)
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format.",
        )

    collection: AsyncIOMotorCollection = get_collection()
    doc = await collection.find_one({"_id": oid})

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    # Convert ObjectId to string for Pydantic
    doc["_id"] = str(doc["_id"])
    return DocumentInDB(**doc)


@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse(
        {
            "message": "Document Intake & Extraction Microservice is up.",
            "endpoints": ["/upload", "/results/{doc_id}", "/docs"],
        }
    )
