import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import chat_app  # Imports logic from your RAG logic file

# -------------------------------------------------------------
# Initialize App
# -------------------------------------------------------------
app = FastAPI(
    title="Multi-RAG Chatbot API",
    description="API for chatting with PDF documents (Text, Tables, Images, Formulas)",
    version="1.0"
)

# -------------------------------------------------------------
# Serve static files (CSS, JS if you add later)
# -------------------------------------------------------------
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------------------------------------------
# Request / Response Models
# -------------------------------------------------------------
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []

# -------------------------------------------------------------
# 1️⃣ Serve the UI (index.html)
# -------------------------------------------------------------
@app.get("/")
def serve_ui():
    return FileResponse("index.html")

# -------------------------------------------------------------
# 2️⃣ Chat API Endpoint
# -------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint for user queries → RAG → LLM response.
    """
    try:
        # 1. Embed query
        query_vector = chat_app.get_embedding(request.query)

        # 2. Retrieve relevant context
        contexts = chat_app.retrieve_context(query_vector)

        if not contexts:
            return ChatResponse(
                answer="I couldn't find relevant information in the document.",
                sources=[]
            )

        # 3. Generate Answer
        answer = chat_app.generate_answer(request.query, contexts)

        return ChatResponse(
            answer=answer,
            sources=contexts
        )

    except Exception as e:
        print("Chat Error:", e)
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------
# 3️⃣ NEW CHAT — Reset Memory (Sidebar Button)
# -------------------------------------------------------------
@app.post("/reset-chat")
async def reset_chat():
    """
    Clears all stored conversation memory for a fresh new chat.
    """
    try:
        chat_app.reset_chat()
        return {"status": "success", "message": "Chat memory cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------
# Run Server
# -------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Server Running...")
    print("👉 Open UI at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
