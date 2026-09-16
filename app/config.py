from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    MODEL = os.getenv("MODEL", "gemini-2.5-flash")

    # Separate model for embeddings - it is a different model family,
    # not a chat model.
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")


settings = Settings()