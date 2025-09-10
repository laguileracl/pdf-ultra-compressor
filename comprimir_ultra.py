#!/usr/bin/env python3
"""
Compresor PDF Ultra-Optimizado
Sistema automático de compresión por línea de comandos
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import argparse
import tempfile
import time
from typing import List, Dict, Tuple

class CompresorPDFUltra:
    """Compresor PDF ultra-optimizado usando las mejores herramientas disponibles."""
    
    def __init__(self, carpeta_input: str = "input", carpeta_output: str = "output"):
        self.carpeta_input = Path(carpeta_input)
        self.carpeta_output = Path(carpeta_output)
        
        # Crear carpetas si no existen
        self.carpeta_input.mkdir(exist_ok=True)
        self.carpeta_output.mkdir(exist_ok=True)
        
        print(f"📁 Carpeta de entrada: {self.carpeta_input.absolute()}")
        print(f"📁 Carpeta de salida: {self.carpeta_output.absolute()}")
    
    def procesar_todos_los_pdfs(self) -> List[Dict]:
        """Procesa todos los PDFs en la carpeta de entrada."""
        pdfs = list(self.carpeta_input.glob("*.pdf"))
        
        if not pdfs:
            print("⚠️  No se encontraron archivos PDF en la carpeta de entrada")
            return []
        
        print(f"🔍 Encontrados {len(pdfs)} archivo(s) PDF para procesar")
        
        resultados = []
        
        for pdf in pdfs:
            print(f"\n🚀 Procesando: {pdf.name}")
            print("=" * 50)
            
            resultado = self.comprimir_pdf_ultra(pdf)
            resultados.append(resultado)
            
            # Mover archivo procesado a una subcarpeta
            self._mover_archivo_procesado(pdf)
        
        return resultados
    
    def comprimir_pdf_ultra(self, archivo_pdf: Path) -> Dict:
        """Aplica compresión ultra-optimizada a un PDF."""
        
        tamaño_original = archivo_pdf.stat().st_size / (1024 * 1024)
        tamaño_bytes_original = archivo_pdf.stat().st_size
        nombre_salida = self.carpeta_output / f"{archivo_pdf.stem}_ultra_optimizado.pdf"
        
        print(f"📊 Tamaño original: {tamaño_original:.2f} MB")
        
        # Lista para guardar todos los intentos de compresión
        candidatos = []
        
        try:
            # Paso 1: Múltiples intentos con Ghostscript
            archivos_gs = self._comprimir_con_ghostscript_multiple(archivo_pdf)
            candidatos.extend(archivos_gs)
            
            # Paso 2: Optimización con qpdf sobre el original y mejores candidatos
            for candidato in [archivo_pdf] + candidatos[:2]:  # Original + 2 mejores
                archivo_qpdf = self._optimizar_con_qpdf(candidato)
                if archivo_qpdf:
                    candidatos.append(archivo_qpdf)
            
            # Paso 3: PDFtk sobre los mejores candidatos
            for candidato in candidatos[:3]:  # 3 mejores
                archivo_pdftk = self._comprimir_con_pdftk(candidato)
                if archivo_pdftk:
                    candidatos.append(archivo_pdftk)
            
            # Encontrar el mejor resultado (más pequeño)
            mejor_archivo = self._encontrar_mejor_compresion(archivo_pdf, candidatos)
            
            # Solo proceder si hay mejora real
            if mejor_archivo and mejor_archivo.stat().st_size < tamaño_bytes_original:
                shutil.copy2(mejor_archivo, nombre_salida)
                tamaño_final = nombre_salida.stat().st_size / (1024 * 1024)
                reduccion = ((tamaño_original - tamaño_final) / tamaño_original) * 100
                
                print(f"✅ Compresión exitosa!")
                print(f"📊 Tamaño final: {tamaño_final:.2f} MB")
                print(f"📊 Reducción: {reduccion:.1f}%")
                
            else:
                # Si no hay mejora, copiar el original
                print("⚠️  Ninguna herramienta logró reducir el tamaño")
                print("📄 Copiando archivo original (sin cambios)")
                shutil.copy2(archivo_pdf, nombre_salida)
                tamaño_final = tamaño_original
                reduccion = 0
            
            # Limpiar archivos temporales
            for temp_file in candidatos:
                if temp_file and temp_file != archivo_pdf and temp_file.exists():
                    try:
                        temp_file.unlink()
                    except:
                        pass  # Ignorar errores de limpieza
            
            resultado = {
                'archivo_original': archivo_pdf.name,
                'archivo_final': nombre_salida.name,
                'tamaño_original_mb': tamaño_original,
                'tamaño_final_mb': tamaño_final,
                'reduccion_porcentaje': reduccion,
                'herramientas_usadas': self._get_herramientas_disponibles()
            }
            
            print(f"💾 Guardado como: {nombre_salida.name}")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error procesando {archivo_pdf.name}: {e}")
            return {
                'archivo_original': archivo_pdf.name,
                'error': str(e),
                'tamaño_original_mb': tamaño_original
            }
    
    def _comprimir_con_ghostscript_multiple(self, archivo_pdf: Path) -> List[Path]:
        """Múltiples intentos de compresión con Ghostscript usando diferentes configuraciones."""
        if not shutil.which('gs'):
            print("⚠️  Ghostscript no disponible, saltando...")
            return []
        
        print("🔧 Probando múltiples configuraciones de Ghostscript...")
        
        candidatos = []
        configuraciones = [
            {
                'nombre': 'alta_calidad (preserva nitidez)',
                'settings': '/printer',
                'color_res': '300',
                'gray_res': '300',
                'mono_res': '600',
                'prioridad': 1  # Mayor prioridad = mejor calidad
            },
            {
                'nombre': 'ebook (equilibrado)',
                'settings': '/ebook',
                'color_res': '200',
                'gray_res': '200',
                'mono_res': '600',
                'prioridad': 2
            },
            {
                'nombre': 'compresion_moderada',
                'settings': '/prepress',
                'color_res': '250',
                'gray_res': '250',
                'mono_res': '800',
                'prioridad': 3
            }
        ]
        
        for i, config in enumerate(configuraciones):
            temp_file = Path(tempfile.mktemp(suffix=f'_gs_{i}.pdf'))
            
            cmd = [
                'gs',
                '-sDEVICE=pdfwrite',
                '-dCompatibilityLevel=1.4',
                f'-dPDFSETTINGS={config["settings"]}',
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
                f'-dColorImageResolution={config["color_res"]}',
                f'-dGrayImageResolution={config["gray_res"]}',
                f'-dMonoImageResolution={config["mono_res"]}',
                '-dColorImageDownsampleType=/Bicubic',
                '-dGrayImageDownsampleType=/Bicubic',
                '-dMonoImageDownsampleType=/Bicubic',
                '-dColorImageDownsampleThreshold=1.5',  # Más conservador
                '-dGrayImageDownsampleThreshold=1.5',   # Más conservador
                '-dMonoImageDownsampleThreshold=1.5',   # Más conservador
                '-dOptimize=true',
                '-dEmbedAllFonts=true',
                '-dSubsetFonts=true',
                '-dCompressFonts=true',
                '-dDetectDuplicateImages=true',
                '-dPreserveAnnots=true',               # Preservar anotaciones
                '-dPreserveMarkedContent=true',        # Preservar contenido marcado
                '-dDoThumbnails=false',                # No generar miniaturas
                '-dCreateJobTicket=false',             # No crear job ticket
                '-dPreserveHalftoneInfo=true',         # Preservar info de medios tonos
                '-dTransferFunctionInfo=/Preserve',    # Preservar funciones de transferencia
                '-dAutoRotatePages=/None',
                f'-sOutputFile={temp_file}',
                str(archivo_pdf)
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0 and temp_file.exists():
                    tamaño_mb = temp_file.stat().st_size / (1024*1024)
                    print(f"  ✅ {config['nombre']}: {tamaño_mb:.2f} MB")
                    candidatos.append(temp_file)
                else:
                    print(f"  ❌ {config['nombre']}: falló")
                    if temp_file.exists():
                        temp_file.unlink()
            except Exception as e:
                print(f"  ❌ {config['nombre']}: error - {e}")
                if temp_file.exists():
                    temp_file.unlink()
        
        return candidatos
    
    def _comprimir_con_ghostscript(self, archivo_pdf: Path) -> Path:
        """Método legacy - ahora usa el método múltiple."""
        candidatos = self._comprimir_con_ghostscript_multiple(archivo_pdf)
        return candidatos[0] if candidatos else None
    
    def _optimizar_con_qpdf(self, archivo_pdf: Path) -> Path:
        """Optimiza usando qpdf si está disponible."""
        if not shutil.which('qpdf'):
            print("⚠️  qpdf no disponible, saltando...")
            return None
        
        print("🔧 Optimizando con qpdf...")
        
        temp_file = Path(tempfile.mktemp(suffix='_qpdf.pdf'))
        
        cmd = [
            'qpdf',
            '--optimize-images',
            '--compress-streams=y',
            '--recompress-flate',
            '--object-streams=generate',
            '--normalize-content=y',
            '--linearize',
            str(archivo_pdf),
            str(temp_file)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0 and temp_file.exists():
                print(f"✅ qpdf: {temp_file.stat().st_size / (1024*1024):.2f} MB")
                return temp_file
            else:
                print(f"⚠️  qpdf falló: {result.stderr}")
                if temp_file.exists():
                    temp_file.unlink()
        except subprocess.TimeoutExpired:
            print("⚠️  qpdf timeout")
            if temp_file.exists():
                temp_file.unlink()
        except Exception as e:
            print(f"⚠️  Error con qpdf: {e}")
            if temp_file.exists():
                temp_file.unlink()
        
        return None
    
    def _comprimir_con_pdftk(self, archivo_pdf: Path) -> Path:
        """Comprime usando PDFtk si está disponible."""
        if not shutil.which('pdftk'):
            print("⚠️  PDFtk no disponible, saltando...")
            return None
        
        print("🔧 Comprimiendo con PDFtk...")
        
        temp_file = Path(tempfile.mktemp(suffix='_pdftk.pdf'))
        
        cmd = [
            'pdftk',
            str(archivo_pdf),
            'output',
            str(temp_file),
            'compress'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0 and temp_file.exists():
                print(f"✅ PDFtk: {temp_file.stat().st_size / (1024*1024):.2f} MB")
                return temp_file
            else:
                print(f"⚠️  PDFtk falló: {result.stderr}")
                if temp_file.exists():
                    temp_file.unlink()
        except subprocess.TimeoutExpired:
            print("⚠️  PDFtk timeout")
            if temp_file.exists():
                temp_file.unlink()
        except Exception as e:
            print(f"⚠️  Error con PDFtk: {e}")
            if temp_file.exists():
                temp_file.unlink()
        
        return None
    
    def _encontrar_mejor_compresion(self, archivo_original: Path, candidatos: List[Path]) -> Path:
        """Encuentra el archivo con mejor balance entre compresión y calidad."""
        if not candidatos:
            return None
        
        tamaño_original = archivo_original.stat().st_size
        mejor_archivo = None
        mejor_puntuacion = -1
        
        # Umbrales de calidad
        MIN_REDUCCION_ACEPTABLE = 10  # Mínimo 10% de reducción
        MAX_REDUCCION_AGRESIVA = 70   # Máximo 70% (evitar pérdida excesiva)
        
        print("🔍 Evaluando resultados de compresión:")
        print(f"   📄 Original: {tamaño_original / (1024*1024):.2f} MB")
        
        for i, candidato in enumerate(candidatos):
            if candidato and candidato.exists():
                tamaño = candidato.stat().st_size
                reduccion = ((tamaño_original - tamaño) / tamaño_original) * 100
                
                # Calcular puntuación basada en balance calidad/compresión
                if reduccion < MIN_REDUCCION_ACEPTABLE:
                    puntuacion = 0  # Muy poca reducción
                elif reduccion > MAX_REDUCCION_AGRESIVA:
                    puntuacion = 50 - (reduccion - MAX_REDUCCION_AGRESIVA)  # Penalizar exceso
                else:
                    # Zona óptima: premiar reducción moderada
                    puntuacion = reduccion + (40 - abs(reduccion - 40))
                
                # Bonificación por orden de prioridad (las primeras configuraciones son mejores)
                bonificacion_calidad = max(0, 20 - (i * 5))
                puntuacion_final = puntuacion + bonificacion_calidad
                
                print(f"   📄 Candidato {i+1}: {tamaño / (1024*1024):.2f} MB ({reduccion:+.1f}%) - Puntuación: {puntuacion_final:.1f}")
                
                if puntuacion_final > mejor_puntuacion:
                    mejor_puntuacion = puntuacion_final
                    mejor_archivo = candidato
        
        if mejor_archivo:
            tamaño_final = mejor_archivo.stat().st_size
            reduccion_final = ((tamaño_original - tamaño_final) / tamaño_original) * 100
            print(f"🏆 Mejor balance: {tamaño_final / (1024*1024):.2f} MB ({reduccion_final:.1f}% reducción, puntuación: {mejor_puntuacion:.1f})")
        else:
            print("❌ Ningún candidato cumple los criterios de calidad")
        
        return mejor_archivo
    
    def _get_herramientas_disponibles(self) -> List[str]:
        """Obtiene lista de herramientas disponibles en el sistema."""
        herramientas = []
        
        if shutil.which('gs'):
            herramientas.append('Ghostscript')
        if shutil.which('qpdf'):
            herramientas.append('qpdf')
        if shutil.which('pdftk'):
            herramientas.append('PDFtk')
        
        return herramientas
    
    def _mover_archivo_procesado(self, archivo_pdf: Path):
        """Mueve el archivo procesado a una subcarpeta."""
        carpeta_procesados = self.carpeta_input / "procesados"
        carpeta_procesados.mkdir(exist_ok=True)
        
        destino = carpeta_procesados / archivo_pdf.name
        shutil.move(str(archivo_pdf), str(destino))
        print(f"📁 Archivo movido a: {destino}")
    
    def mostrar_resumen(self, resultados: List[Dict]):
        """Muestra un resumen de todos los procesamientos."""
        if not resultados:
            return
        
        print("\n" + "="*60)
        print("📊 RESUMEN DE COMPRESIÓN")
        print("="*60)
        
        total_original = 0
        total_final = 0
        exitosos = 0
        
        for resultado in resultados:
            if 'error' not in resultado:
                exitosos += 1
                total_original += resultado['tamaño_original_mb']
                total_final += resultado['tamaño_final_mb']
                
                print(f"✅ {resultado['archivo_original']}")
                print(f"   {resultado['tamaño_original_mb']:.2f} MB → {resultado['tamaño_final_mb']:.2f} MB ({resultado['reduccion_porcentaje']:.1f}% reducción)")
            else:
                print(f"❌ {resultado['archivo_original']}: {resultado['error']}")
        
        if exitosos > 0:
            reduccion_total = ((total_original - total_final) / total_original) * 100
            print(f"\n🎯 TOTALES:")
            print(f"   Archivos procesados: {exitosos}/{len(resultados)}")
            print(f"   Tamaño total original: {total_original:.2f} MB")
            print(f"   Tamaño total final: {total_final:.2f} MB")
            print(f"   Reducción total: {reduccion_total:.1f}%")
            print(f"   Espacio ahorrado: {total_original - total_final:.2f} MB")

def main():
    parser = argparse.ArgumentParser(description='Compresor PDF Ultra-Optimizado')
    parser.add_argument('--input', '-i', default='input', 
                       help='Carpeta de entrada (default: input)')
    parser.add_argument('--output', '-o', default='output',
                       help='Carpeta de salida (default: output)')
    parser.add_argument('--check-tools', action='store_true',
                       help='Verificar herramientas disponibles')
    
    args = parser.parse_args()
    
    print("🚀 COMPRESOR PDF ULTRA-OPTIMIZADO")
    print("="*50)
    
    compresor = CompresorPDFUltra(args.input, args.output)
    
    if args.check_tools:
        herramientas = compresor._get_herramientas_disponibles()
        print(f"🔧 Herramientas disponibles: {', '.join(herramientas) if herramientas else 'Ninguna'}")
        
        if not herramientas:
            print("\n💡 Para obtener mejor compresión, instala estas herramientas:")
            print("   • Ghostscript: brew install ghostscript (macOS)")
            print("   • qpdf: brew install qpdf (macOS)")
            print("   • PDFtk: brew install pdftk-java (macOS)")
        
        return
    
    try:
        resultados = compresor.procesar_todos_los_pdfs()
        compresor.mostrar_resumen(resultados)
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
