"""
Token counting plugin supporting tiktoken for accurate LLM token counts.
"""

from .base import Plugin


class TokenPlugin(Plugin):
    """Count tokens for LLM context window planning using tiktoken."""

    _encoder = None

    TOKENS_PER_WORD = 1.3

    @property
    def encoder(self):
        """Lazy-load tiktoken encoder."""
        if TokenPlugin._encoder is None:
            import tiktoken

            TokenPlugin._encoder = tiktoken.get_encoding("cl100k_base")
        return TokenPlugin._encoder

    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens accurately using tiktoken."""
        if not text:
            return 0
        return len(self.encoder.encode(text))

    def estimate_tokens(self, text: str) -> int:
        """Fast token estimation using word count heuristic (~1.3x)."""
        if not text:
            return 0
        word_count = len(text.split())
        return int(word_count * self.TOKENS_PER_WORD)

    def count_or_estimate(self, text: str, model: str = "gpt-4") -> tuple[int, bool]:
        """Count tokens if tiktoken available, otherwise estimate."""
        try:
            return self.count_tokens(text, model), True
        except ImportError:
            return self.estimate_tokens(text), False
