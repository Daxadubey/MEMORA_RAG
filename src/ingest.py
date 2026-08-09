import pickle
from pathlib import Path
from uuid import uuid4

from docx import Document
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME)
SUPPORTED_EXTENSIONS = {".docx", ".pdf", ".txt"}


def extract_text_from_docx(file_path: str) -> str:
    document = Document(file_path)
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs)


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()


def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def create_chunks(text: str, chunk_size=1000, overlap=150) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current_chunk = ""
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 1 <= chunk_size:
            current_chunk += paragraph + "\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n"
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks


def build_faiss_index(chunks: list[str]) -> faiss.IndexFlatIP:
    embeddings = EMBEDDING_MODEL.encode(chunks, convert_to_numpy=True)
    embeddings = np.asarray(embeddings, dtype="float32")
    faiss.normalize_L2(embeddings)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    return index


def save_index_and_chunks(index: faiss.IndexFlatIP, chunks: list[str], output_dir: str) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(output_path / "faiss.index"))
    with open(output_path / "chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)


def ingest_document(file_path: str, output_dir: str) -> dict:
    extension = Path(file_path).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension '{extension}'. Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )
    if extension == ".docx":
        text = extract_text_from_docx(file_path)
    elif extension == ".pdf":
        text = extract_text_from_pdf(file_path)
    else:
        text = extract_text_from_txt(file_path)
    if not text.strip():
        raise ValueError("Uploaded file does not contain any extractable text.")
    chunks = create_chunks(text)
    if not chunks:
        raise ValueError("Unable to create document chunks from uploaded file.")
    index = build_faiss_index(chunks)
    save_index_and_chunks(index, chunks, output_dir)
    return {
        "index_path": str(Path(output_dir) / "faiss.index"),
        "chunks_path": str(Path(output_dir) / "chunks.pkl"),
        "chunks_count": len(chunks),
    }


def prepare_upload_directory(base_path: str = "data/uploads") -> str:
    upload_dir = Path(base_path)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return str(upload_dir)
