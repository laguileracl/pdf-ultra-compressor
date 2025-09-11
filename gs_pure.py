#!/usr/bin/env python3
"""
Procesador PDF Ghostscript Puro - Optimizado para máxima compresión

Usa únicamente Ghostscript con parámetros super-optimizados para documentos escaneados.
Combina múltiples pasadas para lograr el mejor balance calidad/tamaño.

Uso: python3 gs_pure.py input.pdf output.pdf
"""

import subprocess
import shutil
from pathlib import Path
import sys
import tempfile

def main():
    if len(sys.argv) != 3:
        print("Uso: python3 gs_pure.py input.pdf output.pdf")
        sys.exit(1)
    
    input_pdf = Path(sys.argv[1])
    output_pdf = Path(sys.argv[2])
    
    if not input_pdf.exists():
        print(f"Error: {input_pdf} no existe")
        sys.exit(1)
    
    gs_path = shutil.which("gs")
    if not gs_path:
        print("❌ Ghostscript no encontrado")
        sys.exit(1)
    
    print("🔥 PROCESADOR GHOSTSCRIPT PURO")
    print(f"📄 Entrada: {input_pdf}")
    print(f"💾 Salida: {output_pdf}")
    print(f"⚙️  Ghostscript: {gs_path}")
    
    original_size = input_pdf.stat().st_size / (1024 * 1024)
    print(f"📊 Tamaño original: {original_size:.2f} MB")
    
    # Múltiples estrategias en orden de agresividad
    strategies = [
        ("ultra_bitonal", create_ultra_bitonal_config),
        ("aggressive_mono", create_aggressive_mono_config),
        ("conservative_mono", create_conservative_mono_config),
        ("fallback_screen", create_fallback_screen_config)
    ]
    
    best_result = None
    best_size = float('inf')
    
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        
        for strategy_name, config_func in strategies:
            print(f"\n🎯 Probando estrategia: {strategy_name}")
            temp_output = temp_dir / f"{strategy_name}.pdf"
            
            config = config_func()
            success = process_with_config(input_pdf, temp_output, gs_path, config)
            
            if success and temp_output.exists():
                size_mb = temp_output.stat().st_size / (1024 * 1024)
                reduction = ((original_size - size_mb) / original_size) * 100
                print(f"   ✅ {strategy_name}: {size_mb:.2f} MB ({reduction:+.1f}%)")
                
                # Validar que el archivo es válido
                if validate_pdf(temp_output, gs_path):
                    if size_mb < best_size and size_mb > 0.1:  # No archivos corruptos
                        best_size = size_mb
                        best_result = (strategy_name, temp_output)
                        print(f"   🏆 Nuevo mejor resultado!")
                else:
                    print(f"   ⚠️  PDF inválido, descartando")
            else:
                print(f"   ❌ Falló")
    
    if best_result:
        strategy_name, best_file = best_result
        shutil.copy2(best_file, output_pdf)
        final_size = output_pdf.stat().st_size / (1024 * 1024)
        reduction = ((original_size - final_size) / original_size) * 100
        
        print(f"\n🎉 PROCESO COMPLETADO")
        print(f"🏆 Estrategia ganadora: {strategy_name}")
        print(f"📊 {original_size:.2f} MB → {final_size:.2f} MB ({reduction:+.1f}%)")
        print(f"💾 Archivo guardado en: {output_pdf}")
    else:
        print("\n❌ Error: Ninguna estrategia funcionó")
        sys.exit(1)

def create_ultra_bitonal_config():
    """Configuración ultra-agresiva para documentos bitonales"""
    return [
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dNOPAUSE", "-dBATCH", "-dQUIET",
        # Forzar todo a bitonal (1-bit)
        "-sColorConversionStrategy=Mono",
        "-dProcessColorModel=/DeviceGray",
        "-dColorImageDownsampleType=/Subsample",
        "-dGrayImageDownsampleType=/Subsample",
        "-dMonoImageDownsampleType=/Subsample",
        # Configuración ultra-agresiva mono
        "-dAutoFilterMonoImages=false",
        "-dMonoImageFilter=/CCITTFaxEncode",
        "-dMonoImageResolution=200",  # Resolución reducida
        "-dMonoImageDownsampleThreshold=1.0",
        # Desactivar otras imágenes
        "-dAutoFilterColorImages=false",
        "-dColorImageFilter=/CCITTFaxEncode",
        "-dColorImageResolution=200",
        "-dAutoFilterGrayImages=false", 
        "-dGrayImageFilter=/CCITTFaxEncode",
        "-dGrayImageResolution=200",
        # Optimizaciones máximas
        "-dOptimize=true",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
        "-dEmbedAllFonts=false",  # No embeber fuentes si es posible
    ]

def create_aggressive_mono_config():
    """Configuración agresiva pero más segura"""
    return [
        "-sDEVICE=pdfwrite", 
        "-dCompatibilityLevel=1.5",
        "-dNOPAUSE", "-dBATCH", "-dQUIET",
        # Forzar mono pero permitir grays
        "-sColorConversionStrategy=Mono",
        "-dProcessColorModel=/DeviceGray",
        # Mono CCITT
        "-dAutoFilterMonoImages=false",
        "-dMonoImageFilter=/CCITTFaxEncode", 
        "-dMonoImageResolution=300",
        "-dMonoImageDownsampleThreshold=1.2",
        # Gray como CCITT también
        "-dAutoFilterGrayImages=false",
        "-dGrayImageFilter=/CCITTFaxEncode",
        "-dGrayImageResolution=300", 
        "-dGrayImageDownsampleThreshold=1.2",
        # Color deshabilitado
        "-dDownsampleColorImages=false",
        "-dEncodeColorImages=false",
        # Optimizaciones
        "-dOptimize=true",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
    ]

def create_conservative_mono_config():
    """Configuración conservadora que preserva calidad"""
    return [
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.6", 
        "-dNOPAUSE", "-dBATCH", "-dQUIET",
        # Convertir a mono de manera conservadora
        "-sColorConversionStrategy=Mono",
        "-dProcessColorModel=/DeviceGray",
        # Mono optimizado
        "-dAutoFilterMonoImages=false",
        "-dMonoImageFilter=/CCITTFaxEncode",
        "-dMonoImageResolution=400",
        "-dMonoImageDownsampleThreshold=1.5",
        # Gray con Flate (sin pérdida)
        "-dAutoFilterGrayImages=false",
        "-dGrayImageFilter=/FlateEncode",
        "-dGrayImageResolution=300",
        "-dGrayImageDownsampleThreshold=1.5",
        # Optimizaciones estándar
        "-dOptimize=true",
        "-dDetectDuplicateImages=true",
        "-dEmbedAllFonts=true",
        "-dSubsetFonts=true",
    ]

def create_fallback_screen_config():
    """Configuración de fallback usando screen preset"""
    return [
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.6",
        "-dNOPAUSE", "-dBATCH", "-dQUIET",
        "-dPDFSETTINGS=/screen",  # Preset para máxima compresión
        # Forzar mono
        "-sColorConversionStrategy=Mono",
        "-dProcessColorModel=/DeviceGray",
        # Optimizaciones adicionales
        "-dOptimize=true",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
    ]

def process_with_config(input_pdf, output_pdf, gs_path, config):
    """Procesa PDF con la configuración dada"""
    try:
        cmd = [gs_path] + config + [f"-sOutputFile={output_pdf}", str(input_pdf)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception:
        return False

def validate_pdf(pdf_path, gs_path):
    """Valida que el PDF es legible"""
    try:
        cmd = [gs_path, "-dNODISPLAY", "-dBATCH", "-dQUIET", "-dNOPAUSE", str(pdf_path)]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0
    except Exception:
        return False

if __name__ == "__main__":
    main()
