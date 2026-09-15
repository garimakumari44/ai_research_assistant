"""
Tokenizer utilities.

Responsible for:
- Loading tokenizer models
- Token counting
- Encoding / decoding text
"""

from functools import lru_cache

import tiktoken

from app.core.logging import logger


class Tokenizer:
    """
    Wrapper around tiktoken tokenizer.
    """

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
    ):
        self.model_name = model_name

        self.encoding = self._load_tokenizer()

    def _load_tokenizer(self):
        """
        Load tokenizer encoding.
        """

        try:
            return tiktoken.encoding_for_model(
                self.model_name
            )

        except Exception:

            logger.warning(
                "Model tokenizer not found. Using cl100k_base"
            )

            return tiktoken.get_encoding(
                "cl100k_base"
            )


    def encode(
        self,
        text: str,
    ) -> list[int]:
        """
        Convert text into token ids.
        """

        if not text:
            return []

        return self.encoding.encode(
            text
        )


    def decode(
        self,
        tokens: list[int],
    ) -> str:
        """
        Convert tokens back into text.
        """

        if not tokens:
            return ""

        return self.encoding.decode(
            tokens
        )


    def count_tokens(
        self,
        text: str,
    ) -> int:
        """
        Count number of tokens.
        """

        return len(
            self.encode(text)
        )


    def truncate(
        self,
        text: str,
        max_tokens: int,
    ) -> str:
        """
        Trim text to token limit.
        """

        tokens = self.encode(text)

        if len(tokens) <= max_tokens:
            return text

        truncated = tokens[:max_tokens]

        return self.decode(
            truncated
        )


@lru_cache()
def get_tokenizer(
    model_name: str = "gpt-4o-mini",
) -> Tokenizer:
    """
    Singleton tokenizer instance.
    """

    return Tokenizer(
        model_name=model_name
    )