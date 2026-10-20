import os
from dotenv import load_dotenv 

# Load environment variables from .env
load_dotenv()

def get_env(key: str) -> str:
    result = os.getenv(key)
    if result is None:
        raise ValueError(f"Environment variable {key} not set")
    return result
