# Contributing to RLM Knowledge Retriever

Thank you for your interest in contributing!

## How to Contribute

### Reporting Bugs

- Use GitHub Issues
- Describe the bug and how to reproduce it
- Include your environment (OS, Python version, etc.)

### Suggesting Enhancements

- Use GitHub Issues with label `enhancement`
- Describe the feature and its use case

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Format code (`black rlm_kb/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Development Setup

```bash
git clone https://github.com/yourusername/rlm-knowledge-retriever.git
cd rlm-knowledge-retriever
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev,all]"
```

## Code Style

- Follow PEP 8
- Use `black` for formatting
- Add type hints where appropriate
- Write docstrings for public functions

## Testing

```bash
pytest tests/ -v
pytest tests/ --cov=rlm_kb
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
