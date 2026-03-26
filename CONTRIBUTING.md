# Contributing to DUCK-Bench

Thank you for your interest in contributing to DUCK-Bench! We welcome contributions of all kinds.

## How to Contribute

### New Questions

Follow our [annotation guide](guides/annotation_guide.md) to create new benchmark questions. Each question should include:

- A natural language question
- Evidence/hints for disambiguation
- A gold SQL query
- Database ID, modality tags, and difficulty level

### New Databases

Submit Dataverse-compatible schema snapshots under `data/databases/`. Include:

- SQLite database file
- Schema documentation
- Sample data sufficient for evaluation

### New Baselines

Add your model under `baselines/` with:

- A configuration file describing the model and prompting strategy
- Prediction scripts
- Output predictions on the dev set

### Bug Fixes and Improvements

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run tests (`uv run pytest`)
5. Submit a pull request

## Code Style

- Python code should be formatted with [ruff](https://docs.astral.sh/ruff/)
- Use type hints where practical
- Add tests for new functionality

## Reporting Issues

Open an issue on GitHub with:

- A clear description of the problem
- Steps to reproduce (if applicable)
- Expected vs actual behavior

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
