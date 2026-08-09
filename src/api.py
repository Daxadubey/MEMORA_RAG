from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


@app.get("/")
def root():
    return {"message": "Memora AI API is running"}


# @app.post("/ask")
# def ask_question(request: QuestionRequest):

#     answer, results = generate_answer(request.question)

#     sources = []

#     for result in results:
#         sources.append({
#             "chunk": result["chunk"],
#             "score": result["score"]
#         })

#     return {
#         "answer": answer,
#         "sources": sources
#     }

@app.post("/ask")
def ask_question(request: QuestionRequest):

    answer, results = generate_answer(request.question)

    return {
        "answer": answer
    }