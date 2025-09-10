"""
Compresor PDF de Primera Calidad
Motor principal con algoritmos avanzados de compresión
"""

import fitz  # PyMuPDF
import io
import os
import tempfile
import subprocess
from PIL import Image, ImageFilter, ImageEnhance
import cv2
import numpy as np
from typing import Tuple, Dict, List, Optional
import pikepdf
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompresorPDFAvanzado:
    """
    Compresor PDF de primera calidad que utiliza múltiples tecnologías
    para lograr la máxima compresión sin pérdida de calidad visual.
    """
    
    def __init__(self):
        self.estrategias_compresion = {
            'conservador': {'calidad_imagen': 95, 'dpi_min': 300, 'compresion_texto': False},
            'balanceado': {'calidad_imagen': 85, 'dpi_min': 200, 'compresion_texto': True},
            'agresivo': {'calidad_imagen': 75, 'dpi_min': 150, 'compresion_texto': True},
            'adaptativo': {'calidad_imagen': 'auto', 'dpi_min': 'auto', 'compresion_texto': 'auto'}
        }
    
    def comprimir_pdf(self, 
                     archivo_entrada: str, 
                     archivo_salida: str, 
                     estrategia: str = 'adaptativo',
                     preservar_metadatos: bool = True) -> Dict[str, float]:
        """
        Comprime un PDF utilizando algoritmos avanzados.
        
        Args:
            archivo_entrada: Ruta del PDF original
            archivo_salida: Ruta del PDF comprimido
            estrategia: Nivel de compresión ('conservador', 'balanceado', 'agresivo', 'adaptativo')
            preservar_metadatos: Si mantener metadatos del documento
            
        Returns:
            Diccionario con estadísticas de compresión
        """
        logger.info(f"Iniciando compresión con estrategia: {estrategia}")
        
        # Verificar archivo de entrada
        if not os.path.exists(archivo_entrada):
            raise FileNotFoundError(f"Archivo no encontrado: {archivo_entrada}")
        
        tamaño_original = os.path.getsize(archivo_entrada)
        
        try:
            # Abrir documento PDF
            doc = fitz.open(archivo_entrada)
            
            # Analizar contenido si es estrategia adaptativa
            if estrategia == 'adaptativo':
                config = self._analizar_contenido(doc)
            else:
                config = self.estrategias_compresion[estrategia]
            
            # Aplicar optimizaciones
            doc_optimizado = self._optimizar_documento(doc, config)
            
            # Comprimir imágenes
            self._comprimir_imagenes(doc_optimizado, config)
            
            # Optimizar fuentes y texto
            self._optimizar_texto(doc_optimizado, config)
            
            # Guardar documento optimizado
            doc_optimizado.save(archivo_salida, 
                              garbage=4,  # Máxima limpieza
                              deflate=True,  # Compresión DEFLATE
                              clean=True,  # Limpiar estructura
                              sanitize=True,  # Sanitizar contenido
                              pretty=False,  # Sin formato bonito
                              linear=True)  # Optimizar para web
            
            doc.close()
            doc_optimizado.close()
            
            # Aplicar optimización adicional con qpdf
            self._optimizar_con_qpdf(archivo_salida)
            
            # Calcular estadísticas
            tamaño_final = os.path.getsize(archivo_salida)
            reduccion = ((tamaño_original - tamaño_final) / tamaño_original) * 100
            
            estadisticas = {
                'tamaño_original_mb': tamaño_original / (1024 * 1024),
                'tamaño_final_mb': tamaño_final / (1024 * 1024),
                'reduccion_porcentaje': reduccion,
                'estrategia_usada': estrategia
            }
            
            logger.info(f"Compresión completada: {reduccion:.1f}% de reducción")
            return estadisticas
            
        except Exception as e:
            logger.error(f"Error durante la compresión: {str(e)}")
            raise
    
    def _analizar_contenido(self, doc: fitz.Document) -> Dict:
        """
        Analiza el contenido del PDF para determinar la mejor estrategia.
        """
        logger.info("Analizando contenido del documento...")
        
        total_paginas = len(doc)
        imagenes_por_pagina = []
        texto_por_pagina = []
        
        for num_pagina in range(min(10, total_paginas)):  # Analizar hasta 10 páginas
            pagina = doc[num_pagina]
            
            # Contar imágenes
            imagenes = pagina.get_images()
            imagenes_por_pagina.append(len(imagenes))
            
            # Analizar texto
            texto = pagina.get_text()
            texto_por_pagina.append(len(texto))
        
        # Determinar configuración óptima
        avg_imagenes = sum(imagenes_por_pagina) / len(imagenes_por_pagina) if imagenes_por_pagina else 0
        avg_texto = sum(texto_por_pagina) / len(texto_por_pagina) if texto_por_pagina else 0
        
        if avg_imagenes > 5:  # Documento rico en imágenes
            return {'calidad_imagen': 80, 'dpi_min': 200, 'compresion_texto': True}
        elif avg_texto > 1000:  # Documento rico en texto
            return {'calidad_imagen': 90, 'dpi_min': 250, 'compresion_texto': True}
        else:  # Documento mixto
            return {'calidad_imagen': 85, 'dpi_min': 200, 'compresion_texto': True}
    
    def _optimizar_documento(self, doc: fitz.Document, config: Dict) -> fitz.Document:
        """
        Aplica optimizaciones generales al documento.
        """
        logger.info("Optimizando estructura del documento...")
        
        # Crear nuevo documento optimizado
        doc_opt = fitz.open()
        
        for num_pagina in range(len(doc)):
            pagina_orig = doc[num_pagina]
            
            # Copiar página
            doc_opt.new_page(width=pagina_orig.rect.width, height=pagina_orig.rect.height)
            pagina_nueva = doc_opt[-1]
            
            # Obtener contenido de la página
            pagina_nueva.show_pdf_page(pagina_nueva.rect, doc, num_pagina)
        
        return doc_opt
    
    def _comprimir_imagenes(self, doc: fitz.Document, config: Dict):
        """
        Comprime las imágenes del documento usando algoritmos avanzados.
        """
        logger.info("Comprimiendo imágenes...")
        
        for num_pagina in range(len(doc)):
            pagina = doc[num_pagina]
            imagenes = pagina.get_images()
            
            for i, img in enumerate(imagenes):
                try:
                    # Extraer imagen
                    xref = img[0]
                    imagen_dict = doc.extract_image(xref)
                    imagen_data = imagen_dict["image"]
                    
                    # Cargar imagen con PIL
                    imagen_pil = Image.open(io.BytesIO(imagen_data))
                    
                    # Aplicar compresión inteligente
                    imagen_comprimida = self._comprimir_imagen_inteligente(imagen_pil, config)
                    
                    # Guardar imagen comprimida de vuelta
                    img_bytes = io.BytesIO()
                    imagen_comprimida.save(img_bytes, format='JPEG', 
                                         quality=config.get('calidad_imagen', 85),
                                         optimize=True)
                    
                    # Reemplazar imagen en el PDF
                    doc.update_stream(xref, img_bytes.getvalue())
                    
                except Exception as e:
                    logger.warning(f"No se pudo comprimir imagen {i} en página {num_pagina}: {e}")
                    continue
    
    def _comprimir_imagen_inteligente(self, imagen: Image.Image, config: Dict) -> Image.Image:
        """
        Aplica compresión inteligente basada en el contenido de la imagen.
        """
        # Convertir a array numpy para análisis
        img_array = np.array(imagen)
        
        # Detectar tipo de contenido
        if self._es_texto_escaneado(img_array):
            # Para texto escaneado, usar técnicas especiales
            return self._optimizar_texto_escaneado(imagen)
        elif self._es_fotografia(img_array):
            # Para fotografías, optimizar diferente
            return self._optimizar_fotografia(imagen, config)
        else:
            # Para contenido mixto
            return self._optimizar_mixto(imagen, config)
    
    def _es_texto_escaneado(self, img_array: np.ndarray) -> bool:
        """Detecta si la imagen contiene principalmente texto escaneado."""
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        
        # Calcular distribución de intensidades
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        # El texto escaneado tiende a tener distribución bimodal (blanco y negro)
        return np.sum(hist[:50]) + np.sum(hist[200:]) > np.sum(hist[50:200])
    
    def _es_fotografia(self, img_array: np.ndarray) -> bool:
        """Detecta si la imagen es una fotografía."""
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        
        # Las fotografías tienen más variación de gradientes
        gradientes = cv2.Sobel(gray, cv2.CV_64F, 1, 1, ksize=3)
        variacion = np.std(gradientes)
        
        return variacion > 30  # Umbral experimental
    
    def _optimizar_texto_escaneado(self, imagen: Image.Image) -> Image.Image:
        """Optimiza imágenes que contienen texto escaneado."""
        # Convertir a escala de grises si es necesario
        if imagen.mode != 'L':
            imagen = imagen.convert('L')
        
        # Aplicar filtro para mejorar el texto
        imagen = imagen.filter(ImageFilter.SHARPEN)
        
        # Ajustar contraste
        enhancer = ImageEnhance.Contrast(imagen)
        imagen = enhancer.enhance(1.2)
        
        return imagen
    
    def _optimizar_fotografia(self, imagen: Image.Image, config: Dict) -> Image.Image:
        """Optimiza fotografías manteniendo calidad visual."""
        # Reducir ruido si es necesario
        img_array = np.array(imagen)
        if len(img_array.shape) == 3:
            img_denoised = cv2.fastNlMeansDenoisingColored(img_array, None, 10, 10, 7, 21)
            imagen = Image.fromarray(img_denoised)
        
        return imagen
    
    def _optimizar_mixto(self, imagen: Image.Image, config: Dict) -> Image.Image:
        """Optimiza contenido mixto."""
        # Aplicar un ligero filtro de nitidez
        return imagen.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
    
    def _optimizar_texto(self, doc: fitz.Document, config: Dict):
        """Optimiza fuentes y texto."""
        if not config.get('compresion_texto', False):
            return
        
        logger.info("Optimizando texto y fuentes...")
        # Aquí se pueden implementar optimizaciones de fuentes
        # Por ahora, dejamos que PyMuPDF maneje esto automáticamente
    
    def _optimizar_con_qpdf(self, archivo_pdf: str):
        """Aplica optimización adicional usando qpdf."""
        try:
            archivo_temp = archivo_pdf + ".temp"
            
            # Comando qpdf para optimización
            cmd = [
                "qpdf",
                "--optimize-images",
                "--compress-streams=y",
                "--recompress-flate",
                "--object-streams=generate",
                archivo_pdf,
                archivo_temp
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Reemplazar archivo original
                os.replace(archivo_temp, archivo_pdf)
                logger.info("Optimización con qpdf completada")
            else:
                logger.warning(f"qpdf no disponible o falló: {result.stderr}")
                if os.path.exists(archivo_temp):
                    os.remove(archivo_temp)
                    
        except FileNotFoundError:
            logger.warning("qpdf no está instalado, saltando optimización adicional")
        except Exception as e:
            logger.warning(f"Error en optimización qpdf: {e}")

def comprimir_pdf_simple(entrada: str, salida: str, estrategia: str = 'adaptativo') -> Dict[str, float]:
    """
    Función simple para comprimir un PDF.
    
    Args:
        entrada: Ruta del archivo PDF original
        salida: Ruta del archivo PDF comprimido
        estrategia: Estrategia de compresión
    
    Returns:
        Estadísticas de compresión
    """
    compresor = CompresorPDFAvanzado()
    return compresor.comprimir_pdf(entrada, salida, estrategia)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Uso: python compresor_avanzado.py archivo_entrada.pdf archivo_salida.pdf [estrategia]")
        print("Estrategias: conservador, balanceado, agresivo, adaptativo")
        sys.exit(1)
    
    entrada = sys.argv[1]
    salida = sys.argv[2]
    estrategia = sys.argv[3] if len(sys.argv) > 3 else 'adaptativo'
    
    try:
        stats = comprimir_pdf_simple(entrada, salida, estrategia)
        print(f"\n🎉 Compresión completada exitosamente!")
        print(f"📊 Tamaño original: {stats['tamaño_original_mb']:.2f} MB")
        print(f"📊 Tamaño final: {stats['tamaño_final_mb']:.2f} MB")
        print(f"📊 Reducción: {stats['reduccion_porcentaje']:.1f}%")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
