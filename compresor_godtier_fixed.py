#!/usr/bin/env python3
"""
🚀 COMPRESOR PDF GOD-TIER FIXED 2025 🚀
Versión corregida que maneja aliases y rutas de Ghostscript
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class CompresorPDFGodTierFixed:
    """Compresor PDF GOD-TIER con detección automática de herramientas."""
    
    def __init__(self, carpeta_input: str = "input", carpeta_output: str = "output"):
        self.carpeta_input = Path(carpeta_input)
        self.carpeta_output = Path(carpeta_output)
        
        # Crear carpetas
        self.carpeta_input.mkdir(exist_ok=True)
        self.carpeta_output.mkdir(exist_ok=True)
        
        # Detectar herramientas reales
        self.tools = self._detectar_herramientas()
        
        print(f"🚀 COMPRESOR PDF GOD-TIER FIXED")
        print(f"📁 Input: {self.carpeta_input.absolute()}")
        print(f"📁 Output: {self.carpeta_output.absolute()}")
        self._mostrar_herramientas()
    
    def _detectar_herramientas(self) -> Dict[str, Optional[str]]:
        """Detecta las rutas reales de las herramientas."""
        tools = {}
        
        # Buscar Ghostscript en ubicaciones comunes
        gs_paths = [
            '/opt/homebrew/bin/gs',
            '/usr/local/bin/gs', 
            '/opt/homebrew/Cellar/ghostscript/*/bin/gs',
            'ghostscript'
        ]
        
        tools['gs'] = None
        for path in gs_paths:
            if '*' in path:
                # Buscar con glob
                import glob
                matches = glob.glob(path)
                if matches:
                    tools['gs'] = matches[0]
                    break
            elif Path(path).exists():
                tools['gs'] = path
                break
            elif shutil.which(path):
                tools['gs'] = shutil.which(path)
                break
        
        # Otras herramientas
        tools['qpdf'] = shutil.which('qpdf')
        tools['pdftk'] = shutil.which('pdftk')
        
        return tools
    
    def _mostrar_herramientas(self):
        """Muestra herramientas detectadas."""
        print("\n🔧 HERRAMIENTAS DETECTADAS:")
        
        if self.tools['gs']:
            try:
                result = subprocess.run([self.tools['gs'], '--version'], 
                                      capture_output=True, text=True)
                version = result.stdout.strip().split('\n')[0] if result.returncode == 0 else "desconocida"
                print(f"  ✅ Ghostscript: {self.tools['gs']} (v{version})")
            except:
                print(f"  ⚠️  Ghostscript: {self.tools['gs']} (no se pudo verificar)")
        else:
            print(f"  ❌ Ghostscript: No encontrado")
        
        if self.tools['qpdf']:
            print(f"  ✅ qpdf: {self.tools['qpdf']}")
        else:
            print(f"  ❌ qpdf: No encontrado")
        
        if self.tools['pdftk']:
            print(f"  ✅ PDFtk: {self.tools['pdftk']}")
        else:
            print(f"  ❌ PDFtk: No encontrado")
        
        print()
    
    def procesar_todos_los_pdfs(self) -> List[Dict]:
        """Procesa todos los PDFs."""
        pdfs = list(self.carpeta_input.glob("*.pdf"))
        
        if not pdfs:
            print("⚠️  No se encontraron archivos PDF")
            return []
        
        print(f"🔍 Encontrados {len(pdfs)} archivo(s) PDF")
        
        resultados = []
        for pdf in pdfs:
            print(f"\n🚀 PROCESANDO: {pdf.name}")
            print("=" * 60)
            
            resultado = self.comprimir_pdf_godtier(pdf)
            resultados.append(resultado)
            
            # Mover archivo procesado
            self._mover_archivo_procesado(pdf)
        
        return resultados
    
    def comprimir_pdf_godtier(self, archivo_pdf: Path) -> Dict:
        """Compresión PDF con múltiples estrategias GOD-TIER."""
        
        tamaño_original = archivo_pdf.stat().st_size / (1024 * 1024)
        nombre_salida = self.carpeta_output / f"{archivo_pdf.stem}_godtier_optimized.pdf"
        
        print(f"📊 Tamaño original: {tamaño_original:.2f} MB")
        
        candidatos = []
        
        try:
            # Estrategia 1: Ultra conservador (solo qpdf)
            if self.tools['qpdf']:
                candidato1 = self._compresion_conservadora(archivo_pdf)
                if candidato1:
                    candidatos.append(('conservador', candidato1))
            
            # Estrategia 2: Ghostscript calidad alta
            if self.tools['gs']:
                candidato2 = self._compresion_calidad_alta(archivo_pdf)
                if candidato2:
                    candidatos.append(('calidad_alta', candidato2))
            
            # Estrategia 3: Ghostscript equilibrado
            if self.tools['gs']:
                candidato3 = self._compresion_equilibrada(archivo_pdf)
                if candidato3:
                    candidatos.append(('equilibrado', candidato3))
            
            # Estrategia 4: Ghostscript agresivo pero seguro
            if self.tools['gs']:
                candidato4 = self._compresion_agresiva_segura(archivo_pdf)
                if candidato4:
                    candidatos.append(('agresivo_seguro', candidato4))
            
            # Seleccionar el mejor resultado
            mejor = self._seleccionar_mejor_resultado(archivo_pdf, candidatos)
            
            if mejor:
                shutil.copy2(mejor['archivo'], nombre_salida)
                tamaño_final = nombre_salida.stat().st_size / (1024 * 1024)
                reduccion = ((tamaño_original - tamaño_final) / tamaño_original) * 100
                
                resultado = {
                    'archivo_original': archivo_pdf.name,
                    'archivo_final': nombre_salida.name,
                    'tamaño_original_mb': tamaño_original,
                    'tamaño_final_mb': tamaño_final,
                    'reduccion_porcentaje': reduccion,
                    'metodo_ganador': mejor['metodo'],
                    'puntuacion_calidad': mejor['puntuacion']
                }
                
                print(f"\n🎉 COMPRESIÓN EXITOSA!")
                print(f"📊 {tamaño_original:.2f} MB → {tamaño_final:.2f} MB ({reduccion:.1f}%)")
                print(f"🏆 Método ganador: {mejor['metodo']}")
                print(f"⭐ Puntuación: {mejor['puntuacion']:.1f}/100")
                
            else:
                # Fallback: copiar original
                shutil.copy2(archivo_pdf, nombre_salida)
                resultado = {
                    'archivo_original': archivo_pdf.name,
                    'archivo_final': nombre_salida.name,
                    'tamaño_original_mb': tamaño_original,
                    'tamaño_final_mb': tamaño_original,
                    'reduccion_porcentaje': 0,
                    'metodo_ganador': 'sin_cambios',
                    'puntuacion_calidad': 100.0
                }
                print(f"\n🛡️  Sin cambios (preservando original)")
            
            # Limpiar temporales
            for metodo, archivo_temp in candidatos:
                if archivo_temp.exists():
                    archivo_temp.unlink()
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'archivo_original': archivo_pdf.name, 'error': str(e)}
    
    def _compresion_conservadora(self, archivo_pdf: Path) -> Optional[Path]:
        """Compresión ultra-conservadora con qpdf."""
        print("🛡️  Compresión conservadora (qpdf)...")
        
        temp_file = Path(tempfile.mktemp(suffix='_conservador.pdf'))
        
        cmd = [
            self.tools['qpdf'],
            '--optimize-images',
            '--compress-streams=y',
            '--object-streams=generate',
            str(archivo_pdf),
            str(temp_file)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0 and temp_file.exists():
                tamaño_mb = temp_file.stat().st_size / (1024*1024)
                print(f"  ✅ Conservador: {tamaño_mb:.2f} MB")
                return temp_file
            else:
                print(f"  ⚠️  qpdf warning: {result.stderr}")
                if temp_file.exists() and temp_file.stat().st_size > 0:
                    tamaño_mb = temp_file.stat().st_size / (1024*1024)
                    print(f"  ✅ Conservador (con warnings): {tamaño_mb:.2f} MB")
                    return temp_file
        except Exception as e:
            print(f"  ❌ Error conservador: {e}")
        
        return None
    
    def _compresion_calidad_alta(self, archivo_pdf: Path) -> Optional[Path]:
        """Compresión de calidad alta con Ghostscript."""
        print("💎 Compresión calidad alta...")
        
        temp_file = Path(tempfile.mktemp(suffix='_calidad_alta.pdf'))
        
        cmd = [
            self.tools['gs'],
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.7',
            '-dPDFSETTINGS=/prepress',
            '-dNOPAUSE', '-dQUIET', '-dBATCH',
            '-dColorImageResolution=300',
            '-dGrayImageResolution=300',
            '-dMonoImageResolution=1200',
            '-dColorImageDownsampleThreshold=2.0',
            '-dGrayImageDownsampleThreshold=2.0',
            '-dMonoImageDownsampleThreshold=2.0',
            '-dOptimize=true',
            '-dEmbedAllFonts=true',
            '-dSubsetFonts=true',
            '-dCompressFonts=false',
            '-dPreserveAnnots=true',
            f'-sOutputFile={temp_file}',
            str(archivo_pdf)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0 and temp_file.exists():
                tamaño_mb = temp_file.stat().st_size / (1024*1024)
                print(f"  ✅ Calidad alta: {tamaño_mb:.2f} MB")
                return temp_file
        except Exception as e:
            print(f"  ❌ Error calidad alta: {e}")
        
        return None
    
    def _compresion_equilibrada(self, archivo_pdf: Path) -> Optional[Path]:
        """Compresión equilibrada."""
        print("⚖️  Compresión equilibrada...")
        
        temp_file = Path(tempfile.mktemp(suffix='_equilibrado.pdf'))
        
        cmd = [
            self.tools['gs'],
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.6',
            '-dPDFSETTINGS=/printer',
            '-dNOPAUSE', '-dQUIET', '-dBATCH',
            '-dColorImageResolution=200',
            '-dGrayImageResolution=200',
            '-dMonoImageResolution=600',
            '-dColorImageDownsampleThreshold=1.5',
            '-dOptimize=true',
            '-dEmbedAllFonts=true',
            '-dSubsetFonts=true',
            f'-sOutputFile={temp_file}',
            str(archivo_pdf)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0 and temp_file.exists():
                tamaño_mb = temp_file.stat().st_size / (1024*1024)
                print(f"  ✅ Equilibrado: {tamaño_mb:.2f} MB")
                return temp_file
        except Exception as e:
            print(f"  ❌ Error equilibrado: {e}")
        
        return None
    
    def _compresion_agresiva_segura(self, archivo_pdf: Path) -> Optional[Path]:
        """Compresión agresiva pero segura."""
        print("🎯 Compresión agresiva segura...")
        
        temp_file = Path(tempfile.mktemp(suffix='_agresivo.pdf'))
        
        cmd = [
            self.tools['gs'],
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.5',
            '-dPDFSETTINGS=/ebook',
            '-dNOPAUSE', '-dQUIET', '-dBATCH',
            '-dColorImageResolution=150',
            '-dGrayImageResolution=150',
            '-dMonoImageResolution=600',
            '-dColorImageDownsampleThreshold=1.2',
            '-dOptimize=true',
            '-dEmbedAllFonts=true',
            '-dSubsetFonts=true',
            '-dDetectDuplicateImages=true',
            f'-sOutputFile={temp_file}',
            str(archivo_pdf)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0 and temp_file.exists():
                tamaño_mb = temp_file.stat().st_size / (1024*1024)
                print(f"  ✅ Agresivo seguro: {tamaño_mb:.2f} MB")
                return temp_file
        except Exception as e:
            print(f"  ❌ Error agresivo: {e}")
        
        return None
    
    def _seleccionar_mejor_resultado(self, original: Path, candidatos: List) -> Optional[Dict]:
        """Selecciona el mejor resultado basado en puntuación inteligente."""
        if not candidatos:
            return None
        
        tamaño_original = original.stat().st_size
        mejor_resultado = None
        mejor_puntuacion = -1
        
        print("\n🔍 Evaluando resultados:")
        
        for metodo, archivo in candidatos:
            if not archivo.exists():
                continue
            
            tamaño = archivo.stat().st_size
            reduccion = ((tamaño_original - tamaño) / tamaño_original) * 100
            
            # Sistema de puntuación inteligente
            if reduccion < 5:
                puntuacion = 70 + reduccion  # Poca reducción = puntuación baja
            elif 5 <= reduccion <= 50:
                puntuacion = 80 + (reduccion - 5) / 45 * 20  # Zona óptima
            elif 50 < reduccion <= 80:
                puntuacion = 95 - (reduccion - 50) / 30 * 15  # Empezar a penalizar
            else:
                puntuacion = 60 - (reduccion - 80)  # Muy agresivo = malo
            
            # Bonificaciones por método
            if metodo == 'conservador':
                puntuacion += 10  # Bonus por preservar calidad
            elif metodo == 'calidad_alta':
                puntuacion += 8
            elif metodo == 'equilibrado':
                puntuacion += 5
            
            # Asegurar que no empeore
            if reduccion < 0:
                puntuacion = 0
            
            print(f"  📄 {metodo}: {tamaño/(1024*1024):.2f} MB ({reduccion:+.1f}%) - Puntuación: {puntuacion:.1f}")
            
            if puntuacion > mejor_puntuacion:
                mejor_puntuacion = puntuacion
                mejor_resultado = {
                    'metodo': metodo,
                    'archivo': archivo,
                    'puntuacion': puntuacion,
                    'reduccion': reduccion
                }
        
        return mejor_resultado
    
    def _mover_archivo_procesado(self, archivo_pdf: Path):
        """Mueve archivo procesado."""
        carpeta_procesados = self.carpeta_input / "procesados"
        carpeta_procesados.mkdir(exist_ok=True)
        
        destino = carpeta_procesados / archivo_pdf.name
        shutil.move(str(archivo_pdf), str(destino))
        print(f"📁 Movido a: {destino}")
    
    def mostrar_resumen(self, resultados: List[Dict]):
        """Muestra resumen final."""
        if not resultados:
            return
        
        print("\n" + "="*70)
        print("🚀 RESUMEN FINAL GOD-TIER")
        print("="*70)
        
        total_original = 0
        total_final = 0
        exitosos = 0
        
        for resultado in resultados:
            if 'error' not in resultado:
                exitosos += 1
                total_original += resultado['tamaño_original_mb']
                total_final += resultado['tamaño_final_mb']
                
                print(f"✅ {resultado['archivo_original']}")
                print(f"   📊 {resultado['tamaño_original_mb']:.2f} MB → {resultado['tamaño_final_mb']:.2f} MB ({resultado['reduccion_porcentaje']:.1f}%)")
                print(f"   🏆 {resultado['metodo_ganador']} (calidad: {resultado.get('puntuacion_calidad', 0):.1f}/100)")
            else:
                print(f"❌ {resultado['archivo_original']}: {resultado['error']}")
        
        if exitosos > 0:
            reduccion_total = ((total_original - total_final) / total_original) * 100
            print(f"\n🎯 TOTALES:")
            print(f"   📁 Procesados: {exitosos}/{len(resultados)}")
            print(f"   📊 {total_original:.2f} MB → {total_final:.2f} MB ({reduccion_total:.1f}%)")
            print(f"   💾 Ahorrado: {total_original - total_final:.2f} MB")

def main():
    """Función principal."""
    try:
        compresor = CompresorPDFGodTierFixed()
        resultados = compresor.procesar_todos_los_pdfs()
        compresor.mostrar_resumen(resultados)
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrumpido por usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
