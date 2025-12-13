"""Late chunking embedder for improved context-aware embeddings.

Implements late chunking technique where the full document is encoded through
the transformer, then embeddings are extracted at chunk boundaries. This gives
each chunk access to bidirectional attention over the full document context.

Reference: https://jina.ai/news/late-chunking-in-long-context-embedding-models
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ChunkBoundary:
    """Defines a chunk's boundaries in the source text.

    Attributes:
        start: Start character offset in source text
        end: End character offset in source text
        content: The chunk text content
    """

    start: int
    end: int
    content: str


class LateChunkingEmbedder:
    """Embedder using late chunking for context-aware embeddings.

    Instead of encoding each chunk independently, this embedder:
    1. Encodes the full document through the transformer
    2. Maps chunk character boundaries to token boundaries
    3. Extracts embeddings by pooling over each chunk's token range

    This preserves full document context in each chunk's embedding.
    """

    # Default maximum tokens (can be overridden via config)
    DEFAULT_MAX_CONTEXT_TOKENS = 8192

    # Models known to support long contexts
    LONG_CONTEXT_MODELS = {
        "jinaai/jina-embeddings-v2-base-en": 8192,
        "jinaai/jina-embeddings-v2-small-en": 8192,
        "nomic-ai/nomic-embed-text-v1.5": 8192,
        "BAAI/bge-m3": 8192,
    }

    def __init__(
        self,
        model_name: str = "jinaai/jina-embeddings-v2-small-en",
        device: str | None = None,
        trust_remote_code: bool = True,
        max_context_tokens: int | None = None,
    ) -> None:
        """Initialise late chunking embedder.

        Args:
            model_name: Hugging Face model name (should support long contexts)
            device: Device to use (cuda, mps, cpu, or None for auto)
            trust_remote_code: Whether to trust remote code for models
            max_context_tokens: Maximum tokens to process (from config)
        """
        self._model_name = model_name
        self._device = device
        self._trust_remote_code = trust_remote_code
        self._max_context_tokens = max_context_tokens or self.DEFAULT_MAX_CONTEXT_TOKENS
        self._model: Any = None
        self._tokenizer: Any = None

    def _ensure_model(self) -> None:
        """Lazy load the model and tokenizer."""
        if self._model is not None:
            return

        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(
                self._model_name,
                trust_remote_code=self._trust_remote_code,
            )

            self._model = AutoModel.from_pretrained(
                self._model_name,
                trust_remote_code=self._trust_remote_code,
            )

            # Move to device
            if self._device:
                self._model = self._model.to(self._device)
            elif torch.cuda.is_available():
                self._model = self._model.to("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self._model = self._model.to("mps")

            self._model.eval()

        except ImportError as e:
            raise ImportError(
                "Late chunking requires transformers and torch. "
                "Install with: pip install transformers torch"
            ) from e

    def _char_to_token_boundaries(
        self,
        text: str,
        chunks: list[ChunkBoundary],
    ) -> list[tuple[int, int]]:
        """Map chunk character boundaries to token boundaries.

        Args:
            text: Full document text
            chunks: List of chunk boundaries

        Returns:
            List of (start_token, end_token) tuples for each chunk
        """
        self._ensure_model()

        # Tokenise with offset mapping
        encoding = self._tokenizer(
            text,
            return_tensors="pt",
            return_offsets_mapping=True,
            truncation=True,
            max_length=self._max_context_tokens,
        )

        offset_mapping = encoding["offset_mapping"][0].tolist()
        token_boundaries = []

        for chunk in chunks:
            # Find first token that overlaps with chunk start
            start_token = None
            end_token = None

            for i, (tok_start, tok_end) in enumerate(offset_mapping):
                # Skip special tokens (offset 0,0)
                if tok_start == tok_end == 0:
                    continue

                # Found start token
                if start_token is None and tok_end > chunk.start:
                    start_token = i

                # Found end token
                if tok_start < chunk.end:
                    end_token = i + 1

            # Default to full sequence if boundaries not found
            if start_token is None:
                start_token = 0
            if end_token is None:
                end_token = len(offset_mapping)

            token_boundaries.append((start_token, end_token))

        return token_boundaries

    def embed_document_chunks(
        self,
        full_text: str,
        chunks: list[ChunkBoundary],
    ) -> list[list[float]]:
        """Generate embeddings for chunks using late chunking.

        Encodes the full document once, then extracts embeddings for each chunk
        by pooling over the chunk's token range.

        Args:
            full_text: The complete document text
            chunks: List of chunk boundaries defining where to extract embeddings

        Returns:
            List of embedding vectors, one per chunk
        """
        if not chunks:
            return []

        import torch

        self._ensure_model()

        # Get token boundaries for each chunk
        token_boundaries = self._char_to_token_boundaries(full_text, chunks)

        # Encode full document
        inputs = self._tokenizer(
            full_text,
            return_tensors="pt",
            truncation=True,
            max_length=self._max_context_tokens,
            padding=True,
        )

        # Move to same device as model
        device = next(self._model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Get hidden states from model
        with torch.no_grad():
            outputs = self._model(**inputs)

        # Extract last hidden state [batch, seq_len, hidden_dim]
        hidden_states = outputs.last_hidden_state[0]  # Remove batch dimension

        # Extract embeddings for each chunk by mean pooling
        embeddings = []
        for start_token, end_token in token_boundaries:
            # Ensure valid boundaries
            start_token = max(0, min(start_token, hidden_states.shape[0] - 1))
            end_token = max(start_token + 1, min(end_token, hidden_states.shape[0]))

            # Mean pool over chunk tokens
            chunk_embedding = hidden_states[start_token:end_token].mean(dim=0)

            # Normalise
            chunk_embedding = torch.nn.functional.normalize(chunk_embedding, dim=0)

            embeddings.append(chunk_embedding.cpu().numpy().tolist())

        return embeddings

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for independent texts (fallback mode).

        When used without chunk boundaries, embeds each text independently.
        For best results, use embed_document_chunks instead.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        import torch

        self._ensure_model()

        embeddings = []
        for text in texts:
            inputs = self._tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=self._max_context_tokens,
                padding=True,
            )

            device = next(self._model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self._model(**inputs)

            # Mean pool over all tokens
            embedding = outputs.last_hidden_state[0].mean(dim=0)
            embedding = torch.nn.functional.normalize(embedding, dim=0)
            embeddings.append(embedding.cpu().numpy().tolist())

        return embeddings

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        self._ensure_model()
        return self._model.config.hidden_size

    @property
    def model_name(self) -> str:
        """Return model name."""
        return self._model_name

    def is_available(self) -> bool:
        """Check if late chunking is available (dependencies installed).

        Returns:
            True if transformers and torch are available
        """
        try:
            import torch
            import transformers

            return True
        except ImportError:
            return False


def check_late_chunking_available() -> tuple[bool, str]:
    """Check if late chunking dependencies are available.

    Returns:
        Tuple of (available: bool, message: str)
    """
    try:
        import torch
        import transformers

        return True, "Late chunking is available"
    except ImportError as e:
        missing = str(e).split("'")[1] if "'" in str(e) else "transformers/torch"
        return False, f"Missing dependency: {missing}. Install with: pip install transformers torch"


def create_late_chunking_embedder(
    model_name: str = "jinaai/jina-embeddings-v2-small-en",
    device: str | None = None,
) -> LateChunkingEmbedder | None:
    """Create a late chunking embedder if dependencies available.

    Args:
        model_name: Model to use (should support long contexts)
        device: Device to use

    Returns:
        LateChunkingEmbedder or None if dependencies missing
    """
    available, _ = check_late_chunking_available()
    if not available:
        return None

    return LateChunkingEmbedder(model_name=model_name, device=device)
