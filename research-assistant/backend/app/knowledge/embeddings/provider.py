from __future__ import annotations

from typing import Type

from app.knowledge.embeddings.base import (
    BaseEmbeddingProvider,
    EmbeddingConfig,
)


class EmbeddingProvider:
    """
    Provider registry and factory.

    The application should use this class to obtain embedding
    providers rather than directly constructing provider instances.
    """

    def __init__(self) -> None:
        self._providers: dict[
            str,
            Type[BaseEmbeddingProvider],
        ] = {}

        self._instances: dict[
            str,
            BaseEmbeddingProvider,
        ] = {}

    def register(
        self,
        name: str,
        provider_class: Type[BaseEmbeddingProvider],
    ) -> None:
        """
        Register an embedding provider class.
        """

        normalized_name = name.strip().lower()

        if not normalized_name:
            raise ValueError(
                "Embedding provider name cannot be empty."
            )

        if not issubclass(
            provider_class,
            BaseEmbeddingProvider,
        ):
            raise TypeError(
                "Embedding provider must inherit from "
                "BaseEmbeddingProvider."
            )

        self._providers[normalized_name] = provider_class

    def create(
        self,
        name: str,
        config: EmbeddingConfig,
    ) -> BaseEmbeddingProvider:
        """
        Create or retrieve a provider instance.
        """

        normalized_name = name.strip().lower()

        provider_class = self._providers.get(
            normalized_name
        )

        if provider_class is None:
            available = ", ".join(
                sorted(self._providers.keys())
            )

            raise ValueError(
                f"Unknown embedding provider "
                f"'{normalized_name}'. "
                f"Available providers: "
                f"{available or 'none'}"
            )

        cache_key = (
            f"{normalized_name}:"
            f"{config.model}:"
            f"{config.dimensions}:"
            f"{config.normalize}"
        )

        if cache_key not in self._instances:
            self._instances[cache_key] = provider_class(
                config
            )

        return self._instances[cache_key]

    def register_instance(
        self,
        name: str,
        provider: BaseEmbeddingProvider,
    ) -> None:
        """
        Register an already-created provider instance.

        Useful for dependency injection and testing.
        """

        normalized_name = name.strip().lower()

        if not isinstance(
            provider,
            BaseEmbeddingProvider,
        ):
            raise TypeError(
                "provider must inherit from "
                "BaseEmbeddingProvider."
            )

        self._instances[
            f"instance:{normalized_name}"
        ] = provider

        self._providers.setdefault(
            normalized_name,
            provider.__class__,
        )

    def get_instance(
        self,
        name: str,
    ) -> BaseEmbeddingProvider:
        """
        Return a previously registered instance.
        """

        normalized_name = name.strip().lower()

        key = f"instance:{normalized_name}"

        provider = self._instances.get(key)

        if provider is None:
            raise ValueError(
                f"No embedding provider instance "
                f"registered for '{normalized_name}'."
            )

        return provider

    def available(self) -> list[str]:
        """
        Return registered provider names.
        """

        names = set(self._providers.keys())

        for key in self._instances:
            if key.startswith("instance:"):
                names.add(
                    key.removeprefix("instance:")
                )

        return sorted(names)

    def has(self, name: str) -> bool:
        """
        Check whether a provider exists.
        """

        normalized_name = name.strip().lower()

        return normalized_name in self._providers

    def remove(self, name: str) -> None:
        """
        Remove a provider registration.
        """

        normalized_name = name.strip().lower()

        self._providers.pop(
            normalized_name,
            None,
        )

        instance_key = (
            f"instance:{normalized_name}"
        )

        self._instances.pop(
            instance_key,
            None,
        )