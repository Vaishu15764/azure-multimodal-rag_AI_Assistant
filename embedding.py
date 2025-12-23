import time
from sentence_transformers import SentenceTransformer

print("[embedding] Loading local embedding model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print("[embedding] Model loaded successfully!")


def generate_embeddings(chunks):
    """
    Generates embeddings for text chunks using local HuggingFace embeddings
    (No API call required, fully free, no quota issues)
    """
    if not chunks:
        print("[embedding] No chunks to embed.")
        return []

    embeddings = []
    batch_size = 10

    print(f"[embedding] Generating embeddings for {len(chunks)} chunks...")

    try:
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            # Generate embeddings locally
            batch_embeddings = model.encode(batch)

            # Convert from NumPy to Python list
            for vector in batch_embeddings:
                embeddings.append(vector.tolist())

            time.sleep(0.2)  # safe

        print(f"[embedding] Successfully generated {len(embeddings)} vectors.")
        return embeddings

    except Exception as e:
        print(f"[embedding] Error generating embeddings: {e}")
        return []
