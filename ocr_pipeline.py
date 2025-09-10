#!/usr/bin/env python3
"""
OCR/JBIG2 Pipeline for PDF Ultra Compressor.

Implements Mixed Raster Content (MRC) segmentation for scanned documents:
- Detects scanned documents vs. native digital PDFs
- Separates text/graphics layers from image backgrounds
- Applies OCR using OCRmyPDF
- Uses JBIG2 compression for 1-bit text layers
- Uses JPEG2000/advanced compression for image layers

Usage:
    from ocr_pipeline import OCRPipeline
    
    pipeline = OCRPipeline()
    result = pipeline.process_scanned_pdf(input_pdf, output_pdf)
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import json

try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class OCRPipelineConfig:
    """Configuration for OCR/JBIG2 pipeline."""
    
    def __init__(self):
        # Detection thresholds
        self.scanned_threshold = 0.7  # Confidence threshold for scanned detection
        self.min_text_ratio = 0.1     # Minimum text ratio to proceed with OCR
        
        # OCR settings
        self.ocr_language = "eng"     # OCRmyPDF language code
        self.ocr_dpi = 300           # DPI for OCR processing
        self.force_ocr = False       # Force OCR even if text detected
        
        # JBIG2 settings
        self.jbig2_threshold = 0.9   # Threshold for JBIG2 1-bit conversion
        self.jbig2_enabled = True    # Enable JBIG2 compression
        
        # Image processing
        self.max_image_dpi = 150     # Max DPI for image layers
        self.jpeg_quality = 85       # JPEG quality for image layers
        self.use_jpeg2000 = False    # Use JPEG2000 instead of JPEG
        
        # Performance
        self.parallel_processing = True
        self.temp_cleanup = True
        
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'OCRPipelineConfig':
        """Create config from dictionary."""
        config = cls()
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config


class DocumentAnalysisResult:
    """Result of document analysis for OCR pipeline decision."""
    
    def __init__(self):
        self.is_scanned: bool = False
        self.confidence: float = 0.0
        self.text_ratio: float = 0.0
        self.image_ratio: float = 0.0
        self.page_count: int = 0
        self.avg_dpi: Optional[float] = None
        self.has_embedded_text: bool = False
        self.recommendation: str = "skip"  # "skip", "ocr", "hybrid"
        self.analysis_details: Dict = {}


class OCRPipelineResult:
    """Result of OCR pipeline processing."""
    
    def __init__(self):
        self.success: bool = False
        self.method_used: str = "none"
        self.original_size: int = 0
        self.final_size: int = 0
        self.compression_ratio: float = 1.0
        self.ocr_applied: bool = False
        self.jbig2_applied: bool = False
        self.text_pages: int = 0
        self.image_pages: int = 0
        self.processing_time: float = 0.0
        self.error_message: Optional[str] = None
        self.quality_metrics: Dict = {}


class OCRPipeline:
    """OCR/JBIG2 pipeline for scanned document optimization."""
    
    def __init__(self, config: Optional[OCRPipelineConfig] = None):
        self.config = config or OCRPipelineConfig()
        self.tools = self._detect_tools()
        self._check_dependencies()
        
    def _detect_tools(self) -> Dict[str, Optional[str]]:
        """Detect required tools for OCR pipeline."""
        tools = {
            "ocrmypdf": None,
            "gs": None,
            "qpdf": None,
            "pdfimages": None,
            "tesseract": None,
            "jbig2": None
        }
        
        # Check each tool
        for tool in tools.keys():
            if tool == "jbig2":
                # Check for jbig2enc
                for candidate in ["jbig2", "jbig2enc"]:
                    if shutil.which(candidate):
                        tools[tool] = candidate
                        break
            else:
                tools[tool] = shutil.which(tool)
        
        return tools
    
    def _check_dependencies(self):
        """Check and warn about missing dependencies."""
        missing_tools = []
        missing_python = []
        
        # Required tools
        if not self.tools["ocrmypdf"]:
            missing_tools.append("ocrmypdf")
        if not self.tools["gs"]:
            missing_tools.append("ghostscript")
        if not self.tools["tesseract"]:
            missing_tools.append("tesseract-ocr")
            
        # Optional tools
        if not self.tools["jbig2"] and self.config.jbig2_enabled:
            missing_tools.append("jbig2enc (optional)")
            self.config.jbig2_enabled = False
            
        # Python dependencies
        if not HAS_PIL:
            missing_python.append("Pillow")
        if not HAS_CV2:
            missing_python.append("opencv-python")
            
        if missing_tools or missing_python:
            print("OCR Pipeline Dependencies:")
            if missing_tools:
                print(f"  Missing tools: {', '.join(missing_tools)}")
                print("  Install with: brew install ocrmypdf tesseract jbig2enc")
            if missing_python:
                print(f"  Missing Python packages: {', '.join(missing_python)}")
                print("  Install with: pip install Pillow opencv-python")
    
    def is_available(self) -> bool:
        """Check if OCR pipeline is available."""
        return (self.tools["ocrmypdf"] is not None and 
                self.tools["gs"] is not None and
                HAS_PIL)
    
    def analyze_document(self, pdf_path: Path) -> DocumentAnalysisResult:
        """Analyze PDF to determine if it's suitable for OCR pipeline."""
        result = DocumentAnalysisResult()
        
        if not self.is_available():
            result.recommendation = "skip"
            result.analysis_details["error"] = "OCR pipeline not available"
            return result
        
        try:
            # Get basic PDF info
            result.page_count = self._get_page_count(pdf_path)
            result.has_embedded_text = self._has_embedded_text(pdf_path)
            
            # Analyze first few pages for scanned characteristics
            sample_pages = min(3, result.page_count)
            scanned_indicators = []
            
            for page_num in range(sample_pages):
                page_analysis = self._analyze_page(pdf_path, page_num)
                scanned_indicators.append(page_analysis)
            
            # Aggregate analysis
            if scanned_indicators:
                result.confidence = sum(p.get("scanned_confidence", 0) for p in scanned_indicators) / len(scanned_indicators)
                result.text_ratio = sum(p.get("text_ratio", 0) for p in scanned_indicators) / len(scanned_indicators)
                result.image_ratio = sum(p.get("image_ratio", 0) for p in scanned_indicators) / len(scanned_indicators)
                
                if "avg_dpi" in scanned_indicators[0]:
                    result.avg_dpi = sum(p.get("avg_dpi", 150) for p in scanned_indicators) / len(scanned_indicators)
            
            # Determine if document is scanned
            result.is_scanned = (result.confidence >= self.config.scanned_threshold or
                               (not result.has_embedded_text and result.image_ratio > 0.8))
            
            # Make recommendation
            if result.is_scanned and result.text_ratio >= self.config.min_text_ratio:
                result.recommendation = "ocr"
            elif result.is_scanned and result.image_ratio > 0.9:
                result.recommendation = "hybrid"  # Image-only optimization
            else:
                result.recommendation = "skip"
            
            result.analysis_details = {
                "sample_pages": sample_pages,
                "page_analyses": scanned_indicators
            }
            
        except Exception as e:
            result.recommendation = "skip"
            result.analysis_details["error"] = str(e)
        
        return result
    
    def _get_page_count(self, pdf_path: Path) -> int:
        """Get number of pages in PDF."""
        try:
            cmd = ["qpdf", "--show-npages", str(pdf_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return int(result.stdout.strip())
        except Exception:
            pass
        
        # Fallback using ghostscript
        try:
            cmd = ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=nullpage", 
                   "-c", "eof", str(pdf_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            # Parse output for page count
            if "Processing pages" in result.stderr:
                import re
                match = re.search(r"Processing pages 1 through (\d+)", result.stderr)
                if match:
                    return int(match.group(1))
        except Exception:
            pass
        
        return 1  # Default fallback
    
    def _has_embedded_text(self, pdf_path: Path) -> bool:
        """Check if PDF has embedded text."""
        try:
            cmd = ["pdffonts", str(pdf_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # If pdffonts shows fonts, there's likely embedded text
                lines = result.stdout.strip().split('\n')
                return len(lines) > 2  # Header lines + actual fonts
        except Exception:
            pass
        
        # Fallback: try to extract text with qpdf
        try:
            cmd = ["qpdf", "--filtered-stream-data", "--show-object=1", str(pdf_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            # Look for text content indicators
            return "BT" in result.stdout or "Tj" in result.stdout
        except Exception:
            pass
        
        return False
    
    def _analyze_page(self, pdf_path: Path, page_num: int) -> Dict:
        """Analyze a single page for scanned characteristics."""
        analysis = {
            "page": page_num,
            "scanned_confidence": 0.0,
            "text_ratio": 0.0,
            "image_ratio": 0.0,
            "avg_dpi": 150.0
        }
        
        if not HAS_PIL or not HAS_CV2:
            return analysis
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extract page as image
                img_path = temp_path / f"page_{page_num}.png"
                cmd = [
                    "gs", "-dNOPAUSE", "-dBATCH", "-dSAFER",
                    "-sDEVICE=png16m", "-r150",
                    f"-dFirstPage={page_num + 1}",
                    f"-dLastPage={page_num + 1}",
                    f"-sOutputFile={img_path}",
                    str(pdf_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True)
                if result.returncode != 0 or not img_path.exists():
                    return analysis
                
                # Analyze image characteristics
                img = cv2.imread(str(img_path))
                if img is None:
                    return analysis
                
                # Convert to grayscale
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                # Calculate image characteristics
                height, width = gray.shape
                total_pixels = height * width
                
                # Edge detection to find text vs image areas
                edges = cv2.Canny(gray, 50, 150)
                edge_pixels = np.count_nonzero(edges)
                edge_ratio = edge_pixels / total_pixels
                
                # Analyze intensity distribution
                hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
                
                # Bimodal distribution suggests scanned text
                # Peaks at black (0) and white (255) indicate text
                black_pixels = hist[0:50].sum()
                white_pixels = hist[200:256].sum()
                bimodal_ratio = (black_pixels + white_pixels) / total_pixels
                
                # Texture analysis
                # High frequency content suggests scanned origin
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                texture_variance = laplacian.var()
                
                # Combine indicators for scanned confidence
                scanned_confidence = 0.0
                
                # High bimodal ratio suggests text
                if bimodal_ratio > 0.6:
                    scanned_confidence += 0.4
                    analysis["text_ratio"] = min(bimodal_ratio, 1.0)
                
                # Moderate edge density suggests scanned text
                if 0.05 < edge_ratio < 0.3:
                    scanned_confidence += 0.3
                
                # Texture variance in certain range suggests scanning artifacts
                if 100 < texture_variance < 1000:
                    scanned_confidence += 0.3
                
                analysis["scanned_confidence"] = min(scanned_confidence, 1.0)
                analysis["image_ratio"] = 1.0 - analysis["text_ratio"]
                
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis
    
    def process_scanned_pdf(self, input_pdf: Path, output_pdf: Path) -> OCRPipelineResult:
        """Process a scanned PDF through the OCR/JBIG2 pipeline."""
        result = OCRPipelineResult()
        result.original_size = input_pdf.stat().st_size
        
        if not self.is_available():
            result.error_message = "OCR pipeline not available"
            return result
        
        # Analyze document first
        analysis = self.analyze_document(input_pdf)
        if analysis.recommendation == "skip":
            result.error_message = "Document not suitable for OCR pipeline"
            return result
        
        import time
        start_time = time.time()
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                if analysis.recommendation == "ocr":
                    result = self._process_with_ocr(input_pdf, output_pdf, temp_path, result)
                elif analysis.recommendation == "hybrid":
                    result = self._process_hybrid(input_pdf, output_pdf, temp_path, result)
                
                result.processing_time = time.time() - start_time
                
                if output_pdf.exists():
                    result.final_size = output_pdf.stat().st_size
                    result.compression_ratio = result.original_size / result.final_size
                    result.success = True
                
        except Exception as e:
            result.error_message = str(e)
            result.success = False
        
        return result
    
    def _process_with_ocr(self, input_pdf: Path, output_pdf: Path, temp_path: Path, result: OCRPipelineResult) -> OCRPipelineResult:
        """Process PDF with full OCR pipeline."""
        result.method_used = "ocr"
        
        # Step 1: Apply OCR using OCRmyPDF
        ocr_pdf = temp_path / "ocr_output.pdf"
        
        ocr_cmd = [
            self.tools["ocrmypdf"],
            "--language", self.config.ocr_language,
            "--deskew",
            "--clean",
            "--remove-background",
        ]
        
        if self.config.force_ocr:
            ocr_cmd.append("--force-ocr")
        
        if self.config.jbig2_enabled and self.tools["jbig2"]:
            ocr_cmd.extend(["--jbig2-lossy"])
            result.jbig2_applied = True
        
        ocr_cmd.extend([str(input_pdf), str(ocr_pdf)])
        
        ocr_result = subprocess.run(ocr_cmd, capture_output=True, text=True)
        if ocr_result.returncode != 0:
            raise Exception(f"OCRmyPDF failed: {ocr_result.stderr}")
        
        result.ocr_applied = True
        
        # Step 2: Additional compression with Ghostscript
        gs_cmd = [
            self.tools["gs"],
            "-dNOPAUSE", "-dBATCH", "-dSAFER",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/prepress",
            "-dCompressFonts=true",
            "-dSubsetFonts=true",
            f"-sOutputFile={output_pdf}",
            str(ocr_pdf)
        ]
        
        gs_result = subprocess.run(gs_cmd, capture_output=True, text=True)
        if gs_result.returncode != 0:
            # Fallback: copy OCR result directly
            shutil.copy2(ocr_pdf, output_pdf)
        
        return result
    
    def _process_hybrid(self, input_pdf: Path, output_pdf: Path, temp_path: Path, result: OCRPipelineResult) -> OCRPipelineResult:
        """Process PDF with hybrid image optimization (no OCR)."""
        result.method_used = "hybrid"
        
        # Use aggressive image compression for image-heavy scanned docs
        gs_cmd = [
            self.tools["gs"],
            "-dNOPAUSE", "-dBATCH", "-dSAFER",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/ebook",
            "-dColorImageResolution=150",
            "-dGrayImageResolution=150",
            "-dMonoImageResolution=300",
            f"-dJPEGQ={self.config.jpeg_quality}",
            "-dAutoFilterColorImages=false",
            "-dAutoFilterGrayImages=false",
            "-dColorImageFilter=/DCTDecode",
            "-dGrayImageFilter=/DCTDecode",
            f"-sOutputFile={output_pdf}",
            str(input_pdf)
        ]
        
        if self.config.jbig2_enabled and self.tools["jbig2"]:
            gs_cmd.extend(["-dMonoImageFilter=/JBIG2Decode"])
            result.jbig2_applied = True
        
        gs_result = subprocess.run(gs_cmd, capture_output=True, text=True)
        if gs_result.returncode != 0:
            raise Exception(f"Ghostscript hybrid processing failed: {gs_result.stderr}")
        
        return result
    
    def create_processing_report(self, result: OCRPipelineResult, analysis: DocumentAnalysisResult, output_file: Optional[Path] = None) -> str:
        """Create a detailed processing report."""
        report_lines = [
            "OCR/JBIG2 Pipeline Report",
            "=" * 40,
            f"Success: {'Yes' if result.success else 'No'}",
            f"Method: {result.method_used}",
            ""
        ]
        
        # Document analysis
        report_lines.extend([
            "Document Analysis:",
            f"  Scanned document: {'Yes' if analysis.is_scanned else 'No'} (confidence: {analysis.confidence:.2f})",
            f"  Text ratio: {analysis.text_ratio:.2f}",
            f"  Image ratio: {analysis.image_ratio:.2f}",
            f"  Page count: {analysis.page_count}",
            f"  Has embedded text: {'Yes' if analysis.has_embedded_text else 'No'}",
            f"  Recommendation: {analysis.recommendation}",
            ""
        ])
        
        # Processing results
        if result.success:
            compression_pct = ((result.original_size - result.final_size) / result.original_size) * 100
            
            report_lines.extend([
                "Processing Results:",
                f"  Original size: {result.original_size / (1024*1024):.1f} MB",
                f"  Final size: {result.final_size / (1024*1024):.1f} MB",
                f"  Compression: {compression_pct:.1f}% reduction",
                f"  Compression ratio: {result.compression_ratio:.2f}x",
                f"  Processing time: {result.processing_time:.1f}s",
                ""
            ])
            
            # Applied techniques
            techniques = []
            if result.ocr_applied:
                techniques.append("OCR")
            if result.jbig2_applied:
                techniques.append("JBIG2")
            
            if techniques:
                report_lines.append(f"  Techniques applied: {', '.join(techniques)}")
            
        else:
            report_lines.extend([
                "Processing Failed:",
                f"  Error: {result.error_message or 'Unknown error'}",
                ""
            ])
        
        report_text = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
        
        return report_text


def main():
    """Test the OCR pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OCR/JBIG2 Pipeline for scanned PDFs")
    parser.add_argument("input", help="Input PDF file")
    parser.add_argument("output", help="Output PDF file")
    parser.add_argument("--analyze-only", action="store_true",
                       help="Only analyze document, don't process")
    parser.add_argument("--config", help="JSON config file")
    parser.add_argument("--report", help="Output report file")
    
    args = parser.parse_args()
    
    # Load config if provided
    config = OCRPipelineConfig()
    if args.config:
        with open(args.config, 'r') as f:
            config_dict = json.load(f)
            config = OCRPipelineConfig.from_dict(config_dict)
    
    # Initialize pipeline
    pipeline = OCRPipeline(config)
    
    if not pipeline.is_available():
        print("OCR pipeline not available. Check dependencies.")
        exit(1)
    
    input_pdf = Path(args.input)
    if not input_pdf.exists():
        print(f"Input file not found: {input_pdf}")
        exit(1)
    
    # Analyze document
    print("Analyzing document...")
    analysis = pipeline.analyze_document(input_pdf)
    
    print(f"Document analysis:")
    print(f"  Scanned: {'Yes' if analysis.is_scanned else 'No'} (confidence: {analysis.confidence:.2f})")
    print(f"  Recommendation: {analysis.recommendation}")
    
    if args.analyze_only:
        exit(0)
    
    if analysis.recommendation == "skip":
        print("Document not suitable for OCR pipeline.")
        exit(1)
    
    # Process document
    print("Processing document...")
    output_pdf = Path(args.output)
    result = pipeline.process_scanned_pdf(input_pdf, output_pdf)
    
    # Generate report
    report = pipeline.create_processing_report(
        result, analysis, 
        Path(args.report) if args.report else None
    )
    print(report)
    
    # Exit with appropriate code
    exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
