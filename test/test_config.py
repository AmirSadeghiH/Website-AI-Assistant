import os
from dotenv import load_dotenv

load_dotenv()

print("OPENAI_API_KEY:", "SET" if os.getenv("OPENAI_API_KEY") else "NOT SET")
print("EMBEDDING_API_KEY:", "SET" if os.getenv("EMBEDDING_API_KEY") else "NOT SET")
print("BASE_URL:", os.getenv("BASE_URL"))