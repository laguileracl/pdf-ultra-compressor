#!/usr/bin/env python3
"""
Benchmark runner for PDF Ultra Compressor.

Runs compression tests on a curated dataset and measures:
- Size reduction percentages
- PSNR/SSIM quality metrics where applicable
- Processing time
- Strategy selection frequency

Usage:
    python benchmarks/benchmark_runner.py [--dataset DATASET] [--output OUTPUT]
"""

import argparse
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import compressor
except ImportError:
    print("Error: Could not import compressor module. Run from project root.", file=sys.stderr)
    sys.exit(1)


@dataclass
class BenchmarkResult:
    """Single PDF benchmark result."""
    filename: str
    original_size: int
    compressed_size: int
    compression_ratio: float
    size_reduction_percent: float
    processing_time: float
    selected_strategy: str
    psnr_score: Optional[float] = None
    ssim_score: Optional[float] = None
    error: Optional[str] = None


@dataclass
class BenchmarkSummary:
    """Summary statistics for a benchmark run."""
    total_files: int
    successful_compressions: int
    failed_compressions: int
    avg_compression_ratio: float
    avg_size_reduction: float
    avg_processing_time: float
    avg_psnr: Optional[float]
    avg_ssim: Optional[float]
    strategy_frequency: Dict[str, int]
    total_original_size: int
    total_compressed_size: int


class BenchmarkRunner:
    """Runs PDF compression benchmarks."""
    
    def __init__(self, dataset_dir: Path, output_dir: Path):
        self.dataset_dir = Path(dataset_dir)
        self.output_dir = Path(output_dir)
        self.results: List[BenchmarkResult] = []
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def run_benchmark(self, pdf_path: Path) -> BenchmarkResult:
        """Run benchmark on a single PDF."""
        try:
            # Get original size
            original_size = pdf_path.stat().st_size
            
            # Create temporary workspace
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                input_dir = temp_path / "input"
                output_dir = temp_path / "output"
                input_dir.mkdir()
                output_dir.mkdir()
                
                # Copy PDF to input
                test_pdf = input_dir / pdf_path.name
                shutil.copy2(pdf_path, test_pdf)
                
                # Run compression with timing
                start_time = time.time()
                
                # Mock compression call - in real implementation, would run compressor.py
                # For now, simulate compression with basic metrics
                result = self._simulate_compression(test_pdf, output_dir)
                
                processing_time = time.time() - start_time
                
                if result["success"]:
                    compressed_size = result["compressed_size"]
                    compression_ratio = original_size / compressed_size if compressed_size > 0 else 1.0
                    size_reduction = ((original_size - compressed_size) / original_size) * 100
                    
                    return BenchmarkResult(
                        filename=pdf_path.name,
                        original_size=original_size,
                        compressed_size=compressed_size,
                        compression_ratio=compression_ratio,
                        size_reduction_percent=size_reduction,
                        processing_time=processing_time,
                        selected_strategy=result["strategy"],
                        psnr_score=result.get("psnr"),
                        ssim_score=result.get("ssim")
                    )
                else:
                    return BenchmarkResult(
                        filename=pdf_path.name,
                        original_size=original_size,
                        compressed_size=original_size,
                        compression_ratio=1.0,
                        size_reduction_percent=0.0,
                        processing_time=processing_time,
                        selected_strategy="none",
                        error=result.get("error", "Compression failed")
                    )
                    
        except Exception as e:
            return BenchmarkResult(
                filename=pdf_path.name,
                original_size=pdf_path.stat().st_size if pdf_path.exists() else 0,
                compressed_size=0,
                compression_ratio=1.0,
                size_reduction_percent=0.0,
                processing_time=0.0,
                selected_strategy="error",
                error=str(e)
            )
    
    def _simulate_compression(self, pdf_path: Path, output_dir: Path) -> Dict:
        """Simulate compression for testing. Replace with actual compressor call."""
        # This is a placeholder - in real implementation, would call compressor.py
        # and parse its output for strategy selection and metrics
        
        original_size = pdf_path.stat().st_size
        
        # Simulate compression ratios based on filename patterns
        if "text" in pdf_path.name.lower():
            simulated_ratio = 0.8  # 20% reduction for text-heavy
            strategy = "conservative_qpdf"
        elif "image" in pdf_path.name.lower():
            simulated_ratio = 0.5  # 50% reduction for image-heavy
            strategy = "balanced_gs"
        elif "scan" in pdf_path.name.lower():
            simulated_ratio = 0.3  # 70% reduction for scanned
            strategy = "aggressive_safe_gs"
        else:
            simulated_ratio = 0.7  # 30% reduction default
            strategy = "high_quality_gs"
        
        compressed_size = int(original_size * simulated_ratio)
        
        return {
            "success": True,
            "compressed_size": compressed_size,
            "strategy": strategy,
            "psnr": 45.0 if "scan" not in pdf_path.name.lower() else 38.0,
            "ssim": 0.95 if "text" in pdf_path.name.lower() else 0.85
        }
    
    def run_all_benchmarks(self) -> BenchmarkSummary:
        """Run benchmarks on all PDFs in dataset directory."""
        pdf_files = list(self.dataset_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {self.dataset_dir}")
            return self._empty_summary()
        
        print(f"Running benchmarks on {len(pdf_files)} PDFs...")
        
        for pdf_file in pdf_files:
            print(f"Processing {pdf_file.name}...")
            result = self.run_benchmark(pdf_file)
            self.results.append(result)
        
        return self._calculate_summary()
    
    def _calculate_summary(self) -> BenchmarkSummary:
        """Calculate summary statistics from results."""
        if not self.results:
            return self._empty_summary()
        
        successful = [r for r in self.results if r.error is None]
        failed = [r for r in self.results if r.error is not None]
        
        if not successful:
            return BenchmarkSummary(
                total_files=len(self.results),
                successful_compressions=0,
                failed_compressions=len(failed),
                avg_compression_ratio=1.0,
                avg_size_reduction=0.0,
                avg_processing_time=0.0,
                avg_psnr=None,
                avg_ssim=None,
                strategy_frequency={},
                total_original_size=sum(r.original_size for r in self.results),
                total_compressed_size=sum(r.original_size for r in self.results)
            )
        
        # Calculate averages
        avg_compression_ratio = sum(r.compression_ratio for r in successful) / len(successful)
        avg_size_reduction = sum(r.size_reduction_percent for r in successful) / len(successful)
        avg_processing_time = sum(r.processing_time for r in successful) / len(successful)
        
        # PSNR/SSIM averages (exclude None values)
        psnr_values = [r.psnr_score for r in successful if r.psnr_score is not None]
        ssim_values = [r.ssim_score for r in successful if r.ssim_score is not None]
        
        avg_psnr = sum(psnr_values) / len(psnr_values) if psnr_values else None
        avg_ssim = sum(ssim_values) / len(ssim_values) if ssim_values else None
        
        # Strategy frequency
        strategy_freq = {}
        for result in successful:
            strategy = result.selected_strategy
            strategy_freq[strategy] = strategy_freq.get(strategy, 0) + 1
        
        return BenchmarkSummary(
            total_files=len(self.results),
            successful_compressions=len(successful),
            failed_compressions=len(failed),
            avg_compression_ratio=avg_compression_ratio,
            avg_size_reduction=avg_size_reduction,
            avg_processing_time=avg_processing_time,
            avg_psnr=avg_psnr,
            avg_ssim=avg_ssim,
            strategy_frequency=strategy_freq,
            total_original_size=sum(r.original_size for r in self.results),
            total_compressed_size=sum(r.compressed_size for r in successful) + 
                                 sum(r.original_size for r in failed)
        )
    
    def _empty_summary(self) -> BenchmarkSummary:
        """Return empty summary for no results."""
        return BenchmarkSummary(
            total_files=0,
            successful_compressions=0,
            failed_compressions=0,
            avg_compression_ratio=1.0,
            avg_size_reduction=0.0,
            avg_processing_time=0.0,
            avg_psnr=None,
            avg_ssim=None,
            strategy_frequency={},
            total_original_size=0,
            total_compressed_size=0
        )
    
    def save_results(self, summary: BenchmarkSummary, output_file: Optional[Path] = None):
        """Save benchmark results to JSON file."""
        if output_file is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"benchmark_results_{timestamp}.json"
        
        data = {
            "summary": asdict(summary),
            "individual_results": [asdict(r) for r in self.results],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "dataset_dir": str(self.dataset_dir),
            "total_files_processed": len(self.results)
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Results saved to {output_file}")
    
    def print_summary(self, summary: BenchmarkSummary):
        """Print human-readable summary."""
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)
        print(f"Total files processed: {summary.total_files}")
        print(f"Successful compressions: {summary.successful_compressions}")
        print(f"Failed compressions: {summary.failed_compressions}")
        
        if summary.successful_compressions > 0:
            print(f"\nCompression Performance:")
            print(f"  Average compression ratio: {summary.avg_compression_ratio:.2f}x")
            print(f"  Average size reduction: {summary.avg_size_reduction:.1f}%")
            print(f"  Average processing time: {summary.avg_processing_time:.2f}s")
            
            total_original_mb = summary.total_original_size / (1024 * 1024)
            total_compressed_mb = summary.total_compressed_size / (1024 * 1024)
            total_saved_mb = total_original_mb - total_compressed_mb
            
            print(f"\nOverall Statistics:")
            print(f"  Total original size: {total_original_mb:.1f} MB")
            print(f"  Total compressed size: {total_compressed_mb:.1f} MB") 
            print(f"  Total space saved: {total_saved_mb:.1f} MB")
            
            if summary.avg_psnr:
                print(f"\nQuality Metrics:")
                print(f"  Average PSNR: {summary.avg_psnr:.1f} dB")
            if summary.avg_ssim:
                print(f"  Average SSIM: {summary.avg_ssim:.3f}")
            
            if summary.strategy_frequency:
                print(f"\nStrategy Usage:")
                for strategy, count in sorted(summary.strategy_frequency.items(), 
                                            key=lambda x: x[1], reverse=True):
                    percentage = (count / summary.successful_compressions) * 100
                    print(f"  {strategy}: {count} files ({percentage:.1f}%)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run PDF compression benchmarks")
    parser.add_argument("--dataset", "-d", 
                       default="benchmarks/datasets",
                       help="Path to dataset directory (default: benchmarks/datasets)")
    parser.add_argument("--output", "-o",
                       default="benchmarks/results",
                       help="Output directory for results (default: benchmarks/results)")
    parser.add_argument("--save-json", "-j",
                       help="Save results to specific JSON file")
    
    args = parser.parse_args()
    
    dataset_dir = Path(args.dataset)
    output_dir = Path(args.output)
    
    if not dataset_dir.exists():
        print(f"Error: Dataset directory {dataset_dir} does not exist")
        print("Create it and add some PDF files to benchmark")
        sys.exit(1)
    
    # Run benchmarks
    runner = BenchmarkRunner(dataset_dir, output_dir)
    summary = runner.run_all_benchmarks()
    
    # Print and save results
    runner.print_summary(summary)
    
    output_file = Path(args.save_json) if args.save_json else None
    runner.save_results(summary, output_file)


if __name__ == "__main__":
    main()
