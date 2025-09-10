# Benchmark Dataset

This directory contains curated PDF files for benchmarking the PDF Ultra Compressor.

## Dataset Categories

### Text-Heavy PDFs
- Academic papers, reports, documentation
- Expected compression: 10-30%
- Primary strategy: qpdf conservative

### Image-Heavy PDFs  
- Presentations, brochures, photo albums
- Expected compression: 30-60%
- Primary strategy: Ghostscript balanced

### Scanned Documents
- Scanned papers, forms, legacy documents
- Expected compression: 40-70% 
- Primary strategy: Ghostscript aggressive safe

## Adding Test Files

To add PDFs to the benchmark dataset:

1. Place PDF files in this directory
2. Use descriptive names indicating content type:
   - `text_academic_paper.pdf`
   - `image_presentation.pdf` 
   - `scan_form_document.pdf`

## Usage

Run benchmarks on all PDFs in this directory:

```bash
python benchmarks/benchmark_runner.py --dataset benchmarks/datasets
```

## Sample Files

Due to licensing constraints, this repository doesn't include sample PDFs. You can:

1. **Generate test PDFs** using the sample generator:
   ```bash
   python benchmarks/generate_samples.py
   ```

2. **Use your own PDFs** - copy representative files here

3. **Download public domain PDFs** from sources like:
   - Project Gutenberg (books)
   - arXiv (academic papers)  
   - Government publications

## File Naming Convention

Use prefixes to categorize files:
- `text_*` - Text-heavy documents
- `image_*` - Image-heavy documents  
- `scan_*` - Scanned documents
- `mixed_*` - Mixed content

This helps the benchmark runner categorize results and select appropriate compression strategies.
