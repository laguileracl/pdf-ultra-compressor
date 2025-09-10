# 🚀 PDF Ultra Compressor

[![CI](https://github.com/laguileracl/pdf-ultra-compressor/actions/workflows/ci.yml/badge.svg)](https://github.com/laguileracl/pdf-ultra-compressor/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Discussions](https://img.shields.io/badge/Chat-Discussions-blue)](https://github.com/laguileracl/pdf-ultra-compressor/discussions)
[![Wiki](https://img.shields.io/badge/Wiki-enabled-blueviolet)](https://github.com/laguileracl/pdf-ultra-compressor/wiki)

Command-line, quality-first PDF optimizer for text- and image-heavy PDFs. Drop files into `input/`, get optimized results in `output/`. Focus: maximum size reduction without perceptible quality loss, with strict “never worse” guards. See `docs/` for more details. For longer docs, visit the [Wiki](https://github.com/laguileracl/pdf-ultra-compressor/wiki) — quick links: [Home](https://github.com/laguileracl/pdf-ultra-compressor/wiki), [Usage](https://github.com/laguileracl/pdf-ultra-compressor/wiki/Usage), [Quality Gates](https://github.com/laguileracl/pdf-ultra-compressor/wiki/Quality-Gates), [Roadmap](https://github.com/laguileracl/pdf-ultra-compressor/wiki/Roadmap).

Keywords: pdf compression, pdf optimizer, ghostscript, qpdf, ocr, jbig2, jpeg2000, lossless, high quality, macos, linux, ci, command line

## Features

- Drop-in folder workflow: put PDFs in `input/`, get results in `output/`.
- Multi-pass strategy: Ghostscript (prepress/printer/ebook) + qpdf.
- Quality-first scoring with “never worse” safeguard (copies original if no gain).
- Optional perceptual quality gate (PSNR) to prevent visible degradation.
- Anonymous telemetry (opt-out) records technical, privacy-safe metrics to improve algorithms. Disable with `--disable-telemetry`.

## Highlights

- 🎯 Smart multi-pass pipeline: Ghostscript + qpdf
- 🧠 Quality-first scoring: selects the best candidate (size vs. visual safety)
- 📂 Zero-config workflow: `input/` → `output` (processed moved to `input/processed/`)
- 🧹 Structural cleanup and linearization when possible
- 🛡️ Never-worse guarantee: falls back to original if not improved

## Quick Start (macOS)

Install system tools (recommended):

```bash
brew install ghostscript qpdf
```

Then run:

```bash
# Put PDFs in input/
cp ~/Downloads/my.pdf input/

# Run the compressor (English v1)
python3 compressor.py

# Results in output/
ls output/
```

Alternatively, run the new v1 CLI (English-only):

```bash
python3 compressor.py
```

Telemetry is enabled by default and stores anonymized, technical-only data in `telemetry_data/` locally. To opt out:

```bash
python3 compressor.py --disable-telemetry
```

## Folder Layout

```
pdf-ultra-compressor/
├─ input/                 # Place PDFs here
│  └─ processed/          # Processed originals are moved here
├─ output/                # Optimized PDFs are written here
├─ compressor.py          # Primary CLI optimizer (English v1)
├─ ci/                    # Smoke test
├─ install_tools.sh       # macOS helper to install ghostscript & qpdf
└─ docs & meta
```

## Typical Results

- Scanned documents: 40–70% reduction
- Image-heavy PDFs: 30–60% reduction
- Mostly text PDFs: 10–30% reduction
- Visual quality: preserved; never-worse guarantee (PSNR gate optional)

## Roadmap

- Add OCRmyPDF + JBIG2 for scanned PDFs (MRC-style pipeline)
- Perceptual quality gates with SSIM/LPIPS (PSNR already available)

## Contributing

Contributions are welcome! Please read `CONTRIBUTING.md` and open an issue or pull request.

## License

MIT — see `LICENSE`.

## Community & Discussions

Have questions, feature ideas, or want to share results? Join the project Discussions: https://github.com/laguileracl/pdf-ultra-compressor/discussions

- Announcements: pinned “Welcome & Roadmap”
- Q&A: ask questions
- Ideas: feature proposals
