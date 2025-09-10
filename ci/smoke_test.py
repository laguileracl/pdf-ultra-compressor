import os
import sys
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'input'
OUTPUT = ROOT / 'output'
INPUT.mkdir(exist_ok=True)
OUTPUT.mkdir(exist_ok=True)

# Create a tiny sample PDF
sample_pdf = INPUT / 'ci_sample.pdf'
if not sample_pdf.exists():
    c = canvas.Canvas(str(sample_pdf), pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(72, 720, "PDF Ultra Compressor - CI Smoke Test")
    c.drawString(72, 700, "This is a generated sample PDF for CI testing.")
    c.showPage()
    c.save()

# Use the new v1 English CLI only
script = ROOT / 'compressor.py'
if not script.exists():
    raise FileNotFoundError("compressor.py not found. Ensure you're running from the repo root.")

# Run the compressor
print(f"Running: {script}")
res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
print(res.stdout)
print(res.stderr)

# Assert output exists
outs = list(OUTPUT.glob('*optimized*.pdf')) + list(OUTPUT.glob('*.pdf'))
assert len(outs) > 0, "No output PDFs produced"

print("Smoke test passed with outputs:")
for p in outs:
    print(" -", p.name)
