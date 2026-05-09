from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for AI detection"""
    processing_time_ms: float
    frame_count: int
    avg_fps: float
    memory_usage_mb: float
    cpu_usage_percent: float


class PerformanceMonitor:
    """Monitor and optimize AI detection performance"""
    
    def __init__(self, max_samples: int = 100):
        self.max_samples = max_samples
        self.metrics_history: deque = deque(maxlen=max_samples)
        self.start_time = time.time()
        self.frame_count = 0
        self.last_frame_time = time.time()
        
    def record_frame_processing(self, processing_time_ms: float):
        """Record processing time for a frame"""
        current_time = time.time()
        self.frame_count += 1
        
        # Calculate FPS
        time_diff = current_time - self.last_frame_time
        current_fps = 1.0 / time_diff if time_diff > 0 else 0
        
        # Store metrics
        metrics = PerformanceMetrics(
            processing_time_ms=processing_time_ms,
            frame_count=self.frame_count,
            avg_fps=self._calculate_avg_fps(),
            memory_usage_mb=self._get_memory_usage(),
            cpu_usage_percent=self._get_cpu_usage()
        )
        
        self.metrics_history.append(metrics)
        self.last_frame_time = current_time
    
    def _calculate_avg_fps(self) -> float:
        """Calculate average FPS over recent samples"""
        if len(self.metrics_history) < 2:
            return 0.0
        
        total_time = time.time() - self.start_time
        return self.frame_count / total_time if total_time > 0 else 0.0
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
        except Exception:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=None)
        except ImportError:
            return 0.0
        except Exception:
            return 0.0
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the most recent performance metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_average_processing_time(self) -> float:
        """Get average processing time over recent samples"""
        if not self.metrics_history:
            return 0.0
        
        total_time = sum(m.processing_time_ms for m in self.metrics_history)
        return total_time / len(self.metrics_history)
    
    def should_throttle(self, target_fps: int = 10) -> bool:
        """Determine if processing should be throttled to maintain target FPS"""
        current_fps = self._calculate_avg_fps()
        return current_fps > target_fps
    
    def get_optimization_suggestions(self) -> List[str]:
        """Get performance optimization suggestions"""
        suggestions = []
        metrics = self.get_current_metrics()
        
        if not metrics:
            return suggestions
        
        # Check processing time
        avg_time = self.get_average_processing_time()
        if avg_time > 100:  # More than 100ms per frame
            suggestions.append("Consider reducing frame resolution")
            suggestions.append("Enable frame skipping in AI config")
        
        # Check memory usage
        if metrics.memory_usage_mb > 1000:  # More than 1GB
            suggestions.append("High memory usage detected")
            suggestions.append("Consider reducing detection frequency")
        
        # Check CPU usage
        if metrics.cpu_usage_percent > 80:
            suggestions.append("High CPU usage detected")
            suggestions.append("Consider reducing AI detection features")
        
        # Check FPS
        if metrics.avg_fps < 5:
            suggestions.append("Low FPS detected")
            suggestions.append("Optimize frame processing pipeline")
        
        return suggestions


class FrameSkipper:
    """Frame skipping utility for performance optimization"""
    
    def __init__(self, skip_count: int = 2):
        self.skip_count = skip_count
        self.counter = 0
    
    def should_process_frame(self) -> bool:
        """Determine if current frame should be processed"""
        self.counter += 1
        return self.counter % (self.skip_count + 1) == 0
    
    def reset(self):
        """Reset the frame counter"""
        self.counter = 0


# Global performance monitor
performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return performance_monitor


async def run_performance_optimization():
    """Background task for performance optimization"""
    while True:
        try:
            monitor = get_performance_monitor()
            suggestions = monitor.get_optimization_suggestions()
            
            if suggestions:
                logger.info(f"Performance suggestions: {suggestions}")
            
            # Run every 30 seconds
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Performance optimization error: {e}")
            await asyncio.sleep(60)
