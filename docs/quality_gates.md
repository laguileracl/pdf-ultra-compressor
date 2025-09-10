# Quality Gates Configuration

This document explains the quality gate system in PDF Ultra Compressor.

## Overview

Quality gates are safety mechanisms that ensure compressed PDFs maintain acceptable visual quality. The system supports multiple quality metrics with configurable thresholds.

## Available Quality Gates

### PSNR (Peak Signal-to-Noise Ratio)
- **Default**: Enabled, threshold 35 dB
- **Purpose**: Measures pixel-level difference between original and compressed
- **Good for**: General quality assessment, fast computation
- **Dependencies**: PIL/Pillow, numpy

### SSIM (Structural Similarity Index)
- **Default**: Optional, threshold 0.85
- **Purpose**: Measures structural similarity preserving perceptual quality
- **Good for**: Text documents, images with structure
- **Dependencies**: scikit-image

### LPIPS (Learned Perceptual Image Patch Similarity)
- **Default**: Opt-in, threshold 0.15
- **Purpose**: Deep learning-based perceptual similarity
- **Good for**: Complex images, when human perception matters most
- **Dependencies**: torch, lpips (large download ~100MB)

## Configuration

### Command Line

```bash
# Basic PSNR-only quality gates
python compressor.py

# Enable all available quality gates  
python compressor.py --advanced-gates
```

### Programmatic Configuration

```python
from quality_gates import QualityGateConfig, QualityGateChecker

# Custom configuration
config = QualityGateConfig()
config.psnr_threshold = 40.0      # Stricter PSNR
config.ssim_threshold = 0.90      # Stricter SSIM
config.lpips_enabled = True       # Enable LPIPS
config.require_majority = True    # Majority of gates must pass

checker = QualityGateChecker(config)
```

### JSON Configuration File

Create `quality_config.json`:

```json
{
  "psnr_threshold": 35.0,
  "psnr_enabled": true,
  "ssim_threshold": 0.85,
  "ssim_enabled": true,
  "lpips_threshold": 0.15,
  "lpips_enabled": false,
  "fail_on_any_gate": false,
  "require_majority": true,
  "raster_dpi": 150,
  "max_pages_to_check": 5,
  "page_selection": "distributed"
}
```

## Gate Evaluation Logic

### Majority Mode (Default)
- More than half of enabled gates must pass
- Example: PSNR pass + SSIM fail + LPIPS pass = Overall PASS (2/3)

### Strict Mode (`fail_on_any_gate: true`)
- ALL enabled gates must pass
- Example: PSNR pass + SSIM fail + LPIPS pass = Overall FAIL

### Permissive Mode (`require_majority: false`)
- ANY enabled gate passing is sufficient
- Example: PSNR fail + SSIM fail + LPIPS pass = Overall PASS

## Installation

### Basic (PSNR only)
```bash
pip install pillow numpy
```

### With SSIM
```bash
pip install pillow numpy scikit-image
```

### Full Suite (including LPIPS)
```bash
pip install pillow numpy scikit-image torch lpips
```

## Performance Considerations

### Speed
- **PSNR**: Fast (~100ms per page)
- **SSIM**: Medium (~200ms per page)
- **LPIPS**: Slow (~1-2s per page, GPU recommended)

### Memory
- **PSNR/SSIM**: Low memory usage
- **LPIPS**: High memory usage (~500MB+ for model)

### Recommendations
- **Development/CI**: PSNR + SSIM
- **Production batch**: PSNR only for speed
- **Quality-critical**: All gates enabled
- **Large documents**: Reduce `max_pages_to_check`

## Troubleshooting

### Missing Dependencies
Quality gates automatically disable if dependencies are missing and fall back to available gates.

### Memory Issues
Reduce `raster_dpi` or `max_pages_to_check`:

```json
{
  "raster_dpi": 100,
  "max_pages_to_check": 3
}
```

### Slow Performance
- Disable LPIPS for faster processing
- Use GPU for LPIPS if available
- Process fewer pages

### False Positives
- Lower thresholds for strict content
- Use `page_selection: "first"` for consistent pages
- Enable multiple gates for better accuracy

## Examples

### Text-Heavy Documents
```json
{
  "psnr_threshold": 40.0,
  "ssim_threshold": 0.90,
  "lpips_enabled": false
}
```

### Image-Heavy Documents  
```json
{
  "psnr_threshold": 30.0,
  "ssim_threshold": 0.80,
  "lpips_threshold": 0.20,
  "lpips_enabled": true
}
```

### Scanned Documents
```json
{
  "psnr_threshold": 28.0,
  "ssim_threshold": 0.75,
  "require_majority": false
}
```
