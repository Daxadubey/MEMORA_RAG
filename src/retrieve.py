import faiss
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer


# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

DEFAULT_INDEX_PATH = Path("data/faiss.index")
DEFAULT_CHUNKS_PATH = Path("data/chunks.pkl")
UPLOAD_ROOT = Path("data/uploads")


def load_index_and_chunks(upload_id=None):
    if upload_id:
        upload_dir = UPLOAD_ROOT / upload_id
        index_path = upload_dir / "faiss.index"
        chunks_path = upload_dir / "chunks.pkl"
    else:
        index_path = DEFAULT_INDEX_PATH
        chunks_path = DEFAULT_CHUNKS_PATH

    if not index_path.exists() or not chunks_path.exists():
        raise FileNotFoundError(
            f"Index or chunks file not found for upload_id '{upload_id}'."
            if upload_id else "Default FAISS index or chunks file not found."
        )

    index = faiss.read_index(str(index_path))
    with open(chunks_path, "rb") as f:
        chunks = pickle.load(f)

    return index, chunks


def retrieve(query, top_k=3, upload_id=None):

    index, chunks = load_index_and_chunks(upload_id)

    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True
    ).astype("float32")

    faiss.normalize_L2(query_embedding)

    scores, indices = index.search(query_embedding, top_k)

    results = []

    for score, idx in zip(scores[0], indices[0]):
        results.append({
            "chunk": chunks[idx],
            "score": float(score)
        })

    return results


# Test retrieval
if __name__ == "__main__":
    query = input("Ask a question: ")

    results = retrieve(query)

    print("\n===== RETRIEVED CHUNKS =====")

    for i, result in enumerate(results):
        print(f"\nResult {i + 1}")
        print(f"Similarity Score: {result['score']:.4f}")
        print("-" * 60)
        print(result["chunk"])