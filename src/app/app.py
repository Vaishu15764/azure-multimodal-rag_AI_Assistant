from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import os

from src.app import chat_app


# Initialize App
app = FastAPI(
    title="Multi-RAG Chatbot API",
    description="API for chatting with PDF documents (Text, Tables, Images, Formulas)",
    version="1.0"
)


# Static folder setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(os.path.dirname(BASE_DIR), "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Request/Response Models
class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []


# Greeting detector
def is_greeting(text: str) -> bool:
    greetings = ["hi", "hello", "hey", "hii", "hola"]
    return text.lower().strip() in greetings


# Serve UI
@app.get("/")
def serve_ui():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# Chat Endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):

    try:
        user_query = request.query.strip()

        # Handle greetings separately
        if is_greeting(user_query):
            return ChatResponse(
                answer="Hi 👋 How can I help you?",
                sources=[]
            )

        # Generate embedding
        query_vector = chat_app.get_embedding(user_query)

        # Retrieve context from Pinecone
        contexts = chat_app.retrieve_context(query_vector)

        if not contexts:
            return ChatResponse(
                answer="I couldn't find relevant information in the document.",
                sources=[]
            )

        # Generate answer using LLM
        answer = chat_app.generate_answer(user_query, contexts)

        return ChatResponse(
            answer=answer,
            sources=contexts
        )

    except Exception as e:
        print("Chat Error:", e)
        raise HTTPException(status_code=500, detail=str(e))


# Run Server
if __name__ == "__main__":
    print("🚀 Server Running...")
    print("👉 Open UI at: http://localhost:8000")

    uvicorn.run(
        "src.app.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )