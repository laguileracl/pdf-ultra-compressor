#!/bin/bash

# Script de uso rápido para el Compresor PDF Ultra-Optimizado

echo "🚀 COMPRESOR PDF ULTRA-OPTIMIZADO"
echo "=================================="
echo ""

# Verificar si el script principal existe
if [ ! -f "comprimir_ultra.py" ]; then
    echo "❌ Error: comprimir_ultra.py no encontrado"
    echo "   Asegúrate de estar en el directorio correcto"
    exit 1
fi

# Mostrar estado de las carpetas
echo "📁 Estado de carpetas:"
if [ -d "input" ]; then
    pdf_count=$(find input -name "*.pdf" -type f | wc -l)
    echo "  ✅ input/ - $pdf_count archivo(s) PDF encontrado(s)"
    
    if [ $pdf_count -gt 0 ]; then
        echo "     Archivos:"
        find input -name "*.pdf" -type f -exec basename {} \; | sed 's/^/       • /'
    fi
else
    echo "  ⚠️  input/ - No existe (se creará automáticamente)"
fi

if [ -d "output" ]; then
    echo "  ✅ output/ - Listo para archivos comprimidos"
else
    echo "  ⚠️  output/ - No existe (se creará automáticamente)"
fi

echo ""

# Verificar herramientas
echo "🔧 Verificando herramientas disponibles..."
python3 comprimir_ultra.py --check-tools

echo ""

# Preguntar qué hacer
echo "¿Qué quieres hacer?"
echo "1) Comprimir todos los PDFs en input/"
echo "2) Verificar herramientas solamente"
echo "3) Instalar herramientas necesarias"
echo "4) Salir"
echo ""
read -p "Elige una opción (1-4): " opcion

case $opcion in
    1)
        echo ""
        echo "🚀 Iniciando compresión..."
        python3 comprimir_ultra.py
        ;;
    2)
        echo ""
        echo "🔧 Verificando herramientas..."
        python3 comprimir_ultra.py --check-tools
        ;;
    3)
        echo ""
        echo "📦 Instalando herramientas..."
        if [ -f "instalar_herramientas.sh" ]; then
            ./instalar_herramientas.sh
        else
            echo "❌ Script de instalación no encontrado"
        fi
        ;;
    4)
        echo "👋 ¡Hasta luego!"
        exit 0
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac
