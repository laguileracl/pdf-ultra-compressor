# 📋 INSTRUCCIONES DE USO

## 🎯 Cómo usar tu Compresor PDF Ultra-Optimizado

### PASO 1: Preparación (solo la primera vez)
```bash
# Navegar a tu carpeta del proyecto
cd /Users/laa/Projects/compresorpdf

# Instalar herramientas necesarias
./instalar_herramientas.sh
```

### PASO 2: Comprimir PDFs (uso diario)

#### Opción A - Método más fácil:
```bash
# 1. Coloca tus PDFs en la carpeta input/
cp ~/Descargas/mi_documento.pdf input/

# 2. Ejecuta el script interactivo
./comprimir.sh

# 3. Sigue las instrucciones en pantalla
```

#### Opción B - Método directo:
```bash
# 1. Coloca PDFs en input/
# 2. Ejecuta directamente:
python3 comprimir_ultra.py

# Los resultados aparecerán en output/
```

### 📁 Estructura que verás:

```
input/
├── tu_documento.pdf           # 👈 Colocas aquí
└── procesados/                # 👈 Se mueven aquí después

output/
└── tu_documento_ultra_optimizado.pdf  # 👈 Resultado final
```

### 🔍 Verificar que todo funciona:
```bash
python3 comprimir_ultra.py --check-tools
```

### 💡 Ejemplo completo:

```bash
# 1. Ir al directorio
cd /Users/laa/Projects/compresorpdf

# 2. Copiar un PDF de prueba
cp ~/Descargas/documento_grande.pdf input/

# 3. Comprimir
python3 comprimir_ultra.py

# 4. Ver resultado
ls -la output/
```

### 📊 Lo que verás:

```
🚀 COMPRESOR PDF ULTRA-OPTIMIZADO
==================================================
📁 Carpeta de entrada: /Users/laa/Projects/compresorpdf/input
📁 Carpeta de salida: /Users/laa/Projects/compresorpdf/output
🔍 Encontrados 1 archivo(s) PDF para procesar

🚀 Procesando: documento_grande.pdf
==================================================
📊 Tamaño original: 15.30 MB
🔧 Aplicando compresión con Ghostscript...
✅ Ghostscript: 8.45 MB
🔧 Optimizando con qpdf...
✅ qpdf: 7.82 MB
🔧 Comprimiendo con PDFtk...
✅ PDFtk: 7.65 MB
✅ Compresión completada!
📊 Tamaño final: 7.65 MB
📊 Reducción: 50.0%
💾 Guardado como: documento_grande_ultra_optimizado.pdf
📁 Archivo movido a: input/procesados/documento_grande.pdf

============================================================
📊 RESUMEN DE COMPRESIÓN
============================================================
✅ documento_grande.pdf
   15.30 MB → 7.65 MB (50.0% reducción)

🎯 TOTALES:
   Archivos procesados: 1/1
   Tamaño total original: 15.30 MB
   Tamaño total final: 7.65 MB
   Reducción total: 50.0%
   Espacio ahorrado: 7.65 MB
```

## 🚨 Workflow típico:

1. **Me avisas**: "Hey, tengo PDFs para comprimir"
2. **Tú colocas**: Los PDFs en la carpeta `input/`
3. **Me avisas**: "Ya están listos"
4. **Yo ejecuto**: `python3 comprimir_ultra.py`
5. **Tú obtienes**: PDFs ultra-comprimidos en `output/`

¡Así de simple! 🎉
