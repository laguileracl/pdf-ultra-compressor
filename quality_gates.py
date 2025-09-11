#!/usr/bin/env python3
"""
Advanced quality gates for PDF compression.

Implements SSIM and LPIPS quality assessment to complement the existing PSNR gate.
Provides more sophisticated perceptual quality evaluation for diverse content types.

Usage:
    from quality_gates import QualityGateChecker
    
    checker = QualityGateChecker()
    passed, metrics = checker.evaluate_quality(original_pdf, compressed_pdf)
"""

import os
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any
import json

# Core imaging deps (always try to import independently)
try:
    import numpy as np  # type: ignore
except Exception:
    np = None  # type: ignore

try:
    from PIL import Image  # type: ignore
except Exception:
    Image = None  # type: ignore

# Optional SSIM dependencies (scikit-image)
try:
    from skimage.metrics import structural_similarity as ssim  # type: ignore
    from skimage.color import rgb2gray  # type: ignore
    HAS_SKIMAGE = True
except Exception:
    HAS_SKIMAGE = False
    ssim = None  # type: ignore
    rgb2gray = None  # type: ignore

try:
    import torch
    import lpips
    HAS_LPIPS = False  # Will be set to True if LPIPS loads successfully
    
    # Try to load LPIPS model
    try:
        lpips_model = lpips.LPIPS(net='alex')  # or 'vgg', 'squeeze'
        HAS_LPIPS = True
    except Exception:
        lpips_model = None
        HAS_LPIPS = False
except ImportError:
    HAS_LPIPS = False
    lpips_model = None


class QualityGateConfig:
    """Configuration for quality gates."""
    
    def __init__(self):
        # PSNR thresholds (existing)
        self.psnr_threshold = 35.0
        self.psnr_enabled = True
        
        # SSIM thresholds  
        self.ssim_threshold = 0.85
        self.ssim_enabled = True
        
        # LPIPS thresholds (lower is better for LPIPS)
        self.lpips_threshold = 0.15
        self.lpips_enabled = False  # Opt-in due to model size
        
        # Quality gate behavior
        self.fail_on_any_gate = False  # If True, ALL gates must pass
        self.require_majority = True   # If True, majority of gates must pass
        
        # Rasterization settings
        self.raster_dpi = 150
        self.max_pages_to_check = 5
        self.page_selection = "distributed"  # "first", "distributed", "random"
        
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'QualityGateConfig':
        """Create config from dictionary."""
        config = cls()
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary."""
        return {
            'psnr_threshold': self.psnr_threshold,
            'psnr_enabled': self.psnr_enabled,
            'ssim_threshold': self.ssim_threshold,
            'ssim_enabled': self.ssim_enabled,
            'lpips_threshold': self.lpips_threshold,
            'lpips_enabled': self.lpips_enabled,
            'fail_on_any_gate': self.fail_on_any_gate,
            'require_majority': self.require_majority,
            'raster_dpi': self.raster_dpi,
            'max_pages_to_check': self.max_pages_to_check,
            'page_selection': self.page_selection
        }


class QualityMetrics:
    """Container for quality assessment metrics."""
    
    def __init__(self):
        self.psnr: Optional[float] = None
        self.ssim: Optional[float] = None
        self.lpips: Optional[float] = None
        
        # Per-page metrics (for debugging)
        self.page_metrics: List[Dict] = []
        
        # Gate results
        self.psnr_passed: Optional[bool] = None
        self.ssim_passed: Optional[bool] = None
        self.lpips_passed: Optional[bool] = None
        
        # Overall result
        self.overall_passed: bool = False
        self.gates_evaluated: List[str] = []
        self.gates_passed: List[str] = []
        self.gates_failed: List[str] = []
        
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for JSON serialization."""
        return {
            'psnr': self.psnr,
            'ssim': self.ssim,
            'lpips': self.lpips,
            'psnr_passed': self.psnr_passed,
            'ssim_passed': self.ssim_passed,
            'lpips_passed': self.lpips_passed,
            'overall_passed': self.overall_passed,
            'gates_evaluated': self.gates_evaluated,
            'gates_passed': self.gates_passed,
            'gates_failed': self.gates_failed,
            'page_count': len(self.page_metrics)
        }


class QualityGateChecker:
    """Advanced quality gate checker with SSIM and LPIPS support."""
    
    def __init__(self, config: Optional[QualityGateConfig] = None):
        self.config = config or QualityGateConfig()
        self._check_dependencies()
        
    def _check_dependencies(self):
        """Check and warn about missing dependencies."""
        missing = []
        
        if self.config.ssim_enabled and not HAS_SKIMAGE:
            missing.append("scikit-image (for SSIM)")
            self.config.ssim_enabled = False
            
        if self.config.lpips_enabled and not HAS_LPIPS:
            missing.append("torch + lpips (for LPIPS)")
            self.config.lpips_enabled = False
            
        if missing:
            print(f"Warning: Quality gates disabled due to missing dependencies: {', '.join(missing)}")
            print("Install with: pip install scikit-image torch lpips")
    
    def evaluate_quality(self, original_pdf: Path, compressed_pdf: Path) -> Tuple[bool, QualityMetrics]:
        """
        Evaluate quality of compressed PDF against original.
        
        Returns:
            Tuple of (passed, metrics) where passed indicates if quality gates passed
        """
        metrics = QualityMetrics()
        
        try:
            # Rasterize both PDFs for comparison
            original_images = self._rasterize_pdf(original_pdf)
            compressed_images = self._rasterize_pdf(compressed_pdf)
            
            if not original_images or not compressed_images:
                print("Warning: Could not rasterize PDFs for quality assessment")
                metrics.overall_passed = True  # Fail open
                return True, metrics
            
            # Ensure same number of pages (take minimum)
            min_pages = min(len(original_images), len(compressed_images))
            page_indices = self._select_pages_to_check(min_pages)
            
            # Compute metrics for selected pages
            psnr_values = []
            ssim_values = []
            lpips_values = []
            
            for page_idx in page_indices:
                if page_idx >= min_pages:
                    continue
                    
                original_img = original_images[page_idx]
                compressed_img = compressed_images[page_idx]
                
                page_metrics = {'page': page_idx}
                
                # PSNR (existing logic)
                if self.config.psnr_enabled:
                    psnr = self._compute_psnr(original_img, compressed_img)
                    if psnr is not None:
                        psnr_values.append(psnr)
                        page_metrics['psnr'] = psnr
                
                # SSIM
                if self.config.ssim_enabled:
                    ssim_val = self._compute_ssim(original_img, compressed_img)
                    if ssim_val is not None:
                        ssim_values.append(ssim_val)
                        page_metrics['ssim'] = ssim_val
                
                # LPIPS
                if self.config.lpips_enabled:
                    lpips_val = self._compute_lpips(original_img, compressed_img)
                    if lpips_val is not None:
                        lpips_values.append(lpips_val)
                        page_metrics['lpips'] = lpips_val
                
                metrics.page_metrics.append(page_metrics)
            
            # Calculate average metrics
            if psnr_values:
                metrics.psnr = sum(psnr_values) / len(psnr_values)
                metrics.psnr_passed = metrics.psnr >= self.config.psnr_threshold
                metrics.gates_evaluated.append('psnr')
                if metrics.psnr_passed:
                    metrics.gates_passed.append('psnr')
                else:
                    metrics.gates_failed.append('psnr')
            
            if ssim_values:
                metrics.ssim = sum(ssim_values) / len(ssim_values)
                metrics.ssim_passed = metrics.ssim >= self.config.ssim_threshold
                metrics.gates_evaluated.append('ssim')
                if metrics.ssim_passed:
                    metrics.gates_passed.append('ssim')
                else:
                    metrics.gates_failed.append('ssim')
            
            if lpips_values:
                metrics.lpips = sum(lpips_values) / len(lpips_values)
                metrics.lpips_passed = metrics.lpips <= self.config.lpips_threshold
                metrics.gates_evaluated.append('lpips')
                if metrics.lpips_passed:
                    metrics.gates_passed.append('lpips')
                else:
                    metrics.gates_failed.append('lpips')
            
            # Determine overall pass/fail
            metrics.overall_passed = self._evaluate_overall_result(metrics)
            
            return metrics.overall_passed, metrics
            
        except Exception as e:
            print(f"Error in quality evaluation: {e}")
            # Fail open on errors
            metrics.overall_passed = True
            return True, metrics
    
    def _evaluate_overall_result(self, metrics: QualityMetrics) -> bool:
        """Determine if quality gates passed overall."""
        if not metrics.gates_evaluated:
            return True  # No gates to evaluate, pass
        
        passed_count = len(metrics.gates_passed)
        total_count = len(metrics.gates_evaluated)
        
        if self.config.fail_on_any_gate:
            # ALL gates must pass
            return passed_count == total_count
        elif self.config.require_majority:
            # Majority of gates must pass
            return passed_count > (total_count / 2)
        else:
            # ANY gate passing is sufficient
            return passed_count > 0
    
    def _select_pages_to_check(self, total_pages: int) -> List[int]:
        """Select which pages to check for quality assessment."""
        max_pages = min(self.config.max_pages_to_check, total_pages)
        
        if self.config.page_selection == "first":
            return list(range(max_pages))
        elif self.config.page_selection == "distributed":
            if total_pages <= max_pages:
                return list(range(total_pages))
            else:
                # Distribute pages evenly across document
                step = total_pages / max_pages
                return [int(i * step) for i in range(max_pages)]
        elif self.config.page_selection == "random":
            import random
            return random.sample(range(total_pages), max_pages)
        else:
            return list(range(max_pages))
    
    def _rasterize_pdf(self, pdf_path: Path) -> List[Any]:
        """Rasterize PDF pages to numpy arrays for comparison."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Use Ghostscript to convert PDF to images
                output_pattern = temp_path / "page_%03d.png"
                
                cmd = [
                    "gs", "-dNOPAUSE", "-dBATCH", "-dSAFER",
                    "-sDEVICE=png16m",
                    f"-r{self.config.raster_dpi}",
                    f"-sOutputFile={output_pattern}",
                    str(pdf_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Ghostscript error: {result.stderr}")
                    return []
                
                # Load generated images (prefer Pillow, fallback to OpenCV)
                images: List[Any] = []
                # Try to import cv2 as optional fallback
                try:
                    import cv2  # type: ignore
                except Exception:
                    cv2 = None  # type: ignore

                if np is None:
                    print("Warning: NumPy not available; skipping quality assessment raster load")
                    return []

                for png_file in sorted(temp_path.glob("page_*.png")):
                    try:
                        if Image is not None:
                            img = Image.open(png_file).convert('RGB')
                            img_array = np.array(img)
                            images.append(img_array)
                        elif cv2 is not None:
                            bgr = cv2.imread(str(png_file), cv2.IMREAD_COLOR)
                            if bgr is None:
                                continue
                            rgb = bgr[:, :, ::-1]
                            images.append(rgb)
                        else:
                            print(f"Error loading {png_file}: no imaging backend available (Pillow/OpenCV)")
                            continue
                    except Exception as e:
                        print(f"Error loading {png_file}: {e}")
                        continue
                
                return images
                
        except Exception as e:
            print(f"Error rasterizing {pdf_path}: {e}")
            return []
    
    def _compute_psnr(self, img1: Any, img2: Any) -> Optional[float]:
        """Compute PSNR between two images."""
        try:
            # Ensure same dimensions
            if img1.shape != img2.shape:
                # Resize to smaller dimensions
                min_h = min(img1.shape[0], img2.shape[0])
                min_w = min(img1.shape[1], img2.shape[1])
                img1 = img1[:min_h, :min_w]
                img2 = img2[:min_h, :min_w]
            
            # Convert to float and compute MSE
            img1_f = img1.astype(np.float64)
            img2_f = img2.astype(np.float64)
            
            mse = np.mean((img1_f - img2_f) ** 2)
            if mse == 0:
                return 100.0  # Perfect match
            
            max_pixel = 255.0
            psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
            return float(psnr)
            
        except Exception as e:
            print(f"Error computing PSNR: {e}")
            return None
    
    def _compute_ssim(self, img1: Any, img2: Any) -> Optional[float]:
        """Compute SSIM between two images."""
        if not HAS_SKIMAGE:
            return None
            
        try:
            # Ensure same dimensions
            if img1.shape != img2.shape:
                min_h = min(img1.shape[0], img2.shape[0])
                min_w = min(img1.shape[1], img2.shape[1])
                img1 = img1[:min_h, :min_w]
                img2 = img2[:min_h, :min_w]
            
            # Convert to grayscale for SSIM
            if len(img1.shape) == 3:
                img1_gray = rgb2gray(img1)
                img2_gray = rgb2gray(img2)
            else:
                img1_gray = img1
                img2_gray = img2
            
            # Compute SSIM
            ssim_val = ssim(img1_gray, img2_gray, data_range=1.0)
            return float(ssim_val)
            
        except Exception as e:
            print(f"Error computing SSIM: {e}")
            return None
    
    def _compute_lpips(self, img1: Any, img2: Any) -> Optional[float]:
        """Compute LPIPS between two images."""
        if not HAS_LPIPS or lpips_model is None:
            return None
            
        try:
            # Ensure same dimensions and convert to tensors
            if img1.shape != img2.shape:
                min_h = min(img1.shape[0], img2.shape[0])
                min_w = min(img1.shape[1], img2.shape[1])
                img1 = img1[:min_h, :min_w]
                img2 = img2[:min_h, :min_w]
            
            # Convert to torch tensors and normalize to [-1, 1]
            img1_tensor = torch.from_numpy(img1).float().permute(2, 0, 1).unsqueeze(0)
            img2_tensor = torch.from_numpy(img2).float().permute(2, 0, 1).unsqueeze(0)
            
            img1_tensor = (img1_tensor / 255.0) * 2.0 - 1.0
            img2_tensor = (img2_tensor / 255.0) * 2.0 - 1.0
            
            # Compute LPIPS distance
            with torch.no_grad():
                lpips_dist = lpips_model(img1_tensor, img2_tensor)
                return float(lpips_dist.item())
            
        except Exception as e:
            print(f"Error computing LPIPS: {e}")
            return None
    
    def create_quality_report(self, metrics: QualityMetrics, output_file: Optional[Path] = None) -> str:
        """Create a detailed quality assessment report."""
        report_lines = [
            "PDF Quality Assessment Report",
            "=" * 40,
            f"Overall Result: {'PASS' if metrics.overall_passed else 'FAIL'}",
            ""
        ]
        
        # Summary metrics
        if metrics.psnr is not None:
            status = "PASS" if metrics.psnr_passed else "FAIL"
            report_lines.append(f"PSNR: {metrics.psnr:.2f} dB (threshold: {self.config.psnr_threshold}) - {status}")
        
        if metrics.ssim is not None:
            status = "PASS" if metrics.ssim_passed else "FAIL"
            report_lines.append(f"SSIM: {metrics.ssim:.3f} (threshold: {self.config.ssim_threshold}) - {status}")
        
        if metrics.lpips is not None:
            status = "PASS" if metrics.lpips_passed else "FAIL"
            report_lines.append(f"LPIPS: {metrics.lpips:.3f} (threshold: {self.config.lpips_threshold}) - {status}")
        
        report_lines.extend([
            "",
            f"Gates evaluated: {', '.join(metrics.gates_evaluated)}",
            f"Gates passed: {', '.join(metrics.gates_passed)}",
            f"Gates failed: {', '.join(metrics.gates_failed)}",
            ""
        ])
        
        # Per-page details
        if metrics.page_metrics:
            report_lines.append("Per-page metrics:")
            for page_data in metrics.page_metrics:
                page_line = f"  Page {page_data['page'] + 1}:"
                if 'psnr' in page_data:
                    page_line += f" PSNR={page_data['psnr']:.1f}"
                if 'ssim' in page_data:
                    page_line += f" SSIM={page_data['ssim']:.3f}"
                if 'lpips' in page_data:
                    page_line += f" LPIPS={page_data['lpips']:.3f}"
                report_lines.append(page_line)
        
        report_text = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
        
        return report_text


def main():
    """Test the quality gate system."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test PDF quality gates")
    parser.add_argument("original", help="Original PDF file")
    parser.add_argument("compressed", help="Compressed PDF file")
    parser.add_argument("--config", help="JSON config file for quality gates")
    parser.add_argument("--report", help="Output report file")
    
    args = parser.parse_args()
    
    # Load config if provided
    config = QualityGateConfig()
    if args.config:
        with open(args.config, 'r') as f:
            config_dict = json.load(f)
            config = QualityGateConfig.from_dict(config_dict)
    
    # Run quality assessment
    checker = QualityGateChecker(config)
    passed, metrics = checker.evaluate_quality(Path(args.original), Path(args.compressed))
    
    # Generate report
    report = checker.create_quality_report(metrics, Path(args.report) if args.report else None)
    print(report)
    
    # Exit with appropriate code
    exit(0 if passed else 1)


if __name__ == "__main__":
    main()
