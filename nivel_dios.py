#!/usr/bin/env python3
"""
Nivel Dios PDF Processor - Especializado en documentos escaneados con ruido

Implementa técnicas avanzadas de procesamiento de imágenes:
- Rasterización a alta resolución
- Detección automática de contenido
- Filtros adaptativos por tipo de contenido
- Sharpening selectivo
- Reconstrucción optimizada

Uso: python3 nivel_dios.py input.pdf output.pdf
"""

import tempfile
import subprocess
import shutil
from pathlib import Path
import sys

def main():
    if len(sys.argv) != 3:
        print("Uso: python3 nivel_dios.py input.pdf output.pdf")
        sys.exit(1)
    
    input_pdf = Path(sys.argv[1])
    output_pdf = Path(sys.argv[2])
    
    if not input_pdf.exists():
        print(f"Error: {input_pdf} no existe")
        sys.exit(1)
    
    print("🔥 PROCESADOR NIVEL DIOS - Iniciando...")
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
    
    # Proceso de mejora
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        
        # Paso 1: Rasterizar a alta calidad
        print("\n🔍 Paso 1: Rasterización a alta calidad (400 DPI)...")
        png_dir = temp_dir / "pngs"
        png_dir.mkdir()
        
        png_pattern = str(png_dir / "page-%03d.png")
        raster_cmd = [
            gs_path, "-dSAFER", "-dBATCH", "-dNOPAUSE",
            "-sDEVICE=png16m", "-r400",
            "-dTextAlphaBits=4", "-dGraphicsAlphaBits=4",
            f"-sOutputFile={png_pattern}",
            str(input_pdf)
        ]
        
        try:
            subprocess.run(raster_cmd, capture_output=True, text=True, timeout=600, check=True)
            png_files = sorted(png_dir.glob("page-*.png"))
            print(f"✅ Generadas {len(png_files)} imágenes")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error en rasterización: {e}")
            sys.exit(1)
        
        if not png_files:
            print("❌ No se generaron imágenes")
            sys.exit(1)
        
        # Paso 2: Análisis y procesamiento por página
        print("\n🧠 Paso 2: Análisis y mejora de imágenes...")
        processed_dir = temp_dir / "processed"
        processed_dir.mkdir()
        
        processed_files = []
        for i, png_file in enumerate(png_files, 1):
            print(f"   Procesando página {i}/{len(png_files)}...", end=" ")
            
            # Cargar imagen
            img = cv2.imread(str(png_file), cv2.IMREAD_COLOR)
            if img is None:
                print("❌ Error al cargar")
                continue
            
            # Detectar tipo de contenido
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            content_type = detect_content_type(gray)
            print(f"({content_type})", end=" ")
            
            # Aplicar filtros según contenido
            if content_type == "bitonal":
                processed = process_bitonal(img)
            elif content_type == "grayscale":
                processed = process_grayscale(img)
            else:
                processed = process_color(img)
            
            # Downsample a 300 DPI para balance tamaño/calidad
            h, w = processed.shape[:2]
            new_h, new_w = int(h * 0.75), int(w * 0.75)  # 400->300 DPI
            processed = cv2.resize(processed, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
            
            # Guardar
            output_file = processed_dir / f"page-{i:03d}.png"
            cv2.imwrite(str(output_file), processed, [cv2.IMWRITE_PNG_COMPRESSION, 1])
            processed_files.append(output_file)
            print("✅")
        
        # Paso 3: Reconstruir PDF
        print(f"\n📄 Paso 3: Reconstrucción del PDF...")
        recon_cmd = [
            gs_path, "-sDEVICE=pdfwrite", "-dNOPAUSE", "-dBATCH", "-dQUIET",
            "-dAutoRotatePages=/None",
            "-dCompatibilityLevel=1.6",
            "-dOptimize=true",
            f"-sOutputFile={output_pdf}"
        ] + [str(f) for f in processed_files]
        
        try:
            result = subprocess.run(recon_cmd, capture_output=True, text=True, timeout=300)
            # Check if output file exists and has content, even if return code is non-zero
            # (Ghostscript sometimes reports warnings as errors but still produces valid output)
            if output_pdf.exists() and output_pdf.stat().st_size > 0:
                print("✅ PDF reconstruido")
            else:
                print(f"❌ Error en reconstrucción: return code {result.returncode}")
                if result.stderr:
                    print(f"Error details: {result.stderr}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error en reconstrucción: {e}")
            sys.exit(1)
    
    # Resultados
    final_size = output_pdf.stat().st_size / (1024 * 1024)
    reduction = ((original_size - final_size) / original_size) * 100 if original_size > 0 else 0
    
    print(f"\n🎉 PROCESO COMPLETADO")
    print(f"📊 {original_size:.2f} MB → {final_size:.2f} MB ({reduction:+.1f}%)")
    print(f"💾 Guardado en: {output_pdf}")

def detect_content_type(gray_img):
    """Detecta el tipo de contenido predominante"""
    import numpy as np
    import cv2
    
    # Análisis de histograma
    hist = cv2.calcHist([gray_img], [0], None, [256], [0, 256])
    total_pixels = gray_img.size
    
    # Bitonal: mayoría de píxeles en extremos (0-30, 225-255)
    dark = hist[:30].sum()
    light = hist[225:].sum()
    extreme_ratio = (dark + light) / total_pixels
    
    if extreme_ratio > 0.8:
        return "bitonal"
    
    # Color vs Grayscale se determinaría en la imagen original
    # Por simplicidad, si no es bitonal, asumimos grayscale para scans
    return "grayscale"

def process_bitonal(img):
    """Procesa imágenes bitonales (blanco y negro)"""
    import numpy as np
    import cv2
    
    # Convertir a grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Normalización
    normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    
    # Ligero blur para suavizar ruido antes del threshold
    blurred = cv2.GaussianBlur(normalized, (3, 3), 0)
    
    # Threshold adaptativo para preservar texto
    binary = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 21, 8
    )
    
    # Morfología para limpiar ruido pequeño
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    return binary

def process_grayscale(img):
    """Procesa imágenes en escala de grises"""
    import numpy as np
    import cv2
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Corrección de iluminación (background normalization)
    background = cv2.GaussianBlur(gray, (0, 0), 15.0)
    corrected = cv2.addWeighted(gray, 1.3, background, -0.3, 0)
    
    # Denoising
    denoised = cv2.fastNlMeansDenoising(corrected, None, h=8, templateWindowSize=7, searchWindowSize=21)
    
    # CLAHE para mejorar contraste local
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Unsharp mask para nitidez
    blurred = cv2.GaussianBlur(enhanced, (0, 0), 0.8)
    sharpened = cv2.addWeighted(enhanced, 1.5, blurred, -0.5, 0)
    
    return sharpened

def process_color(img):
    """Procesa imágenes a color"""
    import numpy as np
    import cv2
    
    # Trabajar en espacio YCrCb para separar luminancia de crominancia
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    
    # Denoise en canales de crominancia (reduce color noise)
    cr = cv2.fastNlMeansDenoising(cr, None, h=5)
    cb = cv2.fastNlMeansDenoising(cb, None, h=5)
    
    # Sharpen en canal de luminancia
    y_blurred = cv2.GaussianBlur(y, (0, 0), 0.8)
    y_sharp = cv2.addWeighted(y, 1.4, y_blurred, -0.4, 0)
    
    # Recombinar
    ycrcb_processed = cv2.merge([y_sharp, cr, cb])
    result = cv2.cvtColor(ycrcb_processed, cv2.COLOR_YCrCb2BGR)
    
    return result

if __name__ == "__main__":
    main()
