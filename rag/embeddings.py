import logging
import os
from typing import List, Optional

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

# تنظیم encoding برای خروجی و ورودی
load_dotenv()

logger = logging.getLogger(__name__)


API_KEY = os.getenv('EMBEDDING_API_KEY')
DEFAULT_EMBEDDING_MODEL = (
    os.getenv('EMBEDDING_MODEL')
    or os.getenv('EMBED_MODEL')
    or 'text-embedding-3-small'
)
DEFAULT_EMBEDDING_BASE_URL = (
    os.getenv("EMBEDDING_API_URL")
    or os.getenv("EMBEDDING_BASE_URL")
    or os.getenv("BASE_URL")
    or "https://api.gapgpt.app/v1"
)


class Embedder:
    """Embedding client for queries and document chunks.

    ``embedder_type="api"`` (default) calls the configured OpenAI-compatible
    endpoint. Any other value loads a local SentenceTransformer model; the
    torch stack is imported lazily so serving workers that only use the API
    never pay the memory cost of loading torch / transformers.
    """

    def __init__(
        self,
        embedder_type: str = "api",
        model_name: str = "intfloat/multilingual-e5-small",
        device: str = "cpu",
        model_name_api: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self.embedder_type = embedder_type
        self.model_name = model_name
        self.model = None
        if self.embedder_type != 'api':
            # Lazy import keeps torch out of serving workers that only use
            # the hosted embedding API.
            from sentence_transformers import SentenceTransformer

            self.device = device
            self.model = SentenceTransformer(model_name, device=device)
            logger.info("[Embedder] Model loaded on %s", self.device)

        self.model_name_api = model_name_api or DEFAULT_EMBEDDING_MODEL
        # Client is created lazily on first use so an empty corpus (fresh
        # install with no keys configured yet) never needs a provider.
        self._client = None
        self._client_options = {
            "base_url": base_url or DEFAULT_EMBEDDING_BASE_URL,
            "api_key": api_key,
            "timeout": timeout if timeout is not None
            else float(os.getenv("EMBEDDING_TIMEOUT_SECONDS", "15")),
            "max_retries": max_retries if max_retries is not None
            else int(os.getenv("EMBEDDING_MAX_RETRIES", "0")),
        }

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI(**self._client_options)
        return self._client

    def embed_text(self, texts: List[str]) -> np.ndarray:
        """Embed a list of text chunks (local model or hosted API)."""
        if self.embedder_type == 'api':
            return self.embed_text_api(texts)
        if self.model is None:
            raise RuntimeError("Local embedding model is not available.")
        return self.model.encode(
            ["passage: " + t for t in texts],
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False,
        )

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string with the local model."""
        if self.model is None:
            raise RuntimeError("Local embedding model is not available.")
        return self.model.encode(
            ["query: " + query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]

    def embed_text_api(self, texts: List[str]) -> np.ndarray:
        prefixed_texts = [f"passage: {t}" for t in texts]

        response = self.client.embeddings.create(
            model=self.model_name_api,
            input=prefixed_texts,
        )

        # Extract embeddings from the response
        embeddings = [item.embedding for item in response.data]

        # Convert to numpy array
        return np.array(embeddings)

    def embed_query_api(self, query: str) -> np.ndarray:
        """Embed a single query string via the hosted API."""
        prefixed_query = f"query: {query}"

        try:
            response = self.client.embeddings.create(
                model=self.model_name_api,
                input=[prefixed_query],
            )
        except Exception as exc:
            logger.error(
                "[EMBEDDING ERROR] model=%r error=%r",
                self.model_name_api,
                exc,
            )
            raise

        embedding = response.data[0].embedding
        return np.array(embedding)
