from __future__ import annotations


CITATION_INSTRUCTIONS = """
Citation Guidelines

You are provided with retrieved context consisting of one or more source
documents.

When generating your response:

1. Every factual claim supported by the retrieved context should include
   one or more citations.

2. Use citation numbers in square brackets.

Example:

Python generators produce values lazily. [1]

3. If multiple sources support the same statement, cite them together.

Example:

Transformers use self-attention. [2][4]

4. Never invent citations.

5. Never cite information that is not present in the supplied context.

6. If the retrieved context does not contain enough information,
   explicitly state that the available sources are insufficient.

7. Do not reference internal identifiers such as chunk IDs,
   embedding IDs, or vector database IDs.

8. Use citations only for factual statements.
   Opinions or reasoning do not require citations.

9. Keep citations immediately after the statement they support.

10. Do not create a References section unless explicitly requested.
""".strip()


def get_citation_instructions() -> str:
    """
    Return citation instructions for prompt construction.
    """

    return CITATION_INSTRUCTIONS