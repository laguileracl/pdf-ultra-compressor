#!/usr/bin/env python3
"""
Anonymous Telemetry System for PDF Compressor

This module provides privacy-compliant anonymous data collection for algorithm improvement.
No personal information or document content is collected - only technical metadata and
compression performance metrics.

Features:
- Anonymous document fingerprinting using technical characteristics
- Technical metadata extraction (file size, page count, PDF version)
- Compression result tracking with anonymous correlation
- Public analytics generation for algorithm improvement
- Full GDPR compliance with anonymization
"""

import hashlib
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Optional dependencies with graceful fallback
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False


class DocumentFingerprint:
    """Generate anonymous document identifiers based on technical characteristics."""
    
    @staticmethod
    def generate_anonymous_id(pdf_path: Path) -> str:
        """
        Generate an anonymous document ID using technical characteristics only.
        
        Uses file size, basic PDF structure, and page count to create a unique
        identifier without accessing document content or personal information.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Anonymous document identifier (SHA-256 hash)
        """
        try:
            # Technical characteristics for fingerprinting
            file_size = pdf_path.stat().st_size
            
            # Read first 1KB and last 1KB for structure analysis (no content)
            with open(pdf_path, 'rb') as f:
                header = f.read(1024)
                f.seek(-min(1024, file_size), 2)
                footer = f.read(1024)
            
            # Extract basic PDF structure info
            pdf_version = "unknown"
            if header.startswith(b'%PDF-'):
                version_line = header.split(b'\n')[0]
                pdf_version = version_line.decode('ascii', errors='ignore')
            
            # Create technical fingerprint
            fingerprint_data = {
                'file_size': file_size,
                'pdf_version': pdf_version,
                'header_hash': hashlib.md5(header).hexdigest(),
                'footer_hash': hashlib.md5(footer).hexdigest(),
                'filename_length': len(pdf_path.name),  # Length only, not content
            }
            
            # Add page count if PyPDF2 is available
            if HAS_PYPDF2:
                try:
                    with open(pdf_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        fingerprint_data['page_count'] = len(reader.pages)
                except Exception:
                    fingerprint_data['page_count'] = 0
            
            # Generate anonymous ID
            fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
            anonymous_id = hashlib.sha256(fingerprint_str.encode()).hexdigest()
            
            return anonymous_id
            
        except Exception as e:
            # Fallback to basic file characteristics
            fallback_data = f"{pdf_path.stat().st_size}_{pdf_path.suffix}_{len(pdf_path.name)}"
            return hashlib.sha256(fallback_data.encode()).hexdigest()


class TechnicalMetadataExtractor:
    """Extract technical metadata while preserving anonymity."""
    
    @staticmethod
    def extract_metadata(pdf_path: Path) -> Dict[str, Any]:
        """
        Extract technical metadata without accessing personal information.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with technical metadata
        """
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'file_size_bytes': pdf_path.stat().st_size,
            'file_size_mb': round(pdf_path.stat().st_size / (1024 * 1024), 2),
            'pdf_version': 'unknown',
            'page_count': 0,
            'has_images': False,
            'has_text': False,
            'content_type_estimate': 'unknown',
            'compression_present': False,
        }
        
        try:
            # Basic PDF version detection
            with open(pdf_path, 'rb') as f:
                header = f.read(1024)
                if header.startswith(b'%PDF-'):
                    version_line = header.split(b'\n')[0]
                    metadata['pdf_version'] = version_line.decode('ascii', errors='ignore')
                
                # Check for existing compression indicators
                sample_content = f.read(8192)  # Read more for compression detection
                if b'/FlateDecode' in sample_content or b'/Filter' in sample_content:
                    metadata['compression_present'] = True
            
            # Enhanced analysis with PyPDF2 if available
            if HAS_PYPDF2:
                try:
                    with open(pdf_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        metadata['page_count'] = len(reader.pages)
                        
                        # Analyze first few pages for content type (no actual content extraction)
                        for i, page in enumerate(reader.pages[:3]):  # Max 3 pages for sampling
                            try:
                                # Check for resources without extracting content
                                if '/XObject' in page.get('/Resources', {}):
                                    metadata['has_images'] = True
                                if '/Font' in page.get('/Resources', {}):
                                    metadata['has_text'] = True
                            except Exception:
                                continue
                            
                except Exception as e:
                    # PyPDF2 failed, use Ghostscript fallback
                    metadata.update(TechnicalMetadataExtractor._ghostscript_analysis(pdf_path))
            else:
                # No PyPDF2, try Ghostscript
                metadata.update(TechnicalMetadataExtractor._ghostscript_analysis(pdf_path))
            
            # Estimate content type based on analysis
            if metadata['has_images'] and metadata['has_text']:
                metadata['content_type_estimate'] = 'mixed'
            elif metadata['has_images']:
                metadata['content_type_estimate'] = 'image_heavy'
            elif metadata['has_text']:
                metadata['content_type_estimate'] = 'text_heavy'
            else:
                metadata['content_type_estimate'] = 'unknown'
                
        except Exception as e:
            metadata['analysis_error'] = str(e)
        
        return metadata
    
    @staticmethod
    def _ghostscript_analysis(pdf_path: Path) -> Dict[str, Any]:
        """Use Ghostscript for basic PDF analysis as fallback."""
        analysis = {}
        
        try:
            # Try to get page count using Ghostscript
            cmd = ['gs', '-q', '-dNODISPLAY', '-c', 
                   f'({pdf_path}) (r) file runpdfbegin pdfpagecount = quit']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip().isdigit():
                analysis['page_count'] = int(result.stdout.strip())
                
        except Exception:
            pass
        
        return analysis


class AnonymousTelemetry:
    """Main telemetry class for anonymous data collection and analysis."""
    
    def __init__(self, data_dir: str = "telemetry_data"):
        """
        Initialize telemetry system.
        
        Args:
            data_dir: Directory to store anonymous telemetry data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.data_dir / "documents").mkdir(exist_ok=True)
        (self.data_dir / "compressions").mkdir(exist_ok=True)
        (self.data_dir / "analytics").mkdir(exist_ok=True)
        
        self.fingerprint_generator = DocumentFingerprint()
        self.metadata_extractor = TechnicalMetadataExtractor()
    
    def analyze_document(self, pdf_path: Path) -> str:
        """
        Analyze a document and return its anonymous ID.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Anonymous document ID
        """
        # Generate anonymous ID
        doc_id = self.fingerprint_generator.generate_anonymous_id(pdf_path)
        
        # Extract technical metadata
        metadata = self.metadata_extractor.extract_metadata(pdf_path)
        
        # Store document analysis (anonymized)
        doc_data = {
            'document_id': doc_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'technical_metadata': metadata,
            'privacy_note': 'No personal information or document content stored'
        }
        
        # Save to anonymous document file
        doc_file = self.data_dir / "documents" / f"{doc_id}.json"
        with open(doc_file, 'w') as f:
            json.dump(doc_data, f, indent=2)
        
        return doc_id
    
    def record_compression_result(self, doc_id: str, compression_result: Dict[str, Any]) -> None:
        """
        Record the result of a compression operation.
        
        Args:
            doc_id: Anonymous document ID
            compression_result: Compression result dictionary
        """
        # Create anonymized compression record
        compression_record = {
            'document_id': doc_id,
            'compression_timestamp': datetime.now().isoformat(),
            'original_size_mb': compression_result.get('original_size_mb', 0),
            'final_size_mb': compression_result.get('final_size_mb', 0),
            'reduction_percent': compression_result.get('reduction_percent', 0),
            'winner_method': compression_result.get('winner_method', 'unknown'),
            'quality_metrics': {
                'psnr_db': compression_result.get('psnr_db'),
                'ssim': compression_result.get('ssim'),
                'lpips': compression_result.get('lpips'),
                'quality_score': compression_result.get('quality_score', 0),
            },
            'success': 'error' not in compression_result,
            'error': compression_result.get('error'),
            'privacy_note': 'Anonymous compression metrics only'
        }
        
        # Generate unique compression record ID
        record_id = hashlib.sha256(
            f"{doc_id}_{compression_record['compression_timestamp']}"
            .encode()).hexdigest()[:16]
        
        # Save compression record
        record_file = self.data_dir / "compressions" / f"{record_id}.json"
        with open(record_file, 'w') as f:
            json.dump(compression_record, f, indent=2)
    
    def generate_public_analytics(self) -> Dict[str, Any]:
        """
        Generate public analytics from collected anonymous data.
        
        Returns:
            Public analytics suitable for algorithm improvement
        """
        analytics = {
            'generation_timestamp': datetime.now().isoformat(),
            'total_documents_analyzed': 0,
            'total_compressions': 0,
            'compression_methods': {},
            'size_distributions': {
                'small_files_mb': [],  # <10MB
                'medium_files_mb': [],  # 10-50MB  
                'large_files_mb': [],  # >50MB
            },
            'compression_effectiveness': {
                'by_method': {},
                'by_file_size': {},
                'by_content_type': {},
            },
            'quality_metrics': {
                'psnr_distribution': [],
                'ssim_distribution': [],
                'lpips_distribution': [],
            },
            'recommendations': [],
            'privacy_statement': 'All data anonymized - no personal information included'
        }
        
        try:
            # Analyze document metadata
            doc_files = list((self.data_dir / "documents").glob("*.json"))
            analytics['total_documents_analyzed'] = len(doc_files)
            
            content_types = {}
            for doc_file in doc_files:
                try:
                    with open(doc_file, 'r') as f:
                        doc_data = json.load(f)
                    
                    metadata = doc_data.get('technical_metadata', {})
                    file_size = metadata.get('file_size_mb', 0)
                    content_type = metadata.get('content_type_estimate', 'unknown')
                    
                    # Categorize by size
                    if file_size < 10:
                        analytics['size_distributions']['small_files_mb'].append(file_size)
                    elif file_size < 50:
                        analytics['size_distributions']['medium_files_mb'].append(file_size)
                    else:
                        analytics['size_distributions']['large_files_mb'].append(file_size)
                    
                    # Track content types
                    content_types[content_type] = content_types.get(content_type, 0) + 1
                    
                except Exception:
                    continue
            
            # Analyze compression results
            compression_files = list((self.data_dir / "compressions").glob("*.json"))
            analytics['total_compressions'] = len(compression_files)
            
            method_results = {}
            size_results = {}
            quality_data = {'psnr': [], 'ssim': [], 'lpips': []}
            
            for comp_file in compression_files:
                try:
                    with open(comp_file, 'r') as f:
                        comp_data = json.load(f)
                    
                    if not comp_data.get('success', False):
                        continue
                    
                    method = comp_data.get('winner_method', 'unknown')
                    reduction = comp_data.get('reduction_percent', 0)
                    original_size = comp_data.get('original_size_mb', 0)
                    
                    # Track by method
                    if method not in method_results:
                        method_results[method] = []
                    method_results[method].append(reduction)
                    
                    # Track by size category
                    size_category = 'large' if original_size > 50 else ('medium' if original_size > 10 else 'small')
                    if size_category not in size_results:
                        size_results[size_category] = []
                    size_results[size_category].append(reduction)
                    
                    # Collect quality metrics
                    quality_metrics = comp_data.get('quality_metrics', {})
                    if quality_metrics.get('psnr_db'):
                        quality_data['psnr'].append(quality_metrics['psnr_db'])
                    if quality_metrics.get('ssim'):
                        quality_data['ssim'].append(quality_metrics['ssim'])
                    if quality_metrics.get('lpips'):
                        quality_data['lpips'].append(quality_metrics['lpips'])
                    
                except Exception:
                    continue
            
            # Generate method statistics
            for method, reductions in method_results.items():
                analytics['compression_methods'][method] = len(reductions)
                analytics['compression_effectiveness']['by_method'][method] = {
                    'avg_reduction': round(sum(reductions) / len(reductions), 2) if reductions else 0,
                    'max_reduction': round(max(reductions), 2) if reductions else 0,
                    'usage_count': len(reductions)
                }
            
            # Generate size-based statistics
            for size_cat, reductions in size_results.items():
                analytics['compression_effectiveness']['by_file_size'][size_cat] = {
                    'avg_reduction': round(sum(reductions) / len(reductions), 2) if reductions else 0,
                    'sample_count': len(reductions)
                }
            
            # Quality metrics distributions
            for metric, values in quality_data.items():
                if values:
                    analytics['quality_metrics'][f'{metric}_distribution'] = {
                        'avg': round(sum(values) / len(values), 3),
                        'min': round(min(values), 3),
                        'max': round(max(values), 3),
                        'sample_count': len(values)
                    }
            
            # Generate recommendations based on data
            analytics['recommendations'] = self._generate_recommendations(analytics)
            
        except Exception as e:
            analytics['generation_error'] = str(e)
        
        # Save public analytics
        analytics_file = self.data_dir / "analytics" / f"public_analytics_{int(time.time())}.json"
        with open(analytics_file, 'w') as f:
            json.dump(analytics, f, indent=2)
        
        return analytics
    
    def _generate_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """Generate algorithm improvement recommendations based on analytics."""
        recommendations = []
        
        try:
            # Method effectiveness recommendations
            method_stats = analytics.get('compression_effectiveness', {}).get('by_method', {})
            if method_stats:
                best_method = max(method_stats.keys(), 
                                key=lambda m: method_stats[m].get('avg_reduction', 0))
                recommendations.append(
                    f"Best performing method: {best_method} "
                    f"(avg {method_stats[best_method]['avg_reduction']}% reduction)"
                )
            
            # Size-based recommendations
            size_stats = analytics.get('compression_effectiveness', {}).get('by_file_size', {})
            for size_cat, stats in size_stats.items():
                if stats['avg_reduction'] < 10:
                    recommendations.append(
                        f"Low compression for {size_cat} files - consider algorithm optimization"
                    )
            
            # Quality recommendations
            quality_metrics = analytics.get('quality_metrics', {})
            psnr_data = quality_metrics.get('psnr_distribution', {})
            if psnr_data and psnr_data.get('avg', 0) < 30:
                recommendations.append("Average PSNR below optimal threshold - review quality gates")
                
        except Exception:
            recommendations.append("Analytics data insufficient for recommendations")
        
        return recommendations
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get a summary of collected telemetry data."""
        try:
            doc_count = len(list((self.data_dir / "documents").glob("*.json")))
            comp_count = len(list((self.data_dir / "compressions").glob("*.json")))
            analytics_count = len(list((self.data_dir / "analytics").glob("*.json")))
            
            return {
                'documents_analyzed': doc_count,
                'compressions_recorded': comp_count,
                'analytics_generated': analytics_count,
                'data_directory': str(self.data_dir.absolute()),
                'privacy_compliance': 'GDPR compliant - anonymous data only'
            }
        except Exception as e:
            return {'error': str(e)}


def main():
    """Example usage of the anonymous telemetry system."""
    print("🔒 Anonymous Telemetry System - Privacy-Compliant Data Collection")
    print("="*60)
    
    # Initialize telemetry
    telemetry = AnonymousTelemetry()
    
    # Example workflow (normally done by the main compressor)
    # Note: This is just for demonstration - real usage is in compressor.py
    
    print("📊 Telemetry System Summary:")
    summary = telemetry.get_data_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n🔍 Generating Public Analytics...")
    analytics = telemetry.generate_public_analytics()
    
    print(f"📈 Analytics Summary:")
    print(f"  Documents analyzed: {analytics['total_documents_analyzed']}")
    print(f"  Compressions recorded: {analytics['total_compressions']}")
    print(f"  Methods tracked: {list(analytics['compression_methods'].keys())}")
    
    if analytics.get('recommendations'):
        print(f"\n💡 Recommendations:")
        for rec in analytics['recommendations']:
            print(f"  • {rec}")
    
    print(f"\n🔒 Privacy: {analytics['privacy_statement']}")


if __name__ == "__main__":
    main()
