from deepeval.test_case import LLMTestCase


def create_llm_test_case(
    input_text: str,
    actual_output: str,
    retrieval_context: list[str],
    expected_output: str | None = None,
):
    """
    Creates a DeepEval LLM test case.

    Used for evaluating RAG responses.
    """

    test_case = LLMTestCase(
        input=input_text,

        # LLM generated answer
        actual_output=actual_output,

        # Documents/chunks retrieved by RAG
        retrieval_context=retrieval_context,

        # Optional ground truth answer
        expected_output=expected_output,
    )

    return test_case