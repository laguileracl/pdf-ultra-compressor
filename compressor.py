#!/usr/bin/env python3
"""
PDF Ultra Compressor — v1 (English-only)
Command-line, quality-first PDF optimizer with a conservative fallback and advanced quality gates.

Workflow:
  - Put PDFs in input/
  - Run: python3 compressor.py
  - Optimized PDFs appear in output/
  - Originals are moved to input/processed/

Quality Gates:
  - PSNR (peak signal-to-noise ratio) - default threshold 35 dB
  - SSIM (structural similarity) - optional, threshold 0.85
  - LPIPS (learned perceptual image patch similarity) - optional, threshold 0.15
"""

import shutil
import subprocess
import tempfile
import math
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

# Try to import advanced quality gates
try:
    from quality_gates import QualityGateChecker, QualityGateConfig
    HAS_ADVANCED_GATES = True
except ImportError:
    HAS_ADVANCED_GATES = False

# Try to import anonymous telemetry (optional)
try:
    from anonymous_telemetry import AnonymousTelemetry
    HAS_TELEMETRY = True
except ImportError:
    HAS_TELEMETRY = False


class PDFCompressor:
    """Quality-first PDF compressor with tool auto-detection and safety guards."""

    def __init__(self, input_dir: str = "input", output_dir: str = "output", enable_advanced_gates: bool = False,
                 enable_telemetry: bool = True, enable_anti_noise: bool = False, enable_advanced_raster: bool = False,
                 prefer_sharpness: bool = False):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.enable_advanced_gates = enable_advanced_gates and HAS_ADVANCED_GATES
        self.enable_telemetry = enable_telemetry and HAS_TELEMETRY
        self.enable_anti_noise = enable_anti_noise
        self.enable_advanced_raster = enable_advanced_raster
        self.prefer_sharpness = prefer_sharpness

        # Ensure directories exist
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

        # Detect tools on PATH and common locations (macOS/Homebrew)
        self.tools = self._detect_tools()
        
        # Initialize advanced quality gates if enabled
        self.quality_checker = None
        if self.enable_advanced_gates:
            try:
                self.quality_checker = QualityGateChecker()
                print("🔬 Advanced quality gates enabled (PSNR + SSIM + LPIPS)")
            except Exception as e:
                print(f"⚠️  Advanced quality gates failed to initialize: {e}")
                self.enable_advanced_gates = False

        # Initialize anonymous telemetry (attribute always present)
        self.telemetry = None
        if self.enable_telemetry:
            try:
                self.telemetry = AnonymousTelemetry()
                print("📊 Anonymous telemetry enabled for algorithm improvement")
            except Exception as e:
                print(f"⚠️  Telemetry failed to initialize: {e}")
                self.enable_telemetry = False

        print("🚀 PDF ULTRA COMPRESSOR (v1)")
        print(f"📁 Input:  {self.input_dir.absolute()}")
        print(f"📁 Output: {self.output_dir.absolute()}")
        if not self.enable_advanced_gates and HAS_ADVANCED_GATES:
            print("💡 Tip: Use --advanced-gates for SSIM/LPIPS quality assessment")
        if self.enable_anti_noise:
            print("🧼 Anti-noise mode: text/gray-safe filters enabled")
        if self.enable_advanced_raster:
            print("🖼️ Advanced raster mode: Photoshop-like pipeline enabled")
        if self.prefer_sharpness:
            print("🔎 Preference: prioritize sharpness in selection")
        print()
        self._print_tools()

    # ---------- tooling ----------
    def _detect_tools(self) -> Dict[str, Optional[str]]:
        tools: Dict[str, Optional[str]] = {"gs": None, "qpdf": None, "pdftk": None}

        # Ghostscript: typical Homebrew and system paths
        candidates = [
            "/opt/homebrew/bin/gs",
            "/usr/local/bin/gs",
            "/opt/homebrew/Cellar/ghostscript/*/bin/gs",
            "ghostscript",
            "gs",
        ]

        for path in candidates:
            if "*" in path:
                import glob
                matches = glob.glob(path)
                if matches:
                    tools["gs"] = matches[0]
                    break
            else:
                p = shutil.which(path) if not Path(path).exists() else path
                if p:
                    tools["gs"] = str(p)
                    break

        tools["qpdf"] = shutil.which("qpdf")
        tools["pdftk"] = shutil.which("pdftk")
        tools["ocrmypdf"] = shutil.which("ocrmypdf")
        return tools

    def _print_tools(self) -> None:
        print("🔧 DETECTED TOOLS:")
        # Ghostscript
        if self.tools["gs"]:
            try:
                r = subprocess.run([self.tools["gs"], "--version"], capture_output=True, text=True)
                v = r.stdout.strip().split("\n")[0] if r.returncode == 0 else "unknown"
                print(f"  ✅ Ghostscript: {self.tools['gs']} (v{v})")
            except Exception:
                print(f"  ⚠️  Ghostscript: {self.tools['gs']} (version unknown)")
        else:
            print("  ❌ Ghostscript: Not found")

        # qpdf
        print(f"  {'✅' if self.tools['qpdf'] else '❌'} qpdf: {self.tools['qpdf'] or 'Not found'}")
        # pdftk (optional)
        print(f"  {'✅' if self.tools['pdftk'] else '❌'} PDFtk: {self.tools['pdftk'] or 'Not found'}")
        # ocrmypdf (optional)
        print(f"  {'✅' if self.tools.get('ocrmypdf') else '❌'} OCRmyPDF: {self.tools.get('ocrmypdf') or 'Not found'}\n")

    # ---------- main flow ----------
    def process_all_pdfs(self) -> List[Dict]:
        pdfs = list(self.input_dir.glob("*.pdf"))
        if not pdfs:
            print("⚠️  No PDF files found in input/")
            return []

        print(f"🔍 Found {len(pdfs)} PDF file(s)")
        results: List[Dict] = []

        for pdf in pdfs:
            print(f"\n🚀 PROCESSING: {pdf.name}")
            print("=" * 60)
            res = self.compress_pdf(pdf)
            results.append(res)
            self._move_processed_file(pdf)

        return results

    def compress_pdf(self, pdf_path: Path) -> Dict:
        original_mb = pdf_path.stat().st_size / (1024 * 1024)
        output_name = self.output_dir / f"{pdf_path.stem}_optimized.pdf"

        print(f"📊 Original size: {original_mb:.2f} MB")

        candidates: List[Tuple[str, Path]] = []

        # Anonymous telemetry: analyze document to get anonymous ID
        doc_id: Optional[str] = None
        if self.enable_telemetry and self.telemetry is not None:
            try:
                doc_id = self.telemetry.analyze_document(pdf_path)
            except Exception as e:
                print(f"⚠️  Telemetry analyze failed: {e}")

        # Content-type detection to auto-enable anti-noise on grayscale/bitonal docs
        self._content_profile = None  # type: ignore
        use_anti_noise = self.enable_anti_noise
        try:
            profile = self._detect_content_profile(pdf_path)
            self._content_profile = profile
            if not use_anti_noise and profile and profile.get('mode') in ('grayscale', 'bitonal'):
                use_anti_noise = True
                print(f"🧠 Auto anti-noise: detected {profile.get('mode')} content")
        except Exception as e:
            # Non-fatal
            self._content_profile = None

        try:
            # Strategy 1: ultra-conservative (qpdf only)
            if self.tools["qpdf"]:
                c1 = self._conservative_qpdf(pdf_path)
                if c1:
                    candidates.append(("conservative", c1))

            # Strategy 2: Ghostscript high-quality
            if self.tools["gs"]:
                c2 = self._high_quality_gs(pdf_path)
                if c2:
                    candidates.append(("high_quality", c2))

            # Strategy 3: Ghostscript balanced
            if self.tools["gs"]:
                c3 = self._balanced_gs(pdf_path)
                if c3:
                    candidates.append(("balanced", c3))

            # Anti-noise strategies prioritize text/gray safety
            if use_anti_noise and self.tools["gs"]:
                c_an1 = self._text_preserve_gs(pdf_path)
                if c_an1:
                    candidates.append(("text_preserve", c_an1))
                c_an2 = self._grayscale_pref_gs(pdf_path)
                if c_an2:
                    candidates.append(("grayscale_pref", c_an2))
                # Denoise/raster strategy when OpenCV is available
                c_dn = self._denoise_raster(pdf_path)
                if c_dn:
                    candidates.append(("denoise_raster", c_dn))

            # Content-aware extra strategies based on detected mode
            prof = getattr(self, '_content_profile', None)
            if self.tools["gs"] and prof:
                mode = prof.get('mode')
                if mode == 'color':
                    c_cts = self._color_text_safe_gs(pdf_path)
                    if c_cts:
                        candidates.append(("color_text_safe", c_cts))
                if mode == 'bitonal':
                    c_bin = self._bitonal_ccitt_raster(pdf_path)
                    if c_bin:
                        candidates.append(("bitonal_ccitt", c_bin))
            # MRC/OCR strategy using OCRmyPDF when applicable
            if self.tools.get("ocrmypdf") and (prof is None or prof.get('mode') in ("grayscale", "bitonal")):
                c_mrc = self._mrc_ocrmypdf(pdf_path)
                if c_mrc:
                    candidates.append(("mrc_ocr", c_mrc))
            # Advanced raster candidate if enabled
            if self.enable_advanced_raster:
                c_adv = self._advanced_raster(pdf_path)
                if c_adv:
                    candidates.append(("advanced_raster", c_adv))
                c_mrcl = self._mrc_light_raster(pdf_path)
                if c_mrcl:
                    candidates.append(("mrc_light_raster", c_mrcl))

            # Strategy 4: Ghostscript aggressive but safe
            if self.tools["gs"]:
                c4 = self._aggressive_safe_gs(pdf_path)
                if c4:
                    candidates.append(("aggressive_safe", c4))

            # Select best result (size vs. quality heuristic + sharpness penalty)
            best = self._select_best_result(pdf_path, candidates)

            # Apply quality gates (PSNR + optional SSIM/LPIPS)
            if self.enable_advanced_gates and self.quality_checker:
                best = self._apply_advanced_quality_gates(pdf_path, candidates, best)
            else:
                best = self._apply_psnr_quality_gate(pdf_path, candidates, best)

            if best:
                shutil.copy2(best["file"], output_name)
                final_mb = output_name.stat().st_size / (1024 * 1024)
                reduction = ((original_mb - final_mb) / original_mb) * 100 if original_mb > 0 else 0.0

                result = {
                    "original_file": pdf_path.name,
                    "final_file": output_name.name,
                    "original_size_mb": original_mb,
                    "final_size_mb": final_mb,
                    "reduction_percent": reduction,
                    "winner_method": best["method"],
                    "quality_score": best.get("score", 0.0),
                    "psnr_db": best.get("psnr_db"),
                    "ssim": best.get("ssim"),
                    "lpips": best.get("lpips"),
                }

                print("\n🎉 COMPRESSION SUCCESS")
                print(f"📊 {original_mb:.2f} MB → {final_mb:.2f} MB ({reduction:.1f}%)")
                print(f"🏆 Winner: {best['method']}")
                if best.get("psnr_db") is not None:
                    print(f"🔎 PSNR: {best['psnr_db']:.2f} dB")
                if best.get("ssim") is not None:
                    print(f"🔎 SSIM: {best['ssim']:.3f}")
                if best.get("lpips") is not None:
                    print(f"🔎 LPIPS: {best['lpips']:.3f}")
            else:
                # Preserve original
                shutil.copy2(pdf_path, output_name)
                result = {
                    "original_file": pdf_path.name,
                    "final_file": output_name.name,
                    "original_size_mb": original_mb,
                    "final_size_mb": original_mb,
                    "reduction_percent": 0.0,
                    "winner_method": "no_change",
                    "quality_score": 100.0,
                }
                print("\n🛡️  No change (preserving original)")

            # cleanup temps
            for method, temp in candidates:
                try:
                    if temp.exists():
                        temp.unlink()
                except Exception:
                    pass

            # Record telemetry result if enabled
            if self.enable_telemetry and self.telemetry is not None and doc_id:
                try:
                    self.telemetry.record_compression_result(doc_id, result)
                except Exception as e:
                    print(f"⚠️  Telemetry record failed: {e}")

            return result

        except Exception as e:
            print(f"❌ Error: {e}")
            error_result = {"original_file": pdf_path.name, "error": str(e)}
            if self.enable_telemetry and self.telemetry is not None and doc_id:
                try:
                    self.telemetry.record_compression_result(doc_id, error_result)
                except Exception:
                    pass
            return error_result

    # ---------- content detection & sharpness ----------
    def _detect_content_profile(self, pdf: Path, pages: int = 2, dpi: int = 120) -> Optional[Dict[str, Any]]:
        """Detect if document is predominantly bitonal, grayscale, or color.

        Heuristic using low-DPI rasterization and simple color metrics.
        """
        if not self.tools.get("gs"):
            return None
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            ok = self._rasterize_pdf_to_pngs(pdf, out, pages, dpi)
            if not ok:
                return None
            try:
                from PIL import Image  # type: ignore
            except Exception:
                Image = None  # type: ignore
            try:
                import numpy as np  # type: ignore
            except Exception:
                np = None  # type: ignore
            try:
                import cv2  # type: ignore
            except Exception:
                cv2 = None  # type: ignore

            if np is None:
                return None

            def read_rgb(p: Path):
                try:
                    if 'cv2' in locals() and cv2 is not None:
                        bgr = cv2.imread(str(p), cv2.IMREAD_COLOR)
                        if bgr is None:
                            return None
                        return bgr[:, :, ::-1]  # BGR->RGB
                    if Image is not None:
                        return np.array(Image.open(p).convert('RGB'))
                except Exception:
                    return None
                return None

            color_count = 0
            gray_like_count = 0
            bitonal_like_count = 0
            total_imgs = 0
            for img_path in sorted(out.glob('page-*.png')):
                rgb = read_rgb(img_path)
                if rgb is None:
                    continue
                total_imgs += 1
                r = rgb[:, :, 0].astype('float32')
                g = rgb[:, :, 1].astype('float32')
                b = rgb[:, :, 2].astype('float32')
                # Colorfulness proxy: mean channel deviation normalized
                colorfulness = float((abs(r - g) + abs(g - b) + abs(b - r)).mean() / (3 * 255.0))
                if colorfulness < 0.02:
                    gray_like_count += 1
                else:
                    color_count += 1
                # Bitonal proxy: majority of pixels near extremes
                gray = (0.299 * r + 0.587 * g + 0.114 * b)
                total = gray.size
                low = (gray < 30).sum()
                high = (gray > 225).sum()
                mid = total - int(low) - int(high)
                if (low + high) / total > 0.85 and mid / total < 0.15:
                    bitonal_like_count += 1

            if total_imgs == 0:
                return None
            mode = 'color'
            if bitonal_like_count / total_imgs >= 0.5:
                mode = 'bitonal'
            elif gray_like_count / total_imgs >= 0.5:
                mode = 'grayscale'
            return {
                'mode': mode,
                'counts': {
                    'color': color_count,
                    'grayscale_like': gray_like_count,
                    'bitonal_like': bitonal_like_count,
                    'total': total_imgs,
                }
            }

    def _compute_sharpness_metric(self, pdf: Path, pages: int = 2, dpi: int = 150) -> Optional[float]:
        """Compute average sharpness via Laplacian variance (or gradient variance fallback)."""
        if not self.tools.get("gs"):
            return None
        with tempfile.TemporaryDirectory() as d:
            outdir = Path(d)
            if not self._rasterize_pdf_to_pngs(pdf, outdir, pages, dpi):
                return None
            try:
                from PIL import Image  # type: ignore
            except Exception:
                Image = None  # type: ignore
            try:
                import numpy as np  # type: ignore
            except Exception:
                np = None  # type: ignore
            try:
                import cv2  # type: ignore
            except Exception:
                cv2 = None  # type: ignore
            if np is None:
                return None
            vals: List[float] = []
            for p in sorted(outdir.glob('page-*.png')):
                # grayscale array
                arr = self._read_image_to_array(p, Image, np, cv2)
                if arr is None:
                    continue
                try:
                    if cv2 is not None:
                        lap = cv2.Laplacian(arr, cv2.CV_32F)
                        vals.append(float(lap.var()))
                    else:
                        # Fallback: gradient magnitude variance
                        gx = np.diff(arr.astype('float32'), axis=1)
                        gy = np.diff(arr.astype('float32'), axis=0)
                        mag = np.sqrt(gx[:, :-1] ** 2 + gy[:-1, :] ** 2)
                        vals.append(float(mag.var()))
                except Exception:
                    continue
            if not vals:
                return None
            return float(sum(vals) / len(vals))

    # ---------- strategies ----------
    def _conservative_qpdf(self, pdf: Path) -> Optional[Path]:
        print("🛡️  Conservative compression (qpdf)…")
        if not self.tools.get("qpdf"):
            return None
        tmp = Path(tempfile.mktemp(suffix="_conservative.pdf"))
        cmd = [
            self.tools["qpdf"],
            "--optimize-images",
            "--compress-streams=y",
            "--object-streams=generate",
            str(pdf),
            str(tmp),
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and tmp.exists():
                print(f"  ✅ conservative: {tmp.stat().st_size / (1024*1024):.2f} MB")
                return tmp
        except Exception as e:
            print(f"  ❌ conservative error: {e}")
        return None

    def _text_preserve_gs(self, pdf: Path) -> Optional[Path]:
        """Ghostscript strategy tuned to minimize compression artifacts on text and grayscale content.

        - Prefer lossless for gray images (Flate)
        - Use CCITT for monochrome (bitonal) when possible
        - Moderate JPEG quality for color images
        - Keep higher resolution for mono/gray to avoid stair-stepping
        """
        print("🧼 Text-preserve Ghostscript…")
        if not self.tools.get("gs"):
            return None
        tmp = Path(tempfile.mktemp(suffix="_textpreserve.pdf"))
        cmd = [
            self.tools["gs"],
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.6",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            # Avoid auto filters that may pick noisy JPEG for gray
            "-dAutoFilterGrayImages=false",
            "-dGrayImageFilter=/FlateEncode",
            # Prefer CCITT for mono (bitonal) content
            "-dAutoFilterMonoImages=false",
            "-dMonoImageFilter=/CCITTFaxEncode",
            "-dMonoImageDownsampleType=/Subsample",
            "-dMonoImageResolution=600",
            # Color images with moderate JPEG quality
            "-dAutoFilterColorImages=false",
            "-dColorImageFilter=/DCTEncode",
            "-dJPEGQ=85",
            "-dColorImageDownsampleType=/Bicubic",
            "-dColorImageResolution=200",
            # Gray images kept higher res, helps text scans
            "-dGrayImageDownsampleType=/Bicubic",
            "-dGrayImageResolution=300",
            # Preserve annotations and fonts
            "-dEmbedAllFonts=true",
            "-dSubsetFonts=true",
            "-dCompressFonts=false",
            "-dPreserveAnnots=true",
            "-dDetectDuplicateImages=true",
            f"-sOutputFile={tmp}",
            str(pdf),
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and tmp.exists():
                print(f"  ✅ text_preserve: {tmp.stat().st_size / (1024*1024):.2f} MB")
                return tmp
        except Exception as e:
            print(f"  ❌ text_preserve error: {e}")
        return None

    def _grayscale_pref_gs(self, pdf: Path) -> Optional[Path]:
        """Ghostscript strategy that prefers grayscale to suppress chroma noise for near-monochrome docs.

        Uses JPEG (DCTEncode) with high quality for grayscale to prevent huge size increase.
        """
        print("🧼 Grayscale-preferred Ghostscript…")
        if not self.tools.get("gs"):
            return None
        tmp = Path(tempfile.mktemp(suffix="_grayscale.pdf"))
        cmd = [
            self.tools["gs"],
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.6",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            # Suggest grayscale conversion for output
            "-sColorConversionStrategy=Gray",
            "-dProcessColorModel=/DeviceGray",
            # Filters
            "-dAutoFilterGrayImages=false",
            "-dGrayImageFilter=/DCTEncode",
            "-dJPEGQ=90",
            "-dGrayImageDownsampleType=/Bicubic",
            "-dGrayImageResolution=300",
            # Keep mono CCITT
            "-dAutoFilterMonoImages=false",
            "-dMonoImageFilter=/CCITTFaxEncode",
            "-dMonoImageResolution=600",
            # Preserve fonts/annots
            "-dEmbedAllFonts=true",
            "-dSubsetFonts=true",
            "-dCompressFonts=false",
            "-dPreserveAnnots=true",
            f"-sOutputFile={tmp}",
            str(pdf),
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and tmp.exists():
                print(f"  ✅ grayscale_pref: {tmp.stat().st_size / (1024*1024):.2f} MB")
                return tmp
        except Exception as e:
            print(f"  ❌ grayscale_pref error: {e}")
        return None

    def _color_text_safe_gs(self, pdf: Path) -> Optional[Path]:
        """Ghostscript strategy for color documents with small colored text/graphics.

        - Avoid downsampling color images
        - Use high JPEG quality to reduce chroma artifacts
        - Keep gray/mono settings from text-preserve where safe
        """
        print("🧼 Color-text-safe Ghostscript…")
        if not self.tools.get("gs"):
            return None
        tmp = Path(tempfile.mktemp(suffix="_color_text_safe.pdf"))
        cmd = [
            self.tools["gs"],
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.6",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            # Color images: no downsample, high quality JPEG
            "-dDownsampleColorImages=false",
            "-dAutoFilterColorImages=false",
            "-dColorImageFilter=/DCTEncode",
            "-dJPEGQ=95",
            # Gray images: lossless to keep text edges
            "-dAutoFilterGrayImages=false",
            "-dGrayImageFilter=/FlateEncode",
            "-dGrayImageDownsampleType=/Bicubic",
            "-dGrayImageResolution=300",
            # Mono: CCITT
            "-dAutoFilterMonoImages=false",
            "-dMonoImageFilter=/CCITTFaxEncode",
            "-dMonoImageResolution=600",
            # Preserve fonts/annots
            "-dEmbedAllFonts=true",
            "-dSubsetFonts=true",
            "-dCompressFonts=false",
            "-dPreserveAnnots=true",
            "-dDetectDuplicateImages=true",
            f"-sOutputFile={tmp}",
            str(pdf),
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and tmp.exists():
                print(f"  ✅ color_text_safe: {tmp.stat().st_size / (1024*1024):.2f} MB")
                return tmp
        except Exception as e:
            print(f"  ❌ color_text_safe error: {e}")
        return None

    def _bitonal_ccitt_raster(self, pdf: Path, dpi: int = 300) -> Optional[Path]:
        """Rasterize pages to 1-bit CCITT G4 and rebuild a PDF.

        Heavy-handed but effective for receipts/bitonal scans suffering from noise.
        """
        print("🧼 Bitonal CCITT raster…")
        if not self.tools.get("gs"):
            return None
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            tiff_pattern = str(tdir / "page-%03d.tif")
            # Step 1: PDF -> TIFF G4 (1-bit)
            cmd1 = [
                self.tools["gs"],
                "-sDEVICE=tiffg4",
                f"-r{dpi}",
                "-dNOPAUSE",
                "-dBATCH",
                "-dQUIET",
                f"-sOutputFile={tiff_pattern}",
                str(pdf),
            ]
            try:
                r1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=420)
                if r1.returncode != 0 or not list(tdir.glob('page-*.tif')):
                    return None
            except Exception:
                return None

            # Step 2: TIFFs -> PDF
            out_pdf = Path(tempfile.mktemp(suffix="_bitonal.pdf"))
            # Use Ghostscript to assemble images into PDF
            # Note: order sorted to maintain page order
            tiffs = sorted(tdir.glob('page-*.tif'))
            # Ghostscript accepts multiple inputs; we can pass them in order
            cmd2 = [self.tools["gs"], "-sDEVICE=pdfwrite", "-dNOPAUSE", "-dBATCH", "-dQUIET",
                    f"-sOutputFile={out_pdf}"] + [str(p) for p in tiffs]
            try:
                r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=420)
                if r2.returncode == 0 and out_pdf.exists():
                    print(f"  ✅ bitonal_ccitt: {out_pdf.stat().st_size / (1024*1024):.2f} MB")
                    return out_pdf
            except Exception as e:
                print(f"  ❌ bitonal_ccitt error: {e}")
            return None

    def _high_quality_gs(self, pdf: Path) -> Optional[Path]:
        print("💎 High-quality Ghostscript…")
        if not self.tools.get("gs"):
            return None
        tmp = Path(tempfile.mktemp(suffix="_hq.pdf"))
        cmd = [
            self.tools["gs"],
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.7",
            "-dPDFSETTINGS=/prepress",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            "-dColorImageResolution=300",
            "-dGrayImageResolution=300",
            "-dMonoImageResolution=1200",
            "-dColorImageDownsampleThreshold=2.0",
            "-dGrayImageDownsampleThreshold=2.0",
            "-dMonoImageDownsampleThreshold=2.0",
            "-dOptimize=true",
            "-dEmbedAllFonts=true",
            "-dSubsetFonts=true",
            "-dCompressFonts=false",
            "-dPreserveAnnots=true",
            f"-sOutputFile={tmp}",
            str(pdf),
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and tmp.exists():
                print(f"  ✅ high_quality: {tmp.stat().st_size / (1024*1024):.2f} MB")
                return tmp
        except Exception as e:
            print(f"  ❌ high_quality error: {e}")
        return None

    def _balanced_gs(self, pdf: Path) -> Optional[Path]:
        print("⚖️  Balanced Ghostscript…")
        if not self.tools.get("gs"):
            return None
        tmp = Path(tempfile.mktemp(suffix="_balanced.pdf"))
        cmd = [
            self.tools["gs"],
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.6",
            "-dPDFSETTINGS=/printer",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            "-dColorImageResolution=200",
            "-dGrayImageResolution=200",
            "-dMonoImageResolution=600",
            "-dColorImageDownsampleThreshold=1.5",
            "-dOptimize=true",
            "-dEmbedAllFonts=true",
            "-dSubsetFonts=true",
            f"-sOutputFile={tmp}",
            str(pdf),
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and tmp.exists():
                print(f"  ✅ balanced: {tmp.stat().st_size / (1024*1024):.2f} MB")
                return tmp
        except Exception as e:
            print(f"  ❌ balanced error: {e}")
        return None

    def _aggressive_safe_gs(self, pdf: Path) -> Optional[Path]:
        print("🎯 Aggressive-safe Ghostscript…")
        if not self.tools.get("gs"):
            return None
        tmp = Path(tempfile.mktemp(suffix="_aggressive.pdf"))
        cmd = [
            self.tools["gs"],
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.5",
            "-dPDFSETTINGS=/ebook",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            "-dColorImageResolution=150",
            "-dGrayImageResolution=150",
            "-dMonoImageResolution=600",
            "-dColorImageDownsampleThreshold=1.2",
            "-dOptimize=true",
            "-dEmbedAllFonts=true",
            "-dSubsetFonts=true",
            "-dDetectDuplicateImages=true",
            f"-sOutputFile={tmp}",
            str(pdf),
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and tmp.exists():
                print(f"  ✅ aggressive_safe: {tmp.stat().st_size / (1024*1024):.2f} MB")
                return tmp
        except Exception as e:
            print(f"  ❌ aggressive_safe error: {e}")
        return None

    def _mrc_ocrmypdf(self, pdf: Path) -> Optional[Path]:
        """MRC/OCR pipeline via OCRmyPDF with JBIG2 and image optimization.

        Targets scanned/image PDFs; skips OCR on pages with existing text.
        Requires ocrmypdf installed.
        """
        print("🧠 MRC/OCR via OCRmyPDF…")
        if not self.tools.get("ocrmypdf"):
            return None
        tmp = Path(tempfile.mktemp(suffix="_mrc.pdf"))
        cmd = [
            self.tools["ocrmypdf"],
            "--optimize", "3",
            "--skip-text",
            "--fast-web-view", "1",
            "--tesseract-timeout", "120",
            "--jpeg-quality", "85",
            "--png-quality", "60",
            str(pdf),
            str(tmp),
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            if r.returncode == 0 and tmp.exists():
                print(f"  ✅ mrc_ocr: {tmp.stat().st_size / (1024*1024):.2f} MB")
                return tmp
            else:
                if r.stderr:
                    print(f"  ❌ mrc_ocr error: {r.stderr.splitlines()[-1]}")
        except Exception as e:
            print(f"  ❌ mrc_ocr error: {e}")
        return None

    # ---------- selection ----------
    def _select_best_result(self, original: Path, candidates: List[Tuple[str, Path]]) -> Optional[Dict]:
        if not candidates:
            return None
        original_size = original.stat().st_size
        best: Optional[Dict] = None
        best_score = -1.0

        print("\n🔍 Evaluating results:")
        # Precompute original sharpness to normalize penalties
        try:
            base_sharp = self._compute_sharpness_metric(original) or None
        except Exception:
            base_sharp = None

        for method, f in candidates:
            if not f.exists():
                continue
            size = f.stat().st_size
            reduction = ((original_size - size) / original_size) * 100 if original_size > 0 else 0.0

            # heuristic scoring (favor moderate reductions; avoid over-aggressive)
            if reduction < 5:
                score = 70 + reduction
            elif 5 <= reduction <= 50:
                score = 80 + (reduction - 5) / 45 * 20
            elif 50 < reduction <= 80:
                score = 95 - (reduction - 50) / 30 * 15
            else:
                score = 60 - (reduction - 80)

            if method == "conservative":
                score += 10
            elif method == "high_quality":
                score += 8
            elif method == "balanced":
                score += 5

            if reduction < 0:
                score = 0

            # Sharpness penalty: penalize blurred outputs vs original
            try:
                cand_sharp = self._compute_sharpness_metric(f) or None
            except Exception:
                cand_sharp = None
            if base_sharp is not None and cand_sharp is not None:
                # If candidate sharpness drops significantly vs original, penalize
                # Normalize penalty magnitude
                drop_ratio = max(0.0, float(base_sharp - cand_sharp) / (base_sharp + 1e-6))
                penalty = min(20.0, drop_ratio * 40.0)  # up to -20 points
                if penalty > 0:
                    score -= penalty
                # If user prefers sharpness, reward candidates that are sharper
                if self.prefer_sharpness and cand_sharp > base_sharp:
                    gain_ratio = float(cand_sharp - base_sharp) / (base_sharp + 1e-6)
                    score += min(10.0, gain_ratio * 20.0)

            # Content-aware boost: prefer anti-noise methods for grayscale/bitonal
            prof = getattr(self, '_content_profile', None)
            if prof and prof.get('mode') in ('grayscale', 'bitonal'):
                if method in ("text_preserve", "grayscale_pref", "conservative", "bitonal_ccitt"):
                    score += 6

            # Boost advanced raster candidates slightly when enabled
            if self.enable_advanced_raster and method in ("advanced_raster", "mrc_light_raster"):
                score += 2.5

            print(f"  📄 {method}: {size/(1024*1024):.2f} MB ({reduction:+.1f}%) - score: {score:.1f}")
            if score > best_score:
                best_score = score
                best = {"method": method, "file": f, "score": score, "reduction": reduction}

        return best

    # ---------- perceptual quality gates ----------
    def _apply_advanced_quality_gates(
        self,
        original: Path,
        candidates: List[Tuple[str, Path]],
        best: Optional[Dict],
    ) -> Optional[Dict]:
        """Apply advanced quality gates (PSNR + SSIM + LPIPS)."""
        if not best or not self.quality_checker:
            return best

        try:
            passed, metrics = self.quality_checker.evaluate_quality(original, best["file"])
            
            # Add metrics to result
            if metrics.psnr is not None:
                best["psnr_db"] = metrics.psnr
            if metrics.ssim is not None:
                best["ssim"] = metrics.ssim  
            if metrics.lpips is not None:
                best["lpips"] = metrics.lpips

            print(f"\n🔬 Advanced Quality Gates:")
            if metrics.psnr is not None:
                status = "✅" if metrics.psnr_passed else "❌"
                print(f"   PSNR: {metrics.psnr:.2f} dB {status}")
            if metrics.ssim is not None:
                status = "✅" if metrics.ssim_passed else "❌"
                print(f"   SSIM: {metrics.ssim:.3f} {status}")
            if metrics.lpips is not None:
                status = "✅" if metrics.lpips_passed else "❌"
                print(f"   LPIPS: {metrics.lpips:.3f} {status}")
            
            print(f"   Overall: {'✅ PASS' if passed else '❌ FAIL'}")

            if passed:
                best["score"] = max(best.get("score", 0.0), 95.0)
                return best
            else:
                print("⚠️  Failed quality gates, trying safer alternatives…")
                return self._try_safer_alternatives(original, candidates, metrics)

        except Exception as e:
            print(f"⚠️  Quality gate evaluation failed: {e}")
            # Fall back to PSNR-only
            return self._apply_psnr_quality_gate(original, candidates, best)

    def _try_safer_alternatives(
        self, 
        original: Path, 
        candidates: List[Tuple[str, Path]], 
        failed_metrics
    ) -> Optional[Dict]:
        """Try safer compression alternatives when quality gates fail."""
        for alt in ("high_quality", "conservative"):
            alt_file = next((p for m, p in candidates if m == alt and p.exists()), None)
            if not alt_file:
                continue
                
            try:
                passed, alt_metrics = self.quality_checker.evaluate_quality(original, alt_file)
                if passed:
                    print(f"✅ Alternative '{alt}' passed quality gates")
                    result = {
                        "method": alt, 
                        "file": alt_file, 
                        "score": 96.0, 
                        "reduction": 0.0
                    }
                    
                    # Add metrics
                    if alt_metrics.psnr is not None:
                        result["psnr_db"] = alt_metrics.psnr
                    if alt_metrics.ssim is not None:
                        result["ssim"] = alt_metrics.ssim
                    if alt_metrics.lpips is not None:
                        result["lpips"] = alt_metrics.lpips
                        
                    return result
            except Exception as e:
                print(f"⚠️  Error testing alternative '{alt}': {e}")
                continue

        print("🛡️  No alternative passed quality gates; preserving original.")
        return None

    def _apply_psnr_quality_gate(
        self,
        original: Path,
        candidates: List[Tuple[str, Path]],
        best: Optional[Dict],
    ) -> Optional[Dict]:
        if not best:
            return None

        # Content-aware PSNR threshold
        THRESHOLD_DB = 35.0
        prof = getattr(self, '_content_profile', None)
        if prof:
            if prof.get('mode') == 'bitonal':
                THRESHOLD_DB = 30.0
            elif prof.get('mode') == 'grayscale':
                THRESHOLD_DB = 33.0
        try:
            psnr = self._compute_average_psnr(original, best["file"])
        except Exception:
            psnr = None

        if psnr is None:
            return best

        print(f"\n🔎 Quality gate (PSNR): {psnr:.2f} dB (threshold {THRESHOLD_DB} dB)")
        if psnr >= THRESHOLD_DB:
            best["score"] = max(best.get("score", 0.0), 95.0)
            best["psnr_db"] = psnr
            return best

        print("⚠️  Below PSNR threshold, trying safer alternatives…")
        for alt in ("high_quality", "conservative"):
            alt_file = next((p for m, p in candidates if m == alt and p.exists()), None)
            if not alt_file:
                continue
            alt_psnr = None
            try:
                alt_psnr = self._compute_average_psnr(original, alt_file)
            except Exception:
                pass
            if alt_psnr is not None and alt_psnr >= THRESHOLD_DB:
                print(f"✅ Alternative '{alt}' passed with {alt_psnr:.2f} dB")
                return {"method": alt, "file": alt_file, "score": 96.0, "reduction": 0.0, "psnr_db": alt_psnr}

        print("🛡️  No alternative passed the quality gate; preserving original.")
        return None

    def _compute_average_psnr(self, pdf_a: Path, pdf_b: Path, pages: int = 3, dpi: int = 200) -> Optional[float]:
        if not self.tools.get("gs"):
            return None
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            out1 = Path(d1)
            out2 = Path(d2)
            ok1 = self._rasterize_pdf_to_pngs(pdf_a, out1, pages, dpi)
            ok2 = self._rasterize_pdf_to_pngs(pdf_b, out2, pages, dpi)
            if not ok1 or not ok2:
                return None
            pairs: List[Tuple[Path, Path]] = []
            for i in range(1, pages + 1):
                p1 = out1 / f"page-{i:03d}.png"
                p2 = out2 / f"page-{i:03d}.png"
                if p1.exists() and p2.exists():
                    pairs.append((p1, p2))
            if not pairs:
                return None

            try:
                from PIL import Image  # type: ignore
            except Exception:
                Image = None  # type: ignore
            try:
                import numpy as np  # type: ignore
            except Exception:
                np = None  # type: ignore
            try:
                import cv2  # type: ignore
            except Exception:
                cv2 = None  # type: ignore

            if 'np' not in locals() or np is None:  # type: ignore
                return None

            psnrs: List[float] = []
            for a, b in pairs:
                arr_a = self._read_image_to_array(a, Image, np, cv2)
                arr_b = self._read_image_to_array(b, Image, np, cv2)
                if arr_a is None or arr_b is None:
                    continue
                h = min(arr_a.shape[0], arr_b.shape[0])
                w = min(arr_a.shape[1], arr_b.shape[1])
                arr_a = arr_a[:h, :w]
                arr_b = arr_b[:h, :w]
                mse = float(np.mean((arr_a.astype('float32') - arr_b.astype('float32')) ** 2))
                if mse == 0:
                    psnrs.append(100.0)
                else:
                    psnr = 20 * math.log10(255.0) - 10 * math.log10(mse)
                    psnrs.append(psnr)
            if not psnrs:
                return None
            return float(sum(psnrs) / len(psnrs))

    def _read_image_to_array(self, path: Path, Image, np, cv2) -> Optional[Any]:
        try:
            if cv2 is not None:
                return cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if Image is not None and np is not None:
                return np.array(Image.open(path).convert('L'))
        except Exception:
            return None
        return None

    def _rasterize_pdf_to_pngs(self, pdf: Path, outdir: Path, pages: int, dpi: int) -> bool:
        out_pattern = str(outdir / 'page-%03d.png')
        cmd = [
            self.tools["gs"],
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=png16m",
            f"-r{dpi}",
            "-dTextAlphaBits=4",
            "-dGraphicsAlphaBits=4",
            "-dFirstPage=1",
            f"-dLastPage={pages}",
            f"-sOutputFile={out_pattern}",
            str(pdf),
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            return len(list(outdir.glob('page-*.png'))) > 0
        except Exception:
            return False

    def _rasterize_pdf_full_to_pngs(self, pdf: Path, outdir: Path, dpi: int = 300) -> bool:
        """Rasterize all pages to PNG RGB using Ghostscript."""
        out_pattern = str(outdir / 'page-%03d.png')
        cmd = [
            self.tools["gs"],
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=png16m",
            f"-r{dpi}",
            "-dTextAlphaBits=4",
            "-dGraphicsAlphaBits=4",
            f"-sOutputFile={out_pattern}",
            str(pdf),
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return len(list(outdir.glob('page-*.png'))) > 0
        except Exception:
            return False

    def _assemble_images_to_pdf(self, images: List[Path]) -> Optional[Path]:
        """Assemble a list of images into a PDF using Ghostscript."""
        if not images:
            return None
        out_pdf = Path(tempfile.mktemp(suffix="_images.pdf"))
        cmd = [
            self.tools["gs"],
            "-sDEVICE=pdfwrite",
            "-dNOPAUSE",
            "-dBATCH",
            "-dQUIET",
            "-dAutoRotatePages=/None",
            f"-sOutputFile={out_pdf}",
        ] + [str(p) for p in images]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            # Check if output file exists and has content, even if return code is non-zero
            # (Ghostscript sometimes reports warnings as errors but still produces valid output)
            if out_pdf.exists() and out_pdf.stat().st_size > 0:
                return out_pdf
        except Exception:
            return None
        return None

    def _denoise_raster(self, pdf: Path) -> Optional[Path]:
        """Rasterize, denoise (speckle/chroma), sharpen and rebuild PDF.

        Requires numpy + opencv; skips gracefully if unavailable.
        """
        try:
            import numpy as np  # type: ignore
            import cv2  # type: ignore
            from PIL import Image  # type: ignore
        except Exception:
            return None

        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as to:
            src_dir = Path(td)
            out_dir = Path(to)
            if not self._rasterize_pdf_full_to_pngs(pdf, src_dir, dpi=300):
                return None

            prof = getattr(self, '_content_profile', None)
            mode = prof.get('mode') if prof else None

            processed: List[Path] = []
            for png in sorted(src_dir.glob('page-*.png')):
                try:
                    img = cv2.imread(str(png), cv2.IMREAD_COLOR)
                    if img is None:
                        continue
                    if mode == 'bitonal':
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        blur = cv2.GaussianBlur(gray, (3, 3), 0)
                        th = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                   cv2.THRESH_BINARY, 19, 9)
                        # Optional small opening to remove speckle
                        kernel = np.ones((2, 2), np.uint8)
                        th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel)
                        out = th
                        save_gray = True
                    elif mode == 'grayscale':
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        dn = cv2.fastNlMeansDenoising(gray, None, h=8, templateWindowSize=7, searchWindowSize=21)
                        # Unsharp mask
                        g = cv2.GaussianBlur(dn, (0, 0), 0.8)
                        us = cv2.addWeighted(dn, 1.5, g, -0.5, 0)
                        out = us
                        save_gray = True
                    else:
                        # color: chroma denoise + luma sharpen
                        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
                        y, cr, cb = cv2.split(ycrcb)
                        cr = cv2.fastNlMeansDenoising(cr, None, h=5)
                        cb = cv2.fastNlMeansDenoising(cb, None, h=5)
                        # Sharpen luma
                        g = cv2.GaussianBlur(y, (0, 0), 0.8)
                        y = cv2.addWeighted(y, 1.4, g, -0.4, 0)
                        ycrcb = cv2.merge([y, cr, cb])
                        out = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
                        save_gray = False

                    out_path = out_dir / png.name
                    if save_gray:
                        cv2.imwrite(str(out_path), out)
                    else:
                        cv2.imwrite(str(out_path), out, [cv2.IMWRITE_PNG_COMPRESSION, 3])
                    processed.append(out_path)
                except Exception:
                    continue

            if not processed:
                return None
            # Assemble to PDF
            return self._assemble_images_to_pdf(processed)

    def _mrc_light_raster(self, pdf: Path) -> Optional[Path]:
        """MRC-like raster pipeline with text-aware sharpening and background smoothing.

        Steps per page:
        - Rasterize at higher DPI (e.g., 400), then process and downsample to 300 for crisp edges.
        - Detect text regions via adaptive threshold + morphology; build a foreground (text) mask.
        - Smooth background (NLMeans/Bilateral), mild quantization for color pages.
        - Apply strong unsharp to text regions only; composite onto background in Y channel.
        - Optional palette/grayscale quantization to reduce size while preserving edges.

        Requires numpy + opencv (+Pillow for palette/grayscale quantization). Skips if unavailable.
        """
        try:
            import numpy as np  # type: ignore
            import cv2  # type: ignore
            from PIL import Image  # type: ignore
        except Exception:
            return None

        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as to:
            src_dir = Path(td)
            out_dir = Path(to)
            # Supersample to 400 DPI for processing
            if not self._rasterize_pdf_full_to_pngs(pdf, src_dir, dpi=400):
                return None

            prof = getattr(self, '_content_profile', None)
            mode = prof.get('mode') if prof else None

            def unsharp(arr: 'np.ndarray', sigma: float = 0.8, amount: float = 1.5) -> 'np.ndarray':
                g = cv2.GaussianBlur(arr, (0, 0), sigma)
                us = cv2.addWeighted(arr, 1 + amount, g, -amount, 0)
                return np.clip(us, 0, 255).astype(np.uint8)

            processed: List[Path] = []
            for png in sorted(src_dir.glob('page-*.png')):
                bgr = cv2.imread(str(png), cv2.IMREAD_COLOR)
                if bgr is None:
                    continue
                h, w = bgr.shape[:2]

                # Text mask from grayscale adaptive threshold
                gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
                gblur = cv2.GaussianBlur(gray, (3, 3), 0)
                th = cv2.adaptiveThreshold(gblur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY_INV, 25, 10)
                # Morph refine: remove noise, connect strokes
                kernel = np.ones((2, 2), np.uint8)
                th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=1)
                th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=1)

                # Remove tiny blobs
                num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(th, connectivity=8)
                areas = stats[1:, cv2.CC_STAT_AREA] if num_labels > 1 else []
                clean = np.zeros_like(th)
                if num_labels > 1:
                    for i in range(1, num_labels):
                        if stats[i, cv2.CC_STAT_AREA] >= max(16, (h * w) * 0.00002):
                            clean[labels == i] = 255
                else:
                    clean = th

                text_mask = clean

                # Background smoothing
                try:
                    bg = cv2.fastNlMeansDenoisingColored(bgr, None, h=3, hColor=5, templateWindowSize=7, searchWindowSize=21)
                except Exception:
                    bg = cv2.bilateralFilter(bgr, d=7, sigmaColor=40, sigmaSpace=7)

                # Luma sharpen only under text mask
                ycrcb = cv2.cvtColor(bg, cv2.COLOR_BGR2YCrCb)
                y, cr, cb = cv2.split(ycrcb)
                y_sharp = y.copy()
                y_text = unsharp(y, sigma=0.7, amount=1.8)
                y_sharp[text_mask > 0] = y_text[text_mask > 0]
                ycrcb = cv2.merge([y_sharp, cr, cb])
                comp_bgr = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

                # Downsample to 300 DPI (keep aspect) for smaller size but crisp edges from supersampling
                scale = 300.0 / 400.0
                comp_bgr = cv2.resize(comp_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LANCZOS4)

                # Quantization: grayscale docs -> 16-level grayscale palette PNG; color -> 128-color adaptive palette
                out_path = out_dir / png.name
                if mode in ('grayscale', 'bitonal'):
                    pil_img = Image.fromarray(cv2.cvtColor(comp_bgr, cv2.COLOR_BGR2RGB)).convert('L')
                    # Build 16-level grayscale palette
                    pal_img = pil_img.convert('P', palette=Image.Palette.ADAPTIVE, colors=16, dither=Image.FLOYDSTEINBERG)
                    pal_img.save(out_path, format='PNG', optimize=True)
                else:
                    try:
                        pil_img = Image.fromarray(cv2.cvtColor(comp_bgr, cv2.COLOR_BGR2RGB))
                        pal = pil_img.convert('P', palette=Image.Palette.ADAPTIVE, colors=128, dither=Image.FLOYDSTEINBERG)
                        pal.save(out_path, format='PNG', optimize=True)
                    except Exception:
                        # Fallback PNG
                        cv2.imwrite(str(out_path), comp_bgr, [cv2.IMWRITE_PNG_COMPRESSION, 3])

                processed.append(out_path)

            if not processed:
                return None
            return self._assemble_images_to_pdf(processed)
    def _advanced_raster(self, pdf: Path) -> Optional[Path]:
        """Advanced raster pipeline: background normalization, CLAHE, denoise, unsharp,
        and optional color quantization, then reassemble to PDF.

        Requires numpy + opencv (+Pillow for palette quantization). Skips if unavailable.
        """
        try:
            import numpy as np  # type: ignore
            import cv2  # type: ignore
            from PIL import Image  # type: ignore
        except Exception:
            return None

        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as to:
            src_dir = Path(td)
            out_dir = Path(to)
            if not self._rasterize_pdf_full_to_pngs(pdf, src_dir, dpi=300):
                return None

            prof = getattr(self, '_content_profile', None)
            mode = prof.get('mode') if prof else None

            def unsharp(gray: 'np.ndarray', sigma: float = 1.0, amount: float = 1.5) -> 'np.ndarray':
                g = cv2.GaussianBlur(gray, (0, 0), sigma)
                us = cv2.addWeighted(gray, 1 + amount, g, -amount, 0)
                return np.clip(us, 0, 255).astype(np.uint8)

            def clahe(gray: 'np.ndarray', clip: float = 2.0, tiles: Tuple[int, int] = (8, 8)) -> 'np.ndarray':
                c = cv2.createCLAHE(clipLimit=clip, tileGridSize=tiles)
                return c.apply(gray)

            processed: List[Path] = []
            for png in sorted(src_dir.glob('page-*.png')):
                img = cv2.imread(str(png), cv2.IMREAD_COLOR)
                if img is None:
                    continue

                if mode == 'bitonal':
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    norm = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
                    th = cv2.adaptiveThreshold(norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                               cv2.THRESH_BINARY, 21, 8)
                    kernel = np.ones((2, 2), np.uint8)
                    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel)
                    out = th
                    save_mode = 'gray'
                elif mode == 'grayscale':
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    bg = cv2.GaussianBlur(gray, (0, 0), 15.0)
                    norm = cv2.addWeighted(gray, 1.25, bg, -0.25, 0)
                    dn = cv2.fastNlMeansDenoising(norm, None, h=7, templateWindowSize=7, searchWindowSize=21)
                    eq = clahe(dn, clip=2.0)
                    out = unsharp(eq, sigma=0.8, amount=1.3)
                    save_mode = 'gray'
                else:
                    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
                    y, cr, cb = cv2.split(ycrcb)
                    cr = cv2.fastNlMeansDenoising(cr, None, h=4)
                    cb = cv2.fastNlMeansDenoising(cb, None, h=4)
                    y = unsharp(y, sigma=0.8, amount=0.8)
                    ycrcb = cv2.merge([y, cr, cb])
                    out_bgr = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
                    # Try palette quantization to ~128 colors with dithering
                    try:
                        pil_img = Image.fromarray(cv2.cvtColor(out_bgr, cv2.COLOR_BGR2RGB))
                        pal = pil_img.convert('P', palette=Image.Palette.ADAPTIVE, colors=128, dither=Image.FLOYDSTEINBERG)
                        out_rgb = pal.convert('RGB')
                        out_bgr = cv2.cvtColor(np.array(out_rgb), cv2.COLOR_RGB2BGR)
                    except Exception:
                        pass
                    out = out_bgr
                    save_mode = 'color'

                out_path = out_dir / png.name
                if save_mode == 'gray':
                    cv2.imwrite(str(out_path), out, [cv2.IMWRITE_PNG_COMPRESSION, 3])
                else:
                    cv2.imwrite(str(out_path), out, [cv2.IMWRITE_PNG_COMPRESSION, 3])
                processed.append(out_path)

            if not processed:
                return None
            return self._assemble_images_to_pdf(processed)

    # ---------- utils ----------
    def _move_processed_file(self, pdf: Path) -> None:
        processed_dir = self.input_dir / "processed"
        processed_dir.mkdir(exist_ok=True)
        dest = processed_dir / pdf.name
        shutil.move(str(pdf), str(dest))
        print(f"📁 Moved to: {dest}")

    def show_summary(self, results: List[Dict]) -> None:
        if not results:
            return
        print("\n" + "=" * 70)
        print("🚀 FINAL SUMMARY")
        print("=" * 70)
        total_o = 0.0
        total_f = 0.0
        ok = 0
        for r in results:
            if "error" in r:
                print(f"❌ {r['original_file']}: {r['error']}")
                continue
            ok += 1
            total_o += r["original_size_mb"]
            total_f += r["final_size_mb"]
            print(f"✅ {r['original_file']}")
            print(f"   📊 {r['original_size_mb']:.2f} MB → {r['final_size_mb']:.2f} MB ({r['reduction_percent']:.1f}%)")
            print(f"   🏆 {r['winner_method']} (quality: {r.get('quality_score', 0):.1f}/100)")
        if ok > 0 and total_o > 0:
            reduction_total = ((total_o - total_f) / total_o) * 100
            print("\n🎯 TOTALS:")
            print(f"   📁 Processed: {ok}/{len(results)}")
            print(f"   📊 {total_o:.2f} MB → {total_f:.2f} MB ({reduction_total:.1f}%)")
            print(f"   💾 Saved: {total_o - total_f:.2f} MB")


def main() -> None:
    import argparse
    
    parser = argparse.ArgumentParser(
        description="PDF Ultra Compressor v1 - Quality-first PDF optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compressor.py                    # Basic compression with PSNR gate
  python compressor.py --advanced-gates   # Enable SSIM/LPIPS quality gates
  python compressor.py --input ~/docs --output ~/compressed
        """
    )
    
    parser.add_argument("--input", "-i", default="input",
                       help="Input directory containing PDFs (default: input)")
    parser.add_argument("--output", "-o", default="output", 
                       help="Output directory for compressed PDFs (default: output)")
    parser.add_argument("--advanced-gates", action="store_true",
                       help="Enable advanced quality gates (SSIM + LPIPS)")
    parser.add_argument("--disable-telemetry", action="store_true",
                       help="Disable anonymous telemetry (enabled by default)")
    parser.add_argument("--anti-noise", action="store_true",
                       help="Reduce compression artifacts using text/gray-safe filters and optional grayscale")
    parser.add_argument("--advanced-raster", action="store_true",
                       help="Enable Photoshop-like raster pipeline (background norm, CLAHE, unsharp, quantization)")
    parser.add_argument("--prefer-sharpness", action="store_true",
                       help="Bias selection towards sharper outputs when trade-offs exist")
    
    args = parser.parse_args()
    
    try:
        c = PDFCompressor(
            input_dir=args.input,
            output_dir=args.output, 
            enable_advanced_gates=args.advanced_gates,
            enable_telemetry=not args.disable_telemetry,
            enable_anti_noise=args.anti_noise,
            enable_advanced_raster=args.advanced_raster,
            prefer_sharpness=args.prefer_sharpness
        )
        res = c.process_all_pdfs()
        c.show_summary(res)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
