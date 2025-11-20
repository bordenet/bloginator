"""Parallel processing utilities for Bloginator.

Provides thread-pool and process-pool execution for CPU/IO-bound tasks.
"""

import os
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")


def get_default_workers() -> int:
    """Get default number of worker threads based on CPU count.

    Returns:
        Number of workers (CPU count * 2, max 8)
    """
    cpu_count = os.cpu_count() or 4
    # For IO-bound tasks, use 2x CPU count, but cap at 8
    return min(cpu_count * 2, 8)


def parallel_map(
    func: Callable[[T], R],
    items: Iterable[T],
    max_workers: int | None = None,
    desc: str = "Processing",
) -> list[R]:
    """Execute function on items in parallel using ThreadPoolExecutor.

    Args:
        func: Function to apply to each item
        items: Iterable of items to process
        max_workers: Maximum number of worker threads (default: auto)
        desc: Description for logging (unused, for future progress bars)

    Returns:
        List of results in original order

    Example:
        >>> def process(x): return x * 2
        >>> results = parallel_map(process, [1, 2, 3, 4])
        >>> print(results)
        [2, 4, 6, 8]
    """
    items_list = list(items)
    workers = max_workers or get_default_workers()

    # Don't use thread pool for small lists
    if len(items_list) <= 1:
        return [func(item) for item in items_list]

    results = [None] * len(items_list)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks and track their indices
        future_to_index = {executor.submit(func, item): idx for idx, item in enumerate(items_list)}

        # Collect results as they complete
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            results[idx] = future.result()

    return results


def parallel_map_with_progress(
    func: Callable[[T], R],
    items: Iterable[T],
    max_workers: int | None = None,
    progress_callback: Callable[[int], None] | None = None,
) -> list[R]:
    """Execute function on items in parallel with progress tracking.

    Args:
        func: Function to apply to each item
        items: Iterable of items to process
        max_workers: Maximum number of worker threads (default: auto)
        progress_callback: Optional callback called after each item completes
                          with total completed count

    Returns:
        List of results in original order

    Example:
        >>> def process(x): return x * 2
        >>> def progress(n): print(f"Completed: {n}")
        >>> results = parallel_map_with_progress(process, [1,2,3], progress_callback=progress)
    """
    items_list = list(items)
    workers = max_workers or get_default_workers()

    # Don't use thread pool for small lists
    if len(items_list) <= 1:
        results = [func(item) for item in items_list]
        if progress_callback:
            progress_callback(len(results))
        return results

    results = [None] * len(items_list)
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_index = {executor.submit(func, item): idx for idx, item in enumerate(items_list)}

        # Collect results as they complete
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            results[idx] = future.result()

            completed += 1
            if progress_callback:
                progress_callback(completed)

    return results
