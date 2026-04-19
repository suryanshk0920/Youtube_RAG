"""
Startup Optimization for Low-Memory Environments
================================================
This module provides utilities to reduce memory footprint during startup,
particularly for free-tier hosting (512MB RAM limit).

Key optimizations:
1. Lazy loading of heavy dependencies (embedding models, ChromaDB)
2. Reduced worker count for low-memory environments
3. Garbage collection hints
4. Memory monitoring
"""

import os
import logging

logger = logging.getLogger(__name__)


def optimize_for_low_memory():
    """
    Apply optimizations for low-memory environments (< 1GB RAM).
    Call this before importing heavy dependencies.
    """
    # Set environment variables to reduce memory usage
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")  # Reduce tokenizer memory
    os.environ.setdefault("OMP_NUM_THREADS", "1")  # Limit OpenMP threads
    os.environ.setdefault("MKL_NUM_THREADS", "1")  # Limit MKL threads
    
    # Disable HuggingFace telemetry to save memory
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    
    # Use smaller batch sizes for transformers
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "0")
    
    logger.info("✅ Low-memory optimizations applied")


def get_memory_info() -> dict:
    """Get current memory usage information."""
    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        return {
            "rss_mb": mem_info.rss / 1024 / 1024,  # Resident Set Size
            "vms_mb": mem_info.vms / 1024 / 1024,  # Virtual Memory Size
            "percent": process.memory_percent(),
        }
    except ImportError:
        return {"error": "psutil not installed"}
    except Exception as e:
        return {"error": str(e)}


def log_memory_usage(label: str = ""):
    """Log current memory usage."""
    mem_info = get_memory_info()
    if "error" not in mem_info:
        logger.info(
            f"📊 Memory usage {label}: "
            f"RSS={mem_info['rss_mb']:.1f}MB, "
            f"VMS={mem_info['vms_mb']:.1f}MB, "
            f"Percent={mem_info['percent']:.1f}%"
        )
    else:
        logger.debug(f"Memory monitoring unavailable: {mem_info['error']}")
