from __future__ import annotations

from enum import Enum


class PromptTemplateType(str, Enum):
    """
    Supported prompt templates.
    """

    QA = "qa"
    RAG = "rag"
    CHAT = "chat"
    SUMMARIZATION = "summarization"


# ============================================================
# Question Answering
# ============================================================

QA_TEMPLATE = """
Question

{question}

Answer
""".strip()


# ============================================================
# Retrieval-Augmented Generation
# ============================================================

RAG_TEMPLATE = """
Context

{context}

Question

{question}

Answer
""".strip()


# ============================================================
# Multi-turn Chat
# ============================================================

CHAT_TEMPLATE = """
Conversation History

{history}

Current User Question

{question}

Assistant Response
""".strip()


# ============================================================
# Document Summarization
# ============================================================

SUMMARIZATION_TEMPLATE = """
Document

{document}

Write a concise and accurate summary.
""".strip()


# ============================================================
# Template Registry
# ============================================================

PROMPT_TEMPLATES = {
    PromptTemplateType.QA: QA_TEMPLATE,
    PromptTemplateType.RAG: RAG_TEMPLATE,
    PromptTemplateType.CHAT: CHAT_TEMPLATE,
    PromptTemplateType.SUMMARIZATION: SUMMARIZATION_TEMPLATE,
}


def get_prompt_template(
    template_type: PromptTemplateType,
) -> str:
    """
    Return a prompt template.
    """

    return PROMPT_TEMPLATES[template_type]