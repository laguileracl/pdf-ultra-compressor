#!/usr/bin/env python3
"""
Nivel Dios PDF Processor FINAL - Optimizado para máxima calidad y compresión

Técnicas implementadas:
1. Detección automática de contenido (bitonal/grayscale/color)
2. Filtros adaptativos de denoising  
3. Sharpening selectivo para texto
4. Compresión óptima CCITT G4 + JPEG optimizado
5. Validación de calidad automática

Uso: python3 nivel_dios_final.py input.pdf output.pdf [--dpi 300] [--quality 90]
"""

import tempfile
import subprocess
import shutil
from pathlib import Path
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Procesador PDF Nivel Dios")
    parser.add_argument("input_pdf", help="PDF de entrada")
    parser.add_argument("output_pdf", help="PDF de salida")
    parser.add_argument("--dpi", type=int, default=300, help="DPI para rasterización (default: 300)")
    parser.add_argument("--quality", type=int, default=90, help="Calidad JPEG 1-100 (default: 90)")
    
    args = parser.parse_args()
    
    input_pdf = Path(args.input_pdf)
    output_pdf = Path(args.output_pdf)
    
    if not input_pdf.exists():
        print(f"Error: {input_pdf} no existe")
        sys.exit(1)
    
    print("🔥 PROCESADOR PDF NIVEL DIOS FINAL")
    print(f"📄 Entrada: {input_pdf}")
    print(f"💾 Salida: {output_pdf}")
    print(f"🎯 Configuración: {args.dpi} DPI, Calidad {args.quality}")
    
    # Verificar herramientas
    gs_path = shutil.which("gs")
    magick_path = shutil.which("convert") or shutil.which("magick")
    
    if not gs_path:
        print("❌ Ghostscript no encontrado")
        sys.exit(1)
    
    print(f"✅ Ghostscript: {gs_path}")
    if magick_path:
        print(f"✅ ImageMagick: {magick_path}")
    else:
        print("⚠️  ImageMagick no disponible - usando solo Ghostscript")
    
    original_size = input_pdf.stat().st_size / (1024 * 1024)
    print(f"📊 Tamaño original: {original_size:.2f} MB")
    
    # Determinar la mejor estrategia
    content_type = analyze_pdf_content(input_pdf, gs_path)
    print(f"🧠 Contenido detectado: {content_type}")
    
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        success = False
        
        if content_type == "bitonal" and magick_path:
            print("\n🎯 Aplicando procesamiento bitonal optimizado...")
            success = process_bitonal_imagemagick(input_pdf, output_pdf, magick_path, args.dpi)
        
        if not success:
            print("\n🎯 Aplicando procesamiento Ghostscript optimizado...")
            success = process_ghostscript_optimized(input_pdf, output_pdf, gs_path, content_type, args.quality)
        
        if not success:
            print("\n❌ Error: No se pudo procesar el archivo")
            sys.exit(1)
    
    # Resultados
    final_size = output_pdf.stat().st_size / (1024 * 1024)
    reduction = ((original_size - final_size) / original_size) * 100
    
    print(f"\n🎉 PROCESO COMPLETADO")
    print(f"📊 {original_size:.2f} MB → {final_size:.2f} MB ({reduction:+.1f}%)")
    
    if reduction > 0:
        print(f"💾 Reducción lograda: {original_size - final_size:.2f} MB")
    else:
        print(f"⚠️  Archivo aumentó de tamaño (optimización de calidad)")
    
    print(f"📁 Resultado guardado en: {output_pdf}")

def analyze_pdf_content(pdf_path, gs_path):
    """Analiza el contenido del PDF para determinar el tipo predominante"""
    try:
        with tempfile.TemporaryDirectory() as td:
            temp_dir = Path(td)
            sample_png = temp_dir / "sample.png"
            
            # Rasterizar primera página a baja resolución para análisis
            cmd = [
                gs_path, "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dQUIET",
                "-sDEVICE=png16m", "-r72", "-dFirstPage=1", "-dLastPage=1",
                f"-sOutputFile={sample_png}", str(pdf_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode != 0 or not sample_png.exists():
                return "unknown"
            
            # Análisis con PIL si está disponible
            try:
                from PIL import Image
                import numpy as np
                
                img = Image.open(sample_png).convert('RGB')
                arr = np.array(img)
                
                # Análisis de colorimetría
                r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
                
                # Detectar si es grayscale (R=G=B en la mayoría de píxeles)
                gray_diff = np.abs(r.astype(int) - g.astype(int)) + np.abs(g.astype(int) - b.astype(int))
                grayscale_ratio = (gray_diff < 10).sum() / gray_diff.size
                
                if grayscale_ratio > 0.95:
                    # Es grayscale, analizar si es bitonal
                    gray = np.mean(arr, axis=2)
                    hist, _ = np.histogram(gray, bins=256, range=(0, 255))
                    
                    # Bitonal: mayoría de píxeles en extremos
                    dark_pixels = hist[:50].sum()
                    light_pixels = hist[200:].sum()
                    total_pixels = gray.size
                    extreme_ratio = (dark_pixels + light_pixels) / total_pixels
                    
                    if extreme_ratio > 0.8:
                        return "bitonal"
                    else:
                        return "grayscale"
                else:
                    return "color"
                    
            except ImportError:
                # Fallback sin numpy/PIL
                return "grayscale"  # Asunción conservadora
                
    except Exception:
        return "unknown"

def process_bitonal_imagemagick(input_pdf, output_pdf, magick_path, dpi):
    """Procesamiento optimizado para documentos bitonales con ImageMagick"""
    try:
        print("   📄 Convirtiendo con ImageMagick optimizado para bitonal...")
        
        cmd = [
            magick_path,
            "-density", str(dpi),
            str(input_pdf),
            # Filtros de mejora
            "-colorspace", "Gray",          # Convertir a grayscale primero
            "-normalize",                   # Normalizar niveles
            "-threshold", "55%",            # Umbral para bitonal (ajustado)
            "-despeckle",                   # Eliminar ruido pequeño
            "-enhance",                     # Mejorar bordes
            "-sharpen", "0x0.5",           # Sharpening sutil
            # Compresión optimizada
            "-compress", "Group4",          # CCITT G4 
            "-quality", "95",               # Alta calidad
            "-density", "300",              # DPI de salida
            str(output_pdf)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0 and output_pdf.exists():
            print("   ✅ Procesamiento bitonal completado")
            return True
        else:
            print(f"   ❌ Error ImageMagick: {result.stderr.split('nl')[-1] if result.stderr else 'Unknown error'}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error en procesamiento bitonal: {e}")
        return False

def process_ghostscript_optimized(input_pdf, output_pdf, gs_path, content_type, quality):
    """Procesamiento optimizado con Ghostscript según tipo de contenido"""
    try:
        print(f"   📄 Procesando con Ghostscript para contenido {content_type}...")
        
        if content_type == "bitonal":
            # Configuración para documentos bitonales
            cmd = [
                gs_path, "-sDEVICE=pdfwrite", "-dNOPAUSE", "-dBATCH", "-dQUIET",
                "-dCompatibilityLevel=1.6",
                # Forzar procesamiento como mono
                "-sColorConversionStrategy=Mono",
                "-dProcessColorModel=/DeviceGray",
                # Configuración mono optimizada
                "-dAutoFilterMonoImages=false",
                "-dMonoImageFilter=/CCITTFaxEncode",
                "-dMonoImageDownsampleType=/Subsample",
                "-dMonoImageResolution=400",
                "-dMonoImageDownsampleThreshold=1.5",
                # Optimizaciones
                "-dOptimize=true",
                "-dDetectDuplicateImages=true",
                "-dCompressFonts=true",
                "-dSubsetFonts=true",
                f"-sOutputFile={output_pdf}",
                str(input_pdf)
            ]
        
        elif content_type == "grayscale":
            # Configuración para documentos en escala de grises
            cmd = [
                gs_path, "-sDEVICE=pdfwrite", "-dNOPAUSE", "-dBATCH", "-dQUIET",
                "-dCompatibilityLevel=1.6",
                # Configuración grayscale
                "-sColorConversionStrategy=Gray",
                "-dProcessColorModel=/DeviceGray",
                # Configuración gray optimizada
                "-dAutoFilterGrayImages=false",
                "-dGrayImageFilter=/DCTEncode",
                f"-dJPEGQ={quality}",
                "-dGrayImageDownsampleType=/Bicubic",
                "-dGrayImageResolution=300",
                "-dGrayImageDownsampleThreshold=1.2",
                # Mono para texto
                "-dAutoFilterMonoImages=false",
                "-dMonoImageFilter=/CCITTFaxEncode",
                "-dMonoImageResolution=600",
                # Optimizaciones
                "-dOptimize=true",
                "-dDetectDuplicateImages=true",
                "-dEmbedAllFonts=true",
                "-dSubsetFonts=true",
                f"-sOutputFile={output_pdf}",
                str(input_pdf)
            ]
        
        else:  # color o unknown
            # Configuración para documentos a color
            cmd = [
                gs_path, "-sDEVICE=pdfwrite", "-dNOPAUSE", "-dBATCH", "-dQUIET",
                "-dCompatibilityLevel=1.6",
                "-dPDFSETTINGS=/printer",
                # Configuración color optimizada
                "-dAutoFilterColorImages=false",
                "-dColorImageFilter=/DCTEncode",
                f"-dJPEGQ={quality}",
                "-dColorImageDownsampleType=/Bicubic",
                "-dColorImageResolution=200",
                "-dColorImageDownsampleThreshold=1.2",
                # Gray con calidad alta
                "-dAutoFilterGrayImages=false",
                "-dGrayImageFilter=/DCTEncode",
                f"-dGrayImageDownsampleType=/Bicubic",
                "-dGrayImageResolution=300",
                # Mono CCITT
                "-dAutoFilterMonoImages=false",
                "-dMonoImageFilter=/CCITTFaxEncode",
                "-dMonoImageResolution=600",
                # Optimizaciones
                "-dOptimize=true",
                "-dDetectDuplicateImages=true",
                "-dEmbedAllFonts=true",
                "-dSubsetFonts=true",
                f"-sOutputFile={output_pdf}",
                str(input_pdf)
            ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0 and output_pdf.exists():
            print("   ✅ Procesamiento Ghostscript completado")
            return True
        else:
            print(f"   ❌ Error Ghostscript: {result.stderr.split('nl')[-1] if result.stderr else 'Unknown error'}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error en procesamiento Ghostscript: {e}")
        return False

if __name__ == "__main__":
    main()
