"""Prometheus metrics and model cost tracking telemetry."""

import time
from collections import defaultdict
from typing import Dict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# In-memory metrics registry (compatible with standard Prometheus format)
class PrometheusMetricsRegistry:
    """Thread-safe Prometheus metrics registry for OpenReview AI."""

    def __init__(self):
        self.request_counts: Dict[str, int] = defaultdict(int)
        self.request_durations: Dict[str, list] = defaultdict(list)
        self.active_reviews: int = 0
        self.worker_tasks_total: Dict[str, int] = defaultdict(int)
        self.worker_failures_total: Dict[str, int] = defaultdict(int)
        self.llm_tokens_total: Dict[str, int] = defaultdict(int)
        self.llm_cost_usd_total: Dict[str, float] = defaultdict(float)

        # AutoScaleX Infrastructure Telemetry
        self.queue_depths: Dict[str, int] = defaultdict(int, {"fast": 0, "standard": 0, "heavy": 0})
        self.workload_backlog_score: float = 0.0
        self.active_workers: Dict[str, int] = defaultdict(int, {"fast": 1, "standard": 2, "heavy": 1})
        self.token_governor_throttle_events_total: int = 0
        self.llm_token_burn_rate_rpm: int = 0

    def set_queue_depth(self, tier: str, depth: int):
        self.queue_depths[tier.lower()] = max(0, depth)

    def get_queue_depth(self, tier: str) -> int:
        return self.queue_depths.get(tier.lower(), 0)

    def set_workload_backlog_score(self, score: float):
        self.workload_backlog_score = max(0.0, float(score))

    def set_active_workers(self, tier: str, count: int):
        self.active_workers[tier.lower()] = max(0, count)

    def get_active_workers(self, tier: str) -> int:
        return self.active_workers.get(tier.lower(), 0)

    def record_token_throttle(self):
        self.token_governor_throttle_events_total += 1

    def set_token_burn_rate(self, rpm: int):
        self.llm_token_burn_rate_rpm = max(0, rpm)

    def record_request(self, method: str, path: str, status_code: int, duration_seconds: float):
        key = f'{method}:{path}:{status_code}'
        self.request_counts[key] += 1
        # Store latest durations for latency metrics
        if len(self.request_durations[f'{method}:{path}']) > 500:
            self.request_durations[f'{method}:{path}'].pop(0)
        self.request_durations[f'{method}:{path}'].append(duration_seconds)

    def record_worker_task(self, task_name: str, status: str):
        self.worker_tasks_total[f'{task_name}:{status}'] += 1
        if status == "failure":
            self.worker_failures_total[task_name] += 1

    def record_llm_usage(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int, cost_usd: float):
        self.llm_tokens_total[f'{provider}:{model}:prompt'] += prompt_tokens
        self.llm_tokens_total[f'{provider}:{model}:completion'] += completion_tokens
        self.llm_cost_usd_total[f'{provider}:{model}'] += cost_usd

    def generate_metrics_text(self) -> str:
        """Serializes current telemetry to standard Prometheus text exposition format."""
        lines = []

        # 1. HTTP requests total
        lines.append("# HELP openreview_http_requests_total Total number of HTTP requests processed.")
        lines.append("# TYPE openreview_http_requests_total counter")
        for key, count in self.request_counts.items():
            method, path, status = key.split(":")
            lines.append(f'openreview_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}')

        # 2. HTTP request duration p95/avg
        lines.append("# HELP openreview_http_request_duration_seconds Average latency of HTTP requests.")
        lines.append("# TYPE openreview_http_request_duration_seconds gauge")
        for route, durations in self.request_durations.items():
            if durations:
                method, path = route.split(":")
                avg_lat = sum(durations) / len(durations)
                lines.append(f'openreview_http_request_duration_seconds{{method="{method}",path="{path}"}} {avg_lat:.4f}')

        # 3. Active multi-agent reviews
        lines.append("# HELP openreview_active_reviews Current number of active PR reviews.")
        lines.append("# TYPE openreview_active_reviews gauge")
        lines.append(f"openreview_active_reviews {self.active_reviews}")

        # 4. Celery worker tasks
        lines.append("# HELP openreview_worker_tasks_total Total background Celery tasks processed.")
        lines.append("# TYPE openreview_worker_tasks_total counter")
        for key, count in self.worker_tasks_total.items():
            task, status = key.split(":")
            lines.append(f'openreview_worker_tasks_total{{task="{task}",status="{status}"}} {count}')

        # 5. LLM Token Usage
        lines.append("# HELP openreview_llm_tokens_total Total tokens consumed by AI review agents.")
        lines.append("# TYPE openreview_llm_tokens_total counter")
        for key, tokens in self.llm_tokens_total.items():
            provider, model, token_type = key.split(":")
            lines.append(f'openreview_llm_tokens_total{{provider="{provider}",model="{model}",type="{token_type}"}} {tokens}')

        # 6. LLM Cost Tracking in USD
        lines.append("# HELP openreview_llm_cost_usd_total Total estimated LLM cost in USD.")
        lines.append("# TYPE openreview_llm_cost_usd_total counter")
        for key, cost in self.llm_cost_usd_total.items():
            provider, model = key.split(":")
            lines.append(f'openreview_llm_cost_usd_total{{provider="{provider}",model="{model}"}} {cost:.6f}')

        # 7. AutoScaleX Workload Queue Depths
        lines.append("# HELP openreview_queue_depth Current queued review count per AutoScaleX tier.")
        lines.append("# TYPE openreview_queue_depth gauge")
        for tier in ("fast", "standard", "heavy"):
            depth = self.queue_depths.get(tier, 0)
            lines.append(f'openreview_queue_depth{{tier="{tier}"}} {depth}')

        # 8. AutoScaleX Workload Backlog Score
        lines.append("# HELP openreview_workload_backlog_score Sum of complexity weights of queued reviews.")
        lines.append("# TYPE openreview_workload_backlog_score gauge")
        lines.append(f"openreview_workload_backlog_score {self.workload_backlog_score:.2f}")

        # 9. AutoScaleX Active Workers Fleet
        lines.append("# HELP openreview_active_workers Number of active worker pods/processes per tier.")
        lines.append("# TYPE openreview_active_workers gauge")
        for tier in ("fast", "standard", "heavy"):
            workers = self.active_workers.get(tier, 0)
            lines.append(f'openreview_active_workers{{tier="{tier}"}} {workers}')

        # 10. AutoScaleX Token Governor Telemetry
        lines.append("# HELP openreview_token_governor_throttle_events_total Total LLM governor throttle events.")
        lines.append("# TYPE openreview_token_governor_throttle_events_total counter")
        lines.append(f"openreview_token_governor_throttle_events_total {self.token_governor_throttle_events_total}")

        lines.append("# HELP openreview_llm_token_burn_rate_rpm Sliding 60-second window LLM token burn rate.")
        lines.append("# TYPE openreview_llm_token_burn_rate_rpm gauge")
        lines.append(f"openreview_llm_token_burn_rate_rpm {self.llm_token_burn_rate_rpm}")

        return "\n".join(lines) + "\n"


metrics_registry = PrometheusMetricsRegistry()


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware capturing request metrics and latency for Prometheus."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time

        # Normalize path to prevent high cardinality on UUIDs
        path = request.url.path
        if "/reviews/" in path:
            path = "/api/v1/reviews/{id}"
        elif "/repositories/" in path:
            path = "/api/v1/repositories/{id}"
        elif "/findings/" in path:
            path = "/api/v1/findings/{id}"
        elif "/autofix/" in path:
            path = "/api/v1/autofix/{id}"

        metrics_registry.record_request(
            method=request.method,
            path=path,
            status_code=response.status_code,
            duration_seconds=duration,
        )
        return response
