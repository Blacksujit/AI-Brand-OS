from __future__ import annotations

from pathlib import Path

from core.config import Settings
from core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.embedding_model
        self._device = settings.embedding_device
        self._model = None
        self._cache_dir = settings.data_dir / "model_cache"

    def _load_model(self):
        if self._model is not None:
            return self._model
        from sentence_transformers import SentenceTransformer

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "loading_embedding_model",
            model=self._model_name,
            device=self._device,
        )
        self._model = SentenceTransformer(
            self._model_name,
            device=self._device,
            cache_folder=str(self._cache_dir),
        )
        return self._model

    async def embed_text(self, text: str) -> list[float]:
        model = self._load_model()
        embeddings = model.encode([text], normalize_embeddings=True)
        return embeddings[0].tolist()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        model = self._load_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return [emb.tolist() for emb in embeddings]

    async def cosine_similarity(
        self, a: list[float], b: list[float]
    ) -> float:
        import math

        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @property
    def dimension(self) -> int:
        model = self._load_model()
        return model.get_sentence_embedding_dimension()
