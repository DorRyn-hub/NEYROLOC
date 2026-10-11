"""Small, dependency-free runtime probes for the Workspace inspector."""

from __future__ import annotations

import os
import resource
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryUsage:
    bytes: int | None
    is_peak: bool = False


def process_memory_usage() -> MemoryUsage:
    """Return real process RSS, falling back to the OS peak-RSS counter.

    ``psutil`` is optional and is never installed merely for this indicator.
    The fallback remains honest: the caller can label it as a peak value.
    """

    try:
        import psutil

        rss = int(psutil.Process(os.getpid()).memory_info().rss)
        if rss > 0:
            return MemoryUsage(rss, is_peak=False)
    except (ImportError, OSError, ValueError):
        pass

    try:
        maximum = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except (OSError, ValueError):
        return MemoryUsage(None, is_peak=True)
    if maximum <= 0:
        return MemoryUsage(None, is_peak=True)
    # macOS reports bytes; Linux and the BSD-compatible Python docs report KiB.
    multiplier = 1 if sys.platform == "darwin" else 1024
    return MemoryUsage(maximum * multiplier, is_peak=True)


def format_memory_size(byte_count: int | None) -> str:
    if byte_count is None or byte_count < 0:
        return "—"
    gib = byte_count / (1024**3)
    if gib >= 1:
        return f"{gib:.1f} GB"
    mib = byte_count / (1024**2)
    return f"{mib:.0f} MB"
