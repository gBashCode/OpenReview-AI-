"""Provider-Independent 1,536-Dimensional Embedding Service."""

from abc import ABC, abstractmethod
import hashlib
import math
import re
from typing import List, Optional
import httpx
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("openreview.indexing.embeddings")
settings = get_settings()

EMBEDDING_DIM = 1536


class BaseEmbeddingProvider(ABC):
    """Abstract interface for generating vector embeddings."""

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embeds a batch of code chunks or text documents."""
        pass

    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """Embeds a single search query."""
        pass


class DeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """High-performance, deterministic 1,536-dimensional vector generator.
    
    Uses n-gram token hashing, term-frequency weighting, and L2 normalization.
    Enables reliable semantic retrieval without requiring external third-party API keys.
    """

    def __init__(self, dimension: int = EMBEDDING_DIM):
        self.dimension = dimension

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]

    async def embed_query(self, query: str) -> List[float]:
        return self._generate_vector(query)

    def _generate_vector(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension
        if not text:
            return vector

        # Extract code tokens, identifier words, and symbols
        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*|[0-9]+|[\{\}\(\)\[\]\+\-\*\/=><]", text.lower())
        if not tokens:
            return vector

        # Word n-grams and unigrams
        features = list(tokens)
        for i in range(len(tokens) - 1):
            features.append(f"{tokens[i]}_{tokens[i+1]}")

        for term in features:
            h = hashlib.sha256(term.encode("utf-8")).digest()
            # Map hash to index in vector
            idx = int.from_bytes(h[:4], "big") % self.dimension
            sign = 1.0 if (h[4] % 2 == 0) else -1.0
            weight = 1.5 if len(term) > 3 else 1.0
            vector[idx] += sign * weight

        # L2 Normalization
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 1e-9:
            vector = [v / norm for v in vector]

        return vector


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI text-embedding-3-small provider."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        url = "https://api.openai.com/v1/embeddings"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"input": texts, "model": self.model}

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()["data"]
            return [item["embedding"] for item in data]

    async def embed_query(self, query: str) -> List[float]:
        results = await self.embed_texts([query])
        return results[0] if results else [0.0] * EMBEDDING_DIM


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Returns configured embedding provider or deterministic fallback."""
    openai_key = getattr(settings, "OPENAI_API_KEY", None)
    if openai_key:
        return OpenAIEmbeddingProvider(api_key=openai_key)
    return DeterministicEmbeddingProvider()
