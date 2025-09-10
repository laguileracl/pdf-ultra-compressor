# Contributing to PDF Ultra Compressor

Thanks for your interest in improving this project! We welcome issues and pull requests.

## Ways to Contribute
- Report bugs or performance regressions
- Improve compression quality or speed
- Enhance docs, examples, and tests

## Development Setup
- macOS or Linux recommended; install tools:
  - Homebrew (macOS): `brew install ghostscript qpdf`
  - apt (Ubuntu): `sudo apt-get install -y ghostscript qpdf`
- Python 3.11+

## Project Structure (v1)
- `compressor.py`: main CLI (English-only)
- `ci/`: smoke test
- `docs/`: overview, quality guardrails, roadmap
- `input/`, `output/`: operational folders

## Pull Requests
- Keep changes focused; add tests or sample commands when applicable
- Describe trade-offs and before/after results (sizes, commands used)
- Follow simple Conventional Commits where possible (e.g., `feat:`, `fix:`, `docs:`)

## Coding Guidelines
- Prefer readability over micro-optimizations
- Never-worse guarantee: don’t ship changes that produce worse outputs by default
- Keep formatting consistent (see `.editorconfig`, `pyproject.toml`)

## Repository metadata
- Add helpful topics to increase discoverability: `pdf`, `compression`, `optimizer`, `ghostscript`, `qpdf`, `cli`, `macos`, `linux`, `psnr`, `ssim`, `ocr`, `jbig2`.
- See `docs/` for detailed notes; a GitHub Wiki is enabled and can mirror `docs/`.

## License
By contributing, you agree your contributions are licensed under the MIT License.
