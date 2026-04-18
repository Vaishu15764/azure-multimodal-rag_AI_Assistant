from azure.storage.blob import BlobServiceClient
import os
import dotenv

dotenv.load_dotenv()

conn = os.getenv("connection_url") 
container_name = os.getenv("container_name")

client = BlobServiceClient.from_connection_string(conn)
container_client = client.get_container_client(container_name)

print("\n=== BLOBS IN YOUR CONTAINER ===\n")
for blob in container_client.list_blobs():
    print(blob.name) 