import os
from pathlib import Path
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

ALLOWED_EXTENSIONS = {".docx", ".pdf", ".txt"}

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
            "index_path": str(upload_dir / "faiss.index"),
            "chunks_path": str(upload_dir / "chunks.pkl"),
        },
    )

@app.post("/ask")
def ask_question(request: QuestionRequest):
    answer, results = generate_answer(request.question)
    return {"answer": answer}
