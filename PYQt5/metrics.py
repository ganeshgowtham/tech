from typing import Dict
import time
from contextlib import contextmanager

class NodeMetrics:
    def __init__(self):
        self.metrics: Dict[str, float] = {}
        self.start_time = None
        self.total_time = 0

    def start_workflow(self):
        """Start timing the entire workflow"""
        self.start_time = time.time()
        self.metrics.clear()

    def end_workflow(self):
        """End timing the entire workflow"""
        if self.start_time is not None:
            self.total_time = time.time() - self.start_time
            self.start_time = None

    @contextmanager
    def measure_node(self, node_name: str):
        """Context manager to measure execution time of a node"""
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.metrics[node_name] = duration

    def print_metrics(self):
        """Print execution metrics for all nodes"""
        print("\n=== Execution Metrics ===")
        if not self.total_time:
            print("No metrics available - workflow hasn't completed")
            return

        print(f"\nTotal execution time: {self.total_time:.2f} seconds")
        print("\nNode-wise breakdown:")
        print("-" * 50)
        print(f"{'Node':<20} {'Time (s)':<10} {'Percentage':<10}")
        print("-" * 50)

        for node_name, duration in self.metrics.items():
            percentage = (duration / self.total_time) * 100
            print(f"{node_name:<20} {duration:.2f}s      {percentage:.1f}%")