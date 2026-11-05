"""
orchestrator.py — Pipeline Orchestrator and DAG Runner (Unit 1.D)
Executes data pipelines as directed acyclic graphs with dependency resolution,
retry handling, task timing, and execution state logging.
"""

from __future__ import annotations

import time
from typing import Callable, Any


class PipelineTask:
    """An individual execution node in the pipeline DAG."""

    def __init__(
        self,
        name: str,
        func: Callable[[], Any],
        dependencies: list[str] | None = None,
        max_retries: int = 2,
    ) -> None:
        self.name = name
        self.func = func
        self.dependencies = dependencies or []
        self.max_retries = max_retries
        self.status = "PENDING"
        self.duration_ms = 0.0
        self.result: Any = None
        self.error: str | None = None


class PipelineOrchestrator:
    """Coordinates multi-step ML & Data pipelines."""

    def __init__(self, name: str = "ML_Data_Orchestrator") -> None:
        self.name = name
        self.tasks: dict[str, PipelineTask] = {}
        self.execution_order: list[str] = []

    def add_task(
        self,
        name: str,
        func: Callable[[], Any],
        dependencies: list[str] | None = None,
        max_retries: int = 2,
    ) -> PipelineOrchestrator:
        self.tasks[name] = PipelineTask(name, func, dependencies, max_retries)
        return self

    def _topological_sort(self) -> list[str]:
        """Compute execution order respecting task dependencies."""
        visited = set()
        order = []

        def visit(task_name: str, path: set):
            if task_name in path:
                raise ValueError(f"Cyclic dependency detected: {task_name}")
            if task_name not in visited:
                path.add(task_name)
                for dep in self.tasks[task_name].dependencies:
                    if dep not in self.tasks:
                        raise ValueError(f"Task '{task_name}' depends on unknown task '{dep}'")
                    visit(dep, path)
                path.remove(task_name)
                visited.add(task_name)
                order.append(task_name)

        for name in self.tasks:
            visit(name, set())

        return order

    def run(self) -> dict[str, Any]:
        """Execute all tasks in topological dependency order."""
        self.execution_order = self._topological_sort()
        start_total = time.perf_counter()
        results_summary = {}

        for task_name in self.execution_order:
            task = self.tasks[task_name]
            task.status = "RUNNING"
            attempts = 0
            success = False

            while attempts <= task.max_retries and not success:
                attempts += 1
                t0 = time.perf_counter()
                try:
                    task.result = task.func()
                    task.duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                    task.status = "SUCCESS"
                    success = True
                except Exception as exc:
                    task.duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                    if attempts > task.max_retries:
                        task.status = "FAILED"
                        task.error = str(exc)
                        results_summary[task_name] = {
                            "status": "FAILED",
                            "duration_ms": task.duration_ms,
                            "error": str(exc),
                        }
                        return {
                            "pipeline_status": "FAILED",
                            "failed_task": task_name,
                            "results": results_summary,
                        }

            results_summary[task_name] = {
                "status": task.status,
                "duration_ms": task.duration_ms,
                "retries": attempts - 1,
            }

        total_ms = round((time.perf_counter() - start_total) * 1000.0, 2)
        return {
            "pipeline_status": "SUCCESS",
            "total_latency_ms": total_ms,
            "tasks_executed": len(self.execution_order),
            "results": results_summary,
        }
