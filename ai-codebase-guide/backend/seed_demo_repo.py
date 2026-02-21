import chromadb
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

# Use same path as main.py
client = chromadb.PersistentClient(path="./chroma_db")

repo_id = "demo_repo"
collection_name = f"repo_{repo_id}"
collection = client.get_or_create_collection(name=collection_name)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

text = "Authentication is handled in auth/service.py using verify_credentials."

embedding = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=text
).data[0].embedding

collection.add(
    documents=[text],
    embeddings=[embedding],
    metadatas=[{
        "file_path": "auth/service.py",
        "start_line": 1,
        "end_line": 5,
        "chunk_id": "chunk_001"
    }],
    ids=["chunk_001"]
)

print("Demo repo seeded successfully.")