import time
from typing import Dict, Any
from datetime import datetime, timezone

class MetricsRegistry:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MetricsRegistry, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_metrics()
        return cls._instance

    def _init_metrics(self):
        self.boot_time = time.time()
        self.request_count = 0
        self.request_latency_sum = 0.0
        self.status_codes: Dict[int, int] = {}
        
        # Track counts of different RAG query modes (in-memory since startup)
        self.retrieval_count = 0
        self.graph_retrieval_count = 0
        self.verification_count = 0
        self.deep_research_count = 0

    def increment_request(self, latency_ms: float, status_code: int):
        self.request_count += 1
        self.request_latency_sum += latency_ms
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1

    def increment_rag_metric(self, retrieval: bool = False, graph: bool = False, verification: bool = False, deep_research: bool = False):
        if retrieval:
            self.retrieval_count += 1
        if graph:
            self.graph_retrieval_count += 1
        if verification:
            self.verification_count += 1
        if deep_research:
            self.deep_research_count += 1

    def get_uptime_seconds(self) -> float:
        return time.time() - self.boot_time

    def get_metrics_summary(self) -> Dict[str, Any]:
        avg_latency = (self.request_latency_sum / self.request_count) if self.request_count > 0 else 0.0
        return {
            "uptime_seconds": self.get_uptime_seconds(),
            "request_count": self.request_count,
            "average_latency_ms": round(avg_latency, 2),
            "status_codes": self.status_codes,
            "retrieval_count": self.retrieval_count,
            "graph_retrieval_count": self.graph_retrieval_count,
            "verification_count": self.verification_count,
            "deep_research_count": self.deep_research_count
        }

metrics_registry = MetricsRegistry()
