"""Tests for parallel processing utilities."""

import time

import pytest

from bloginator.utils.parallel import get_default_workers, parallel_map, parallel_map_with_progress


class TestGetDefaultWorkers:
    """Tests for get_default_workers."""

    def test_returns_reasonable_value(self):
        """Test that default workers is reasonable."""
        workers = get_default_workers()
        assert isinstance(workers, int)
        assert workers > 0
        assert workers <= 8  # Should be capped at 8


class TestParallelMap:
    """Tests for parallel_map."""

    def test_simple_map(self):
        """Test basic parallel mapping."""

        def double(x):
            return x * 2

        result = parallel_map(double, [1, 2, 3, 4, 5])
        assert result == [2, 4, 6, 8, 10]

    def test_preserves_order(self):
        """Test that results maintain original order."""

        def slow_process(x):
            # Slower for smaller numbers to test ordering
            time.sleep(0.01 * (6 - x))
            return x * 2

        result = parallel_map(slow_process, [1, 2, 3, 4, 5])
        assert result == [2, 4, 6, 8, 10]

    def test_empty_list(self):
        """Test with empty list."""

        def double(x):
            return x * 2

        result = parallel_map(double, [])
        assert result == []

    def test_single_item(self):
        """Test with single item (should not use thread pool)."""

        def double(x):
            return x * 2

        result = parallel_map(double, [5])
        assert result == [10]

    def test_custom_workers(self):
        """Test with custom worker count."""

        def double(x):
            return x * 2

        result = parallel_map(double, [1, 2, 3, 4], max_workers=2)
        assert result == [2, 4, 6, 8]

    def test_exception_propagation(self):
        """Test that exceptions are propagated."""

        def failing_func(x):
            if x == 3:
                raise ValueError("Test error")
            return x * 2

        with pytest.raises(ValueError, match="Test error"):
            parallel_map(failing_func, [1, 2, 3, 4])

    def test_with_generator(self):
        """Test with generator input."""

        def double(x):
            return x * 2

        result = parallel_map(double, (x for x in range(5)))
        assert result == [0, 2, 4, 6, 8]


class TestParallelMapWithProgress:
    """Tests for parallel_map_with_progress."""

    def test_progress_callback_called(self):
        """Test that progress callback is called."""
        progress_calls = []

        def track_progress(n):
            progress_calls.append(n)

        def double(x):
            return x * 2

        result = parallel_map_with_progress(
            double, [1, 2, 3, 4, 5], progress_callback=track_progress
        )

        assert result == [2, 4, 6, 8, 10]
        assert len(progress_calls) == 5
        assert max(progress_calls) == 5

    def test_progress_callback_incremental(self):
        """Test that progress increases incrementally."""
        progress_calls = []

        def track_progress(n):
            progress_calls.append(n)

        def double(x):
            return x * 2

        parallel_map_with_progress(double, [1, 2, 3], progress_callback=track_progress)

        # Should have 3 calls with increasing values
        assert len(progress_calls) == 3
        assert sorted(progress_calls) == [1, 2, 3]

    def test_without_progress_callback(self):
        """Test that it works without progress callback."""

        def double(x):
            return x * 2

        result = parallel_map_with_progress(double, [1, 2, 3])
        assert result == [2, 4, 6]

    def test_single_item_with_progress(self):
        """Test single item with progress callback."""
        progress_calls = []

        def track_progress(n):
            progress_calls.append(n)

        def double(x):
            return x * 2

        result = parallel_map_with_progress(double, [5], progress_callback=track_progress)

        assert result == [10]
        assert progress_calls == [1]

    def test_empty_list_with_progress(self):
        """Test empty list with progress callback."""
        progress_calls = []

        def track_progress(n):
            progress_calls.append(n)

        def double(x):
            return x * 2

        result = parallel_map_with_progress(double, [], progress_callback=track_progress)

        assert result == []
        # Progress callback is called with 0 for empty list
        assert progress_calls == [0]
