import os
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .ingest import ingest_document, prepare_upload_directory
from .rag import generate_answer

app = FastAPI(title="Memora AI API")

# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str
    upload_id: Optional[str] = None

ALLOWED_EXTENSIONS = {".docx", ".pdf", ".txt"}
UPLOAD_ROOT = Path("data/uploads")

@app.get("/")
def root():
    return {"message": "Memora AI API is running"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    filename = Path(file.filename).name
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. Supported types are: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
        )
    upload_root = Path(prepare_upload_directory())
    upload_id = uuid4().hex
    upload_dir = upload_root / upload_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / filename
    try:
        contents = await file.read()
        saved_path.write_bytes(contents)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {exc}")
    try:
        result = ingest_document(str(saved_path), str(upload_dir))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process uploaded file: {exc}")
    return JSONResponse(
        status_code=201,
        content={
            "message": "File uploaded and indexed successfully.",
            "upload_id": upload_id,
            "filename": filename,
            "chunks_count": result["chunks_count"],
        },
    )

@app.post("/ask")
def ask_question(request: QuestionRequest):
    upload_id = request.upload_id.strip() if request.upload_id else None
    if upload_id:
        upload_dir = UPLOAD_ROOT / upload_id
        if not upload_dir.exists() or not upload_dir.is_dir():
            raise HTTPException(
                status_code=400,
                detail=f"Upload directory not found for upload_id '{upload_id}'.",
            )
        if not (upload_dir / "faiss.index").exists() or not (upload_dir / "chunks.pkl").exists():
            raise HTTPException(
                status_code=400,
                detail=f"Index or chunks file missing for upload_id '{upload_id}'.",
            )

    answer, sources = generate_answer(request.question, upload_id=upload_id)
    return {"answer": answer, "sources": sources}
