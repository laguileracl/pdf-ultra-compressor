#!/bin/bash

# Script de instalación para Compresor PDF Ultra-Optimizado
# Instala todas las herramientas necesarias en macOS

echo "🚀 Instalando herramientas para Compresor PDF Ultra-Optimizado"
echo "=============================================================="

# Verificar si Homebrew está instalado
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew no está instalado. Instalando..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Agregar Homebrew al PATH
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "✅ Homebrew ya está instalado"
fi

echo ""
echo "📦 Instalando herramientas de compresión PDF..."

# Instalar Ghostscript
echo "🔧 Instalando Ghostscript..."
if brew install ghostscript; then
    echo "✅ Ghostscript instalado correctamente"
else
    echo "⚠️  Error instalando Ghostscript"
fi

# Instalar qpdf
echo "🔧 Instalando qpdf..."
if brew install qpdf; then
    echo "✅ qpdf instalado correctamente"
else
    echo "⚠️  Error instalando qpdf"
fi

# Instalar PDFtk
echo "🔧 Instalando PDFtk..."
if brew install pdftk-java; then
    echo "✅ PDFtk instalado correctamente"
else
    echo "⚠️  Error instalando PDFtk"
fi

echo ""
echo "🐍 Configurando entorno Python..."

# Verificar si Python 3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "🔧 Instalando Python 3..."
    brew install python
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "🔧 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias Python (versión básica)
echo "🔧 Instalando dependencias Python básicas..."
pip install --upgrade pip

echo ""
echo "✅ Instalación completada!"
echo ""
echo "📋 Herramientas instaladas:"

# Verificar instalaciones
if command -v gs &> /dev/null; then
    echo "  ✅ Ghostscript: $(gs --version)"
else
    echo "  ❌ Ghostscript: No disponible"
fi

if command -v qpdf &> /dev/null; then
    echo "  ✅ qpdf: $(qpdf --version)"
else
    echo "  ❌ qpdf: No disponible"
fi

if command -v pdftk &> /dev/null; then
    echo "  ✅ PDFtk: Disponible"
else
    echo "  ❌ PDFtk: No disponible"
fi

echo ""
echo "🎯 Uso del compresor:"
echo "  1. Coloca tus PDFs en la carpeta 'input/'"
echo "  2. Ejecuta: python comprimir_ultra.py"
echo "  3. Los PDFs optimizados aparecerán en 'output/'"
echo ""
echo "🔍 Para verificar herramientas: python comprimir_ultra.py --check-tools"
