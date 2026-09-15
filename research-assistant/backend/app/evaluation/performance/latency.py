from __future__ import annotations

import time
from typing import Callable, Any, Dict


def measure_latency(
    function: Callable,
    *args,
    **kwargs,
) -> Dict[str, Any]:
    """
    Measure execution latency of a function.

    Returns:
        result:
            Function output

        latency_ms:
            Execution time in milliseconds
    """

    start_time = time.perf_counter()


    result = function(
        *args,
        **kwargs
    )


    end_time = time.perf_counter()


    latency_ms = (
        end_time - start_time
    ) * 1000


    return {
        "result": result,
        "latency_ms": latency_ms,
    }



class LatencyTracker:
    """
    Tracks latency of different
    RAG pipeline stages.
    """

    def __init__(self):

        self.metrics = {
            "retrieval_latency_ms": 0.0,
            "reranking_latency_ms": 0.0,
            "generation_latency_ms": 0.0,
            "total_latency_ms": 0.0,
        }


    def start(self):
        """
        Start total pipeline timer.
        """

        self.start_time = (
            time.perf_counter()
        )


    def stop(self):
        """
        Stop total pipeline timer.
        """

        end_time = (
            time.perf_counter()
        )

        self.metrics[
            "total_latency_ms"
        ] = (
            end_time
            -
            self.start_time
        ) * 1000


    def record(
        self,
        name: str,
        latency_ms: float,
    ):
        """
        Record stage latency.
        """

        self.metrics[name] = latency_ms


    def get_metrics(self):
        """
        Return latency report.
        """

        return self.metric