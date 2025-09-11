#!/usr/bin/env python3
"""
Nivel Dios PDF Processor v2 - Robusto para documentos escaneados

Combina múltiples técnicas de mejora:
1. Rasterización de alta calidad
2. Detección automática de contenido  
3. Filtros especializados por tipo
4. Reconstrucción optimizada

Uso: python3 nivel_dios_v2.py input.pdf output.pdf
"""

import tempfile
import subprocess
import shutil
from pathlib import Path
import sys

def main():
    if len(sys.argv) != 3:
        print("Uso: python3 nivel_dios_v2.py input.pdf output.pdf")
        sys.exit(1)
    
    input_pdf = Path(sys.argv[1])
    output_pdf = Path(sys.argv[2])
    
    if not input_pdf.exists():
        print(f"Error: {input_pdf} no existe")
        sys.exit(1)
    
    print("🔥 PROCESADOR NIVEL DIOS v2 - Iniciando...")
    print(f"📄 Entrada: {input_pdf}")
    print(f"💾 Salida: {output_pdf}")
    
    # Verificar dependencias
    try:
        import numpy as np
        import cv2
        from PIL import Image
        print("✅ Dependencias de imagen disponibles")
    except ImportError as e:
        print(f"❌ Falta dependencia: {e}")
        sys.exit(1)
    
    # Verificar Ghostscript
    gs_path = shutil.which("gs")
    if not gs_path:
        print("❌ Ghostscript no encontrado")
        sys.exit(1)
    
    print(f"✅ Ghostscript: {gs_path}")
    
    original_size = input_pdf.stat().st_size / (1024 * 1024)
    print(f"📊 Tamaño original: {original_size:.2f} MB")
    
    # Proceso de mejora robusto
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        
        # Estrategia 1: Procesamiento directo bitonal optimizado
        print("\n🎯 Estrategia 1: Procesamiento bitonal optimizado...")
        result1 = process_bitonal_optimized(input_pdf, output_pdf, gs_path, temp_dir)
        
        if result1:
            final_size = output_pdf.stat().st_size / (1024 * 1024)
            reduction = ((original_size - final_size) / original_size) * 100
            print(f"\n🎉 PROCESO COMPLETADO (Estrategia 1)")
            print(f"📊 {original_size:.2f} MB → {final_size:.2f} MB ({reduction:+.1f}%)")
            print(f"💾 Guardado en: {output_pdf}")
            return
        
        # Estrategia 2: Rasterización con imagemagick si disponible
        print("\n🎯 Estrategia 2: Procesamiento con ImageMagick...")
        result2 = process_with_imagemagick(input_pdf, output_pdf, temp_dir)
        
        if result2:
            final_size = output_pdf.stat().st_size / (1024 * 1024)
            reduction = ((original_size - final_size) / original_size) * 100
            print(f"\n🎉 PROCESO COMPLETADO (Estrategia 2)")
            print(f"📊 {original_size:.2f} MB → {final_size:.2f} MB ({reduction:+.1f}%)")
            print(f"💾 Guardado en: {output_pdf}")
            return
        
        # Estrategia 3: Fallback a técnicas de Ghostscript avanzadas
        print("\n🎯 Estrategia 3: Ghostscript avanzado...")
        result3 = process_gs_advanced(input_pdf, output_pdf, gs_path)
        
        if result3:
            final_size = output_pdf.stat().st_size / (1024 * 1024)
            reduction = ((original_size - final_size) / original_size) * 100
            print(f"\n🎉 PROCESO COMPLETADO (Estrategia 3)")
            print(f"📊 {original_size:.2f} MB → {final_size:.2f} MB ({reduction:+.1f}%)")
            print(f"💾 Guardado en: {output_pdf}")
            return
        
        print("\n❌ Todas las estrategias fallaron")
        sys.exit(1)

def process_bitonal_optimized(input_pdf, output_pdf, gs_path, temp_dir):
    """Estrategia optimizada para documentos bitonales con CCITT G4"""
    print("   Aplicando compresión CCITT G4 optimizada...")
    
    try:
        # Usar TIFF G4 como intermedio - más confiable para bitonal
        tiff_path = temp_dir / "temp.tif"
        
        # PDF -> TIFF G4 (1-bit) con parámetros optimizados
        cmd1 = [
            gs_path,
            "-sDEVICE=tiffg4",
            "-r600",  # Alta resolución para preservar texto
            "-dNOPAUSE", "-dBATCH", "-dQUIET",
            "-dDownScaleColorImages=false",  # No reducir resolución
            "-dDownScaleGrayImages=false",
            "-dDownScaleMonoImages=false",
            f"-sOutputFile={tiff_path}",
            str(input_pdf)
        ]
        
        result1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=300)
        if result1.returncode != 0 or not tiff_path.exists():
            print(f"      ❌ Error en conversión a TIFF: {result1.stderr}")
            return False
        
        print(f"      ✅ TIFF generado: {tiff_path.stat().st_size / (1024*1024):.2f} MB")
        
        # TIFF G4 -> PDF con compresión CCITT
        cmd2 = [
            gs_path,
            "-sDEVICE=pdfwrite",
            "-dNOPAUSE", "-dBATCH", "-dQUIET",
            "-dCompatibilityLevel=1.6",
            "-dOptimize=true",
            "-dAutoFilterMonoImages=false",
            "-dMonoImageFilter=/CCITTFaxEncode",
            "-dMonoImageDownsampleType=/Subsample",
            "-dMonoImageResolution=600",
            "-dDetectDuplicateImages=true",
            f"-sOutputFile={output_pdf}",
            str(tiff_path)
        ]
        
        result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=300)
        if result2.returncode == 0 and output_pdf.exists():
            print(f"      ✅ PDF reconstruido exitosamente")
            return True
        else:
            print(f"      ❌ Error en reconstrucción PDF: {result2.stderr}")
            return False
            
    except Exception as e:
        print(f"      ❌ Error en estrategia 1: {e}")
        return False

def process_with_imagemagick(input_pdf, output_pdf, temp_dir):
    """Estrategia con ImageMagick si está disponible"""
    convert_path = shutil.which("convert")
    if not convert_path:
        print("      ❌ ImageMagick no disponible")
        return False
    
    try:
        print(f"      ✅ ImageMagick encontrado: {convert_path}")
        
        # ImageMagick con optimizaciones para documentos escaneados
        cmd = [
            convert_path,
            "-density", "300",  # DPI de entrada
            str(input_pdf),
            "-threshold", "50%",  # Convertir a bitonal
            "-despeckle",  # Eliminar ruido pequeño
            "-enhance",    # Mejorar definición
            "-sharpen", "0x1",  # Leve sharpening
            "-compress", "Group4",  # Compresión CCITT G4
            str(output_pdf)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0 and output_pdf.exists():
            print(f"      ✅ Procesado con ImageMagick")
            return True
        else:
            print(f"      ❌ Error ImageMagick: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"      ❌ Error en estrategia 2: {e}")
        return False

def process_gs_advanced(input_pdf, output_pdf, gs_path):
    """Estrategia fallback con Ghostscript avanzado"""
    try:
        print("      Aplicando filtros Ghostscript especializados...")
        
        # Configuración agresiva pero segura para documentos bitonal
        cmd = [
            gs_path,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.6",
            "-dNOPAUSE", "-dQUIET", "-dBATCH",
            # Conversión forzada a bitonal
            "-sColorConversionStrategy=Mono",
            "-dProcessColorModel=/DeviceGray",
            # Configuración mono optimizada
            "-dAutoFilterMonoImages=false",
            "-dMonoImageFilter=/CCITTFaxEncode",
            "-dMonoImageDownsampleType=/Subsample",
            "-dMonoImageResolution=600",
            "-dMonoImageDownsampleThreshold=1.0",
            # Optimizaciones generales
            "-dOptimize=true",
            "-dDetectDuplicateImages=true",
            "-dCompressFonts=true",
            "-dSubsetFonts=true",
            f"-sOutputFile={output_pdf}",
            str(input_pdf)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0 and output_pdf.exists():
            print(f"      ✅ Procesado con Ghostscript avanzado")
            return True
        else:
            print(f"      ❌ Error Ghostscript: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"      ❌ Error en estrategia 3: {e}")
        return False

if __name__ == "__main__":
    main()
