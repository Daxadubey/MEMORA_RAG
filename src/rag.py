import os
from dotenv import load_dotenv
from google import genai

from .retrieve import retrieve


# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")


# Initialize Gemini
client = genai.Client(api_key=api_key)


SYSTEM_PROMPT = """
You are a professional and polite document AI assistant.

Answer the user's question using ONLY the information provided
in the retrieved context.

Rules:
- Do NOT use outside knowledge.
- Do NOT invent or hallucinate information.
- Do NOT assume information that is not present in the context.
- If the retrieved context does not contain enough information
  to answer the question, say:
  "The answer is not available in the provided document."
- Keep the answer clear, concise, professional, and accurate.
"""


def generate_answer(question, top_k=3, upload_id=None):

    # Step 1: Retrieve relevant chunks
    results = retrieve(question, top_k=top_k, upload_id=upload_id)

    # Step 2: Prepare context
    context_parts = []

    for i, result in enumerate(results):
        context_parts.append(
            f"--- Retrieved Chunk {i + 1} ---\n"
            f"{result['chunk']}"
        )

    context = "\n\n".join(context_parts)

    # Step 3: Create prompt
    prompt = f"""
{SYSTEM_PROMPT}

## Retrieved Context

{context}

## User Question

{question}

## Answer
"""

    # Step 4: Send context + question to Gemini
    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt
    )

    sources = [
        {
            "chunk": result["chunk"],
            "similarity": result["score"],
        }
        for result in results
    ]

    return response.text, sources


# Chat loop
if __name__ == "__main__":
    while True:
        question = input("\nAsk a question (or type 'exit'): ")

        if question.lower() == "exit":
            break

        answer, sources = generate_answer(question)

        print("\n===== ANSWER =====")
        print(answer)

        print("\n===== SOURCES USED =====")

        for i, source in enumerate(sources):
            print(
                f"Chunk {i + 1} | "
                f"Similarity: {source['similarity']:.4f}"
            )