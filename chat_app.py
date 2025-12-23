import os
import dotenv
from groq import Groq
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Load environment variables
dotenv.load_dotenv()

# --- Configuration ---
PINECONE_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Initialize Groq ---
client = Groq(api_key=GROQ_API_KEY)

# --- Initialize Pinecone ---
pc = Pinecone(api_key=PINECONE_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# --- Local Embedding Model ---
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# ------------------------------
# MEMORY SUPPORT (NEW FEATURE)
# ------------------------------
conversation_memory = []   # stores previous Q/A pairs


def reset_chat():
    """Clear chat history memory."""
    global conversation_memory
    conversation_memory = []
    return True


# ----------------------------------------------------------
# 1️⃣ EMBEDDING FUNCTION
# ----------------------------------------------------------
def get_embedding(text):
    embedding = model.encode([text])[0]
    return embedding.tolist()


# ----------------------------------------------------------
# 2️⃣ RETRIEVE CONTEXT FROM PINECONE
# ----------------------------------------------------------
def retrieve_context(query_vector, top_k=5):
    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )

    contexts = []
    for match in results['matches']:
        if 'text' in match['metadata']:
            contexts.append(match['metadata']['text'])

    return contexts


# ----------------------------------------------------------
# 3️⃣ GENERATE ANSWER USING GROQ (LLAMA-3.3-70B)
# ----------------------------------------------------------
def generate_answer(query, context_list):
    global conversation_memory

    context_text = "\n\n---\n\n".join(context_list)

    # Build RAG prompt including memory
    memory_text = ""
    if conversation_memory:
        memory_text = "\n\nPrevious conversation:\n"
        for q, a in conversation_memory:
            memory_text += f"User: {q}\nAssistant: {a}\n"

    prompt = f"""
You are a helpful RAG AI Assistant.
Use only the provided document context to answer.
If the information is missing, say:
"I don't know based on provided document."

{memory_text}

Context:
{context_text}

Question:
{query}

Answer:
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content

    # Save to memory
    conversation_memory.append((query, answer))

    return answer


# ----------------------------------------------------------
# 4️⃣ EXPOSE A FUNCTION TO FASTAPI
# ----------------------------------------------------------
def process_query(query):
    """Main function called by FastAPI."""
    query_vector = get_embedding(query)
    contexts = retrieve_context(query_vector)

    if not contexts:
        return {"answer": "No relevant information found in the document.", "sources": []}

    answer = generate_answer(query, contexts)

    # Return document sources (you can modify to include metadata)
    return {
        "answer": answer,
        "sources": contexts  # simple version — uses text chunks as sources
    }


# ----------------------------------------------------------
# 5️⃣ COMMAND LINE CHAT (OPTIONAL)
# ----------------------------------------------------------
def start_chat():
    print("=== Document Chatbot via Groq (Type 'exit' to quit) ===")

    while True:
        query = input("\nUser: ")
        if query.lower() in ["exit", "quit"]:
            break

        try:
            result = process_query(query)
            print(f"\nBot: {result['answer']}")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    start_chat()
