# PDF Ultra Compressor — Docs

Welcome to the docs. This repository ships a CLI-only, quality-first PDF optimizer.

## Overview

- Input folder: `input/`
- Output folder: `output/`
- Originals moved to: `input/processed/`

Run:

```bash
python3 compressor.py
```

## Quality guardrails

- Never-worse: selection heuristic preserves quality; if no improvement, original is copied.
- Optional PSNR gate: rasterizes a few pages, checks PSNR; if below threshold, falls back to safer result or preserves original.

## Roadmap

- SSIM/LPIPS quality gates
- OCR/JBIG2 (MRC) for scanned docs
- Benchmark suite & dataset
