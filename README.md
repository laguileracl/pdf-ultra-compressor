# 🚀 Compresor PDF Ultra-Optimizado

Sistema automático de compresión PDF que utiliza las mejores herramientas disponibles para reducir significativamente el tamaño sin perder calidad visual.

## ✨ Características

- 🎯 **Ultra-optimización**: Combina Ghostscript, qpdf y PDFtk para máxima compresión
- 📁 **Sistema de carpetas**: Solo coloca PDFs en `input/` y obtén resultados en `output/`
- ⚡ **Totalmente automático**: Sin configuraciones complejas ni interfaces gráficas
- 🔧 **Múltiples herramientas**: Usa la mejor combinación disponible en tu sistema
- 📊 **Estadísticas detalladas**: Reportes completos de compresión
- 🧹 **Auto-organización**: Mueve archivos procesados automáticamente

## �️ Instalación Rápida

### 1. Instalar herramientas (una sola vez)
```bash
./instalar_herramientas.sh
```

### 2. O instalar manualmente en macOS:
```bash
brew install ghostscript qpdf pdftk-java
```

## � Uso Ultra-Simple

### Método 1: Script automático
```bash
./comprimir.sh
```

### Método 2: Directo
```bash
# 1. Coloca tus PDFs en la carpeta input/
cp mi_documento.pdf input/

# 2. Ejecuta el compresor
python3 comprimir_ultra.py

# 3. Encuentra tus PDFs optimizados en output/
```

### Método 3: Personalizado
```bash
python3 comprimir_ultra.py --input mi_carpeta --output resultados
```

## 📁 Estructura de Carpetas

```
compresorpdf/
├── input/                    # 👈 Coloca aquí tus PDFs
│   ├── documento1.pdf
│   ├── documento2.pdf
│   └── procesados/          # Archivos ya procesados
├── output/                  # 👈 PDFs optimizados aparecen aquí
│   ├── documento1_ultra_optimizado.pdf
│   └── documento2_ultra_optimizado.pdf
└── comprimir_ultra.py       # Script principal
```

## 🔧 Herramientas Utilizadas

1. **Ghostscript**: Compresión profesional con configuración `/ebook`
2. **qpdf**: Optimización estructural y linearización
3. **PDFtk**: Compresión adicional y limpieza
4. **Python**: Orquestación y automatización

## 📊 Resultados Típicos

- **Documentos escaneados**: 60-80% de reducción
- **PDFs con imágenes**: 40-60% de reducción  
- **Documentos de texto**: 20-40% de reducción
- **Calidad visual**: Sin pérdida perceptible

## 🎯 Comandos Útiles

```bash
# Verificar herramientas instaladas
python3 comprimir_ultra.py --check-tools

# Usar carpetas personalizadas
python3 comprimir_ultra.py --input /ruta/pdfs --output /ruta/comprimidos

# Ver ayuda completa
python3 comprimir_ultra.py --help
```

## 💡 Tips

- Los archivos procesados se mueven automáticamente a `input/procesados/`
- Si una herramienta no está disponible, el script continúa con las demás
- Los nombres de salida incluyen "_ultra_optimizado" para evitar confusiones
- El proceso preserva la calidad visual mientras maximiza la compresión
