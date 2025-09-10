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
                 enable_telemetry: bool = True):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.enable_advanced_gates = enable_advanced_gates and HAS_ADVANCED_GATES
        self.enable_telemetry = enable_telemetry and HAS_TELEMETRY

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
        print(f"  {'✅' if self.tools['pdftk'] else '❌'} PDFtk: {self.tools['pdftk'] or 'Not found'}\n")

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

            # Strategy 4: Ghostscript aggressive but safe
            if self.tools["gs"]:
                c4 = self._aggressive_safe_gs(pdf_path)
                if c4:
                    candidates.append(("aggressive_safe", c4))

            # Select best result (size vs. quality heuristic)
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

    # ---------- selection ----------
    def _select_best_result(self, original: Path, candidates: List[Tuple[str, Path]]) -> Optional[Dict]:
        if not candidates:
            return None
        original_size = original.stat().st_size
        best: Optional[Dict] = None
        best_score = -1.0

        print("\n🔍 Evaluating results:")
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

        THRESHOLD_DB = 35.0
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
    
    args = parser.parse_args()
    
    try:
        c = PDFCompressor(
            input_dir=args.input,
            output_dir=args.output, 
            enable_advanced_gates=args.advanced_gates,
            enable_telemetry=not args.disable_telemetry
        )
        res = c.process_all_pdfs()
        c.show_summary(res)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
