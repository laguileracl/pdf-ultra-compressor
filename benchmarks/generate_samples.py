#!/usr/bin/env python3
"""
Generate sample PDF files for benchmarking.

Creates representative PDFs with different characteristics:
- Text-heavy documents
- Image-heavy documents  
- Mixed content documents

Usage:
    python benchmarks/generate_samples.py [--output OUTPUT_DIR] [--count COUNT]
"""

import argparse
import os
import random
from pathlib import Path
from typing import List

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.graphics.shapes import Drawing, Rect
    from reportlab.graphics import renderPDF
    from PIL import Image, ImageDraw, ImageFont
    import io
except ImportError as e:
    print(f"Error: Missing required packages for PDF generation: {e}")
    print("Install with: pip install reportlab pillow")
    exit(1)


class SamplePDFGenerator:
    """Generates sample PDFs for benchmarking."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        
    def generate_text_heavy_pdf(self, filename: str, pages: int = 10) -> Path:
        """Generate a text-heavy PDF (academic paper style)."""
        output_path = self.output_dir / filename
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        story.append(Paragraph("Sample Academic Paper: PDF Compression Techniques", title_style))
        story.append(Spacer(1, 12))
        
        # Abstract
        story.append(Paragraph("Abstract", self.styles['Heading2']))
        abstract_text = """
        This paper presents a comprehensive analysis of PDF compression techniques 
        and their effectiveness on different document types. We examine lossless 
        and lossy compression methods, focusing on maintaining visual quality while 
        achieving maximum size reduction. Our findings demonstrate that hybrid 
        approaches combining multiple compression strategies yield optimal results 
        across diverse content types.
        """
        story.append(Paragraph(abstract_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Generate multiple sections with lorem ipsum style text
        sections = [
            "Introduction",
            "Related Work", 
            "Methodology",
            "Experimental Setup",
            "Results and Analysis",
            "Discussion",
            "Conclusion"
        ]
        
        lorem_paragraphs = [
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
            "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
            "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.",
            "Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.",
            "Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem."
        ]
        
        for section in sections:
            story.append(Paragraph(section, self.styles['Heading2']))
            
            # Add 2-4 paragraphs per section
            for _ in range(random.randint(2, 4)):
                para_text = random.choice(lorem_paragraphs)
                story.append(Paragraph(para_text, self.styles['Normal']))
                story.append(Spacer(1, 12))
            
            story.append(Spacer(1, 20))
        
        # References
        story.append(Paragraph("References", self.styles['Heading2']))
        references = [
            "[1] Smith, J. (2023). Advanced PDF Compression Algorithms. Journal of Document Processing, 15(3), 45-67.",
            "[2] Johnson, A. & Brown, M. (2022). Lossless Image Compression in PDF Documents. Proceedings of DocEng 2022.",
            "[3] Wilson, K. (2021). Quality Assessment in Document Compression. ACM Transactions on Graphics, 40(2), 123-135."
        ]
        
        for ref in references:
            story.append(Paragraph(ref, self.styles['Normal']))
            story.append(Spacer(1, 8))
        
        doc.build(story)
        return output_path
    
    def _create_sample_image(self, width: int = 400, height: int = 300, image_type: str = "chart") -> io.BytesIO:
        """Create a sample image for embedding in PDFs."""
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        if image_type == "chart":
            # Simple bar chart
            bars = [50, 120, 80, 150, 90, 110]
            bar_width = width // len(bars) - 10
            max_height = height - 40
            
            for i, bar_height in enumerate(bars):
                x1 = i * (bar_width + 10) + 20
                y1 = height - 20
                x2 = x1 + bar_width
                y2 = y1 - (bar_height / max(bars)) * max_height
                
                # Random colors for bars
                color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
                draw.rectangle([x1, y2, x2, y1], fill=color, outline='black')
        
        elif image_type == "diagram":
            # Simple flowchart-like diagram
            boxes = [(50, 50, 150, 100), (200, 50, 300, 100), (125, 150, 225, 200)]
            for box in boxes:
                draw.rectangle(box, fill='lightblue', outline='navy', width=2)
                # Add some text-like lines
                for j in range(3):
                    y = box[1] + 20 + j * 10
                    draw.line([(box[0] + 10, y), (box[2] - 10, y)], fill='black', width=1)
            
            # Connect boxes with arrows
            draw.line([(150, 75), (200, 75)], fill='black', width=2)
            draw.line([(250, 100), (175, 150)], fill='black', width=2)
        
        else:  # gradient or pattern
            # Create a gradient-like pattern
            for y in range(height):
                for x in range(width):
                    r = int(255 * (x / width))
                    g = int(255 * (y / height))
                    b = 128
                    if x % 20 < 10 and y % 20 < 10:
                        draw.point((x, y), fill=(r, g, b))
        
        # Save to BytesIO
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        return img_buffer
    
    def generate_image_heavy_pdf(self, filename: str, pages: int = 8) -> Path:
        """Generate an image-heavy PDF (presentation style)."""
        output_path = self.output_dir / filename
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        story = []
        
        # Title page
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1
        )
        
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("Visual Presentation: Data Analysis Results", title_style))
        story.append(Spacer(1, 1*inch))
        
        # Add title page image
        img_buffer = self._create_sample_image(500, 300, "chart")
        story.append(RLImage(img_buffer, width=5*inch, height=3*inch))
        story.append(PageBreak())
        
        # Generate content pages with images
        slide_titles = [
            "Market Analysis Overview",
            "Performance Metrics", 
            "User Engagement Data",
            "Revenue Trends",
            "Geographic Distribution",
            "Competitive Analysis",
            "Future Projections"
        ]
        
        for i, title in enumerate(slide_titles):
            story.append(Paragraph(title, self.styles['Heading1']))
            story.append(Spacer(1, 0.5*inch))
            
            # Add 1-2 images per slide
            for img_num in range(random.randint(1, 2)):
                img_type = random.choice(["chart", "diagram", "pattern"])
                img_buffer = self._create_sample_image(400, 250, img_type)
                story.append(RLImage(img_buffer, width=4*inch, height=2.5*inch))
                story.append(Spacer(1, 0.3*inch))
            
            # Add some bullet points
            bullet_points = [
                "Key insight from data analysis",
                "Significant trend identified in Q3", 
                "Performance exceeded expectations",
                "Strategic recommendations for next quarter"
            ]
            
            for point in bullet_points[:random.randint(2, 4)]:
                story.append(Paragraph(f"• {point}", self.styles['Normal']))
                story.append(Spacer(1, 8))
            
            if i < len(slide_titles) - 1:
                story.append(PageBreak())
        
        doc.build(story)
        return output_path
    
    def generate_mixed_content_pdf(self, filename: str, pages: int = 12) -> Path:
        """Generate a mixed content PDF (report style)."""
        output_path = self.output_dir / filename
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        story = []
        
        # Title and TOC
        story.append(Paragraph("Annual Report 2024", self.styles['Title']))
        story.append(Spacer(1, 0.5*inch))
        
        story.append(Paragraph("Table of Contents", self.styles['Heading1']))
        toc_items = [
            "1. Executive Summary ........................... 2",
            "2. Financial Performance ...................... 4", 
            "3. Market Analysis ............................ 6",
            "4. Operations Overview ........................ 8",
            "5. Future Outlook ............................. 10"
        ]
        
        for item in toc_items:
            story.append(Paragraph(item, self.styles['Normal']))
            story.append(Spacer(1, 8))
        
        story.append(PageBreak())
        
        # Executive Summary (text-heavy)
        story.append(Paragraph("1. Executive Summary", self.styles['Heading1']))
        summary_text = """
        This annual report presents our company's performance for fiscal year 2024. 
        We achieved significant growth across all key metrics, with revenue increasing 
        by 15% year-over-year and market share expanding in three key geographic regions. 
        Our strategic investments in technology and human capital have positioned us 
        well for continued growth in the coming year.
        
        Key highlights include the successful launch of our new product line, 
        establishment of partnerships in emerging markets, and implementation of 
        sustainable business practices across all operations. These achievements 
        reflect our commitment to delivering value to stakeholders while maintaining 
        our focus on innovation and operational excellence.
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(PageBreak())
        
        # Financial Performance (mixed text and charts)
        story.append(Paragraph("2. Financial Performance", self.styles['Heading1']))
        story.append(Paragraph("Revenue Growth", self.styles['Heading2']))
        
        # Add financial chart
        chart_buffer = self._create_sample_image(500, 300, "chart")
        story.append(RLImage(chart_buffer, width=5*inch, height=3*inch))
        story.append(Spacer(1, 0.3*inch))
        
        financial_text = """
        Our financial performance in 2024 exceeded expectations, with total revenue 
        reaching $2.4 billion, representing a 15% increase from the previous year. 
        This growth was driven primarily by strong performance in our core business 
        segments and successful market expansion initiatives.
        """
        story.append(Paragraph(financial_text, self.styles['Normal']))
        story.append(PageBreak())
        
        # Market Analysis (more images)
        story.append(Paragraph("3. Market Analysis", self.styles['Heading1']))
        
        # Multiple charts and diagrams
        for i in range(2):
            img_type = "chart" if i == 0 else "diagram"
            img_buffer = self._create_sample_image(400, 250, img_type)
            story.append(RLImage(img_buffer, width=4*inch, height=2.5*inch))
            story.append(Spacer(1, 0.2*inch))
        
        market_text = """
        Market conditions remained favorable throughout 2024, with sustained demand 
        in our target sectors. Competitive analysis shows we have strengthened our 
        position relative to key competitors, particularly in the premium segment.
        """
        story.append(Paragraph(market_text, self.styles['Normal']))
        story.append(PageBreak())
        
        # Operations (text-heavy again)
        story.append(Paragraph("4. Operations Overview", self.styles['Heading1']))
        operations_text = """
        Operational efficiency improvements were a key focus in 2024. We implemented 
        new automation systems that reduced processing time by 25% while maintaining 
        quality standards. Supply chain optimization initiatives resulted in cost 
        savings of $12 million annually.
        
        Our workforce grew by 8% to support expanded operations, with particular 
        emphasis on hiring in technical and customer service roles. Employee 
        satisfaction scores increased to 4.2/5.0, reflecting our continued investment 
        in workplace culture and professional development programs.
        
        Sustainability initiatives included reducing energy consumption by 15% and 
        achieving zero waste to landfill at our primary manufacturing facilities. 
        These efforts support our commitment to environmental stewardship while 
        contributing to operational cost reductions.
        """
        story.append(Paragraph(operations_text, self.styles['Normal']))
        story.append(PageBreak())
        
        # Future Outlook
        story.append(Paragraph("5. Future Outlook", self.styles['Heading1']))
        outlook_text = """
        Looking ahead to 2025, we remain optimistic about growth prospects despite 
        ongoing market uncertainties. Our strategic plan focuses on three key areas: 
        digital transformation, geographic expansion, and product innovation.
        
        Planned investments include $50 million in technology infrastructure and 
        $25 million in research and development. We expect these investments to 
        drive revenue growth of 12-18% in the coming fiscal year.
        """
        story.append(Paragraph(outlook_text, self.styles['Normal']))
        
        doc.build(story)
        return output_path
    
    def generate_all_samples(self, count_per_type: int = 2) -> List[Path]:
        """Generate all sample PDF types."""
        generated_files = []
        
        print(f"Generating {count_per_type} files of each type...")
        
        # Text-heavy samples
        for i in range(count_per_type):
            filename = f"text_academic_paper_{i+1}.pdf"
            print(f"Generating {filename}...")
            path = self.generate_text_heavy_pdf(filename, pages=random.randint(8, 15))
            generated_files.append(path)
        
        # Image-heavy samples  
        for i in range(count_per_type):
            filename = f"image_presentation_{i+1}.pdf"
            print(f"Generating {filename}...")
            path = self.generate_image_heavy_pdf(filename, pages=random.randint(6, 10))
            generated_files.append(path)
        
        # Mixed content samples
        for i in range(count_per_type):
            filename = f"mixed_report_{i+1}.pdf"
            print(f"Generating {filename}...")
            path = self.generate_mixed_content_pdf(filename, pages=random.randint(10, 16))
            generated_files.append(path)
        
        return generated_files


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate sample PDFs for benchmarking")
    parser.add_argument("--output", "-o", 
                       default="benchmarks/datasets",
                       help="Output directory for generated PDFs")
    parser.add_argument("--count", "-c", 
                       type=int, default=2,
                       help="Number of files to generate per type (default: 2)")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    generator = SamplePDFGenerator(output_dir)
    
    generated_files = generator.generate_all_samples(args.count)
    
    print(f"\nGenerated {len(generated_files)} sample PDF files:")
    for file_path in generated_files:
        size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"  {file_path.name} ({size_mb:.1f} MB)")
    
    print(f"\nFiles saved to: {output_dir}")
    print("Run benchmarks with: python benchmarks/benchmark_runner.py")


if __name__ == "__main__":
    main()
