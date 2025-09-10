# Contributing to PDF Ultra Compressor

Thanks for your interest in improving this project! We welcome issues and pull requests.

## Ways to Contribute
- Report bugs or performance regressions
- Improve compression quality or speed
- Add platform support and installers
- Enhance docs, examples, and tests

## Development Setup
- macOS recommended; install tools:
  - Homebrew: `brew install ghostscript qpdf pdftk-java`
- Python 3.10+

## Project Structure
- `comprimir_ultra.py`: main CLI pipeline (Ghostscript + qpdf + PDFtk)
- `compresor_godtier_fixed.py`: quality-first selector with multiple strategies
- `instalar_herramientas.sh`: macOS helper install script
- `input/`, `output/`: operational folders

## Pull Requests
- Keep changes focused; add tests or sample commands when applicable
- Describe trade-offs and before/after results (sizes, commands used)
- Follow simple Conventional Commits where possible (e.g., `feat:`, `fix:`, `docs:`)

## Coding Guidelines
- Prefer readability over micro-optimizations
- Guard for failure: never write a worse output than input
- Avoid breaking existing CLI flags/behavior; if needed, document clearly

## License
By contributing, you agree your contributions are licensed under the MIT License.
