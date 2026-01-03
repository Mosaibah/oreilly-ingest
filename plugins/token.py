"""
Token counting plugin supporting tiktoken for accurate LLM token counts.
"""

from .base import Plugin


class TokenPlugin(Plugin):
    """
    Count tokens for LLM context window planning.

    Uses tiktoken with cl100k_base encoding (GPT-4, GPT-3.5-turbo).

    Usage:
        token_plugin = kernel["token"]
        count = token_plugin.count_tokens("Hello world")
        estimate = token_plugin.estimate_tokens("Hello world")
    """

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
        """
        Count tokens accurately using tiktoken.

        Args:
            text: Text to tokenize
            model: Model name (currently uses cl100k_base for all)

        Returns:
            Exact token count
        """
        if not text:
            return 0
        return len(self.encoder.encode(text))

    def estimate_tokens(self, text: str) -> int:
        """
        Fast token estimation without tiktoken.

        Uses word count * 1.3 heuristic. Accurate within ~10% for English.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        if not text:
            return 0
        word_count = len(text.split())
        return int(word_count * self.TOKENS_PER_WORD)

    def count_or_estimate(self, text: str, model: str = "gpt-4") -> tuple[int, bool]:
        """
        Count tokens if tiktoken available, otherwise estimate.

        Args:
            text: Text to process
            model: Model for tiktoken encoding

        Returns:
            Tuple of (count, is_exact) where is_exact indicates tiktoken was used
        """
        try:
            return self.count_tokens(text, model), True
        except ImportError:
            return self.estimate_tokens(text), False
