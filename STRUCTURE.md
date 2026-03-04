# Project Structure

```
LeakShield/
├── leakshield/              # Core library
│   ├── engines/             # Detection engines
│   │   ├── hash_engine.py   # L4: Sample duplication
│   │   ├── mdf_engine.py    # L1/L5/L6: Distribution, label, temporal
│   │   └── image_engine.py  # L4: Image duplication
│   ├── __init__.py          # Main API
│   ├── config.py            # Configuration
│   ├── result.py            # Result classes
│   └── cli.py               # Command-line interface
│
├── tests/                   # Test suite (33 tests, 72% coverage)
├── benchmarks/              # Performance benchmarks (100% detection rate)
├── examples/                # Usage examples
├── .github/                 # CI/CD workflows
│
├── README.md                # Project documentation
├── CONTRIBUTING.md          # Contribution guidelines
├── CHANGELOG.md             # Version history
├── BENCHMARK.md             # Performance report
├── STRUCTURE.md             # This file
├── LICENSE                  # MIT License
└── pyproject.toml           # Project configuration
```

## Key Files

- **README.md**: Installation, usage, and examples
- **BENCHMARK.md**: Performance validation (100% detection rate)
- **CONTRIBUTING.md**: How to contribute
- **STRUCTURE.md**: Project structure overview
- **LICENSE**: MIT open source license

## Core Components

- **leakshield/**: Main library code
- **tests/**: Comprehensive test suite
- **benchmarks/**: Performance benchmarks
- **examples/**: Usage examples and tutorials

## Development

```bash
# Install
pip install -e ".[dev,image]"

# Test
pytest tests/ -v

# Benchmark
python benchmarks/run_benchmark.py
```

## Links

- **GitHub**: https://github.com/eachst/LeakShield
- **PyPI**: https://pypi.org/project/leakshield/
- **Issues**: https://github.com/eachst/LeakShield/issues
