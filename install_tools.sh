#!/bin/bash

# Install system tools needed for PDF Ultra Compressor (macOS)
set -e

echo "🚀 Installing tools for PDF Ultra Compressor"
echo "========================================="

# Homebrew
if ! command -v brew &> /dev/null; then
  echo "🍺 Homebrew not found. Installing…"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
  eval "$(/opt/homebrew/bin/brew shellenv)"
else
  echo "✅ Homebrew present"
fi

echo "\n🔧 Installing system dependencies…"
brew update
brew install ghostscript qpdf || true

echo "\n✅ Done!"
echo "Tools status:"
if command -v gs &> /dev/null; then
  echo "  ✅ Ghostscript: $(gs --version)"
else
  echo "  ❌ Ghostscript: Not available"
fi
if command -v qpdf &> /dev/null; then
  echo "  ✅ qpdf: $(qpdf --version | head -n1)"
else
  echo "  ❌ qpdf: Not available"
fi
