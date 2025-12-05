# Performance Benchmarks

Performance tests that measure and track execution time for critical operations.

## Contents

| File | Purpose |
|------|---------|
| `test_performance.py` | Core operation benchmarks |

## Running Benchmarks

```bash
# Run all benchmarks
pytest tests/benchmarks/ -v

# With timing output
pytest tests/benchmarks/ -v --durations=0

# Skip in regular test runs
pytest tests/ -m "not benchmark" -v
```

## Markers

All benchmark tests should use:

```python
@pytest.mark.benchmark
@pytest.mark.performance
@pytest.mark.slow
```

## Benchmarked Operations

- **Extraction**: Document parsing speed by format
- **Chunking**: Text chunking throughput
- **Indexing**: Vector embedding and storage
- **Search**: Query execution time
- **Generation**: LLM prompt construction

## Performance Targets

| Operation | Target | Acceptable |
|-----------|--------|------------|
| Extract (per doc) | < 1s | < 5s |
| Chunk (per 10KB) | < 100ms | < 500ms |
| Index (per chunk) | < 200ms | < 1s |
| Search (per query) | < 500ms | < 2s |

## Notes

- Benchmarks are excluded from regular test runs
- Results vary by hardware; focus on relative changes
- Use `pytest-benchmark` for detailed profiling if needed
