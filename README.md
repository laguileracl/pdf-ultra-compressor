# 🚀 PDF Ultra Compressor

Command-line, high-quality PDF optimizer designed for open collaboration. Drop files into `input/`, get optimized results in `output/`. Focus: maximum size reduction without perceptible quality loss, with strict “never worse” guards.

## Highlights

- 🎯 Smart multi-pass pipeline: Ghostscript + qpdf (+ PDFtk if available)
- 🧠 Quality-first scoring: selects the best candidate (size vs. visual safety)
- 📂 Zero-config workflow: `input/` → `output/` (processed moved to `input/procesados/`)
- 🧹 Structural cleanup and linearization when possible
- � Never-worse guarantee: falls back to original if not improved

## Quick Start (macOS)

Install system tools (recommended):

```bash
brew install ghostscript qpdf pdftk-java
```

Then run:

```bash
# Put PDFs in input/
cp ~/Downloads/my.pdf input/

# Run the compressor
python3 comprimir_ultra.py

# Results in output/
ls output/
```

Alternatively, use the helper script:

```bash
./comprimir.sh
```

## Folder Layout

```
compresorpdf/
├─ input/                 # Place PDFs here
│  └─ procesados/         # Processed originals are moved here
├─ output/                # Optimized PDFs are written here
├─ comprimir_ultra.py     # Primary CLI optimizer
├─ compresor_godtier_fixed.py  # Advanced selector (quality-first)
└─ scripts...
```

## Typical Results

- Scanned documents: 40–70% reduction
- Image-heavy PDFs: 30–60% reduction
- Mostly text PDFs: 10–30% reduction
- Visual quality: preserved; never-worse guarantee

## Contributing

Contributions are welcome! Please read `CONTRIBUTING.md` and open an issue or pull request.

## License

MIT — see `LICENSE`.
