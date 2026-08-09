from docx import Document
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle

def extract_text(file_path):
    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def create_chunks(text, chunk_size=1000, overlap=150):
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:

        # If adding the paragraph stays within the chunk size
        if len(current_chunk) + len(paragraph) + 1 <= chunk_size:
            current_chunk += paragraph + "\n"

        else:
            # Save current chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            # Start a new chunk
            current_chunk = paragraph + "\n"

    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

file_path = "data/MEMORA_AI_SRS.docx"

text = extract_text(file_path)

chunks = create_chunks(text)

# Load the embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Convert chunks into embeddings
embeddings = embedding_model.encode(
    chunks,
    convert_to_numpy=True
)

print("Embedding shape:", embeddings.shape)

# Normalize embeddings for cosine similarity
faiss.normalize_L2(embeddings)

# Create FAISS index
dimension = embeddings.shape[1]

index = faiss.IndexFlatIP(dimension)

# Add embeddings to FAISS
index.add(embeddings)

print("Total vectors in FAISS:", index.ntotal)

# Save FAISS index
faiss.write_index(index, "data/faiss.index")

# Save chunks separately
with open("data/chunks.pkl", "wb") as f:
    pickle.dump(chunks, f)

print("FAISS index and chunks saved successfully.")
print(f"Total characters: {len(text)}")
print(f"Total chunks: {len(chunks)}")

def search(query, top_k=3):

    # Convert user question into embedding
    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True
    ).astype("float32")

    # Normalize query vector
    faiss.normalize_L2(query_embedding)

    # Search FAISS
    distances, indices = index.search(query_embedding, top_k)

    # Display results
    print("\nUser Query:")
    print(query)

    print("\nRetrieved Chunks:")

    for rank, idx in enumerate(indices[0]):
        print(f"\n--- Result {rank + 1} ---")
        print(f"Similarity Score: {distances[0][rank]}")
        print(chunks[idx])

search("What is the main objective of Memora AI?")

# for i, chunk in enumerate(chunks):
#     print("\n" + "=" * 60)
#     print(f"CHUNK {i + 1}")
#     print("=" * 60)
#     print(chunk)