import faiss
import pickle
from sentence_transformers import SentenceTransformer


# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Load FAISS index
index = faiss.read_index("data/faiss.index")

# Load original chunks
with open("data/chunks.pkl", "rb") as f:
    chunks = pickle.load(f)


def retrieve(query, top_k=3):

    # Convert user question into embedding
    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True
    )

    # Normalize query vector
    faiss.normalize_L2(query_embedding)

    # Search FAISS
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