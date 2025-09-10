#!/usr/bin/env python3
"""
Script to integrate telemetry into compressor.py safely
"""

import re

# Read the original file
with open('compressor.py', 'r') as f:
    content = f.read()

print("Original file length:", len(content))

# 1. Add telemetry import after quality_gates import
quality_import_pattern = r'(# Try to import advanced quality gates\ntry:\n    from quality_gates import QualityGateChecker, QualityGateConfig\n    HAS_ADVANCED_GATES = True\nexcept ImportError:\n    HAS_ADVANCED_GATES = False)'

telemetry_import = '''# Try to import advanced quality gates
try:
    from quality_gates import QualityGateChecker, QualityGateConfig
    HAS_ADVANCED_GATES = True
except ImportError:
    HAS_ADVANCED_GATES = False

# Try to import anonymous telemetry
try:
    from anonymous_telemetry import AnonymousTelemetry
    HAS_TELEMETRY = True
except ImportError:
    HAS_TELEMETRY = False'''

content = re.sub(quality_import_pattern, telemetry_import, content)

# 2. Update constructor signature
constructor_pattern = r'def __init__\(self, input_dir: str = "input", output_dir: str = "output", enable_advanced_gates: bool = False\):'
new_constructor = 'def __init__(self, input_dir: str = "input", output_dir: str = "output", \n                 enable_advanced_gates: bool = False, enable_telemetry: bool = True):'
content = re.sub(constructor_pattern, new_constructor, content)

# 3. Add telemetry config line
config_pattern = r'(self\.enable_advanced_gates = enable_advanced_gates and HAS_ADVANCED_GATES)'
new_config = '''self.enable_advanced_gates = enable_advanced_gates and HAS_ADVANCED_GATES
        self.enable_telemetry = enable_telemetry and HAS_TELEMETRY'''
content = re.sub(config_pattern, new_config, content)

# 4. Add telemetry initialization
quality_init_pattern = r'(        # Initialize advanced quality gates if enabled\n        self\.quality_checker = None\n        if self\.enable_advanced_gates:\n            try:\n                self\.quality_checker = QualityGateChecker\(\)\n                print\("🔬 Advanced quality gates enabled \(PSNR \+ SSIM \+ LPIPS\)"\)\n            except Exception as e:\n                print\(f"⚠️  Advanced quality gates failed to initialize: \{e\}"\)\n                self\.enable_advanced_gates = False)'

telemetry_init = '''        # Initialize advanced quality gates if enabled
        self.quality_checker = None
        if self.enable_advanced_gates:
            try:
                self.quality_checker = QualityGateChecker()
                print("🔬 Advanced quality gates enabled (PSNR + SSIM + LPIPS)")
            except Exception as e:
                print(f"⚠️  Advanced quality gates failed to initialize: {e}")
                self.enable_advanced_gates = False

        # Initialize anonymous telemetry if enabled
        self.telemetry = None
        if self.enable_telemetry:
            try:
                self.telemetry = AnonymousTelemetry()
                print("📊 Anonymous telemetry enabled for algorithm improvement")
            except Exception as e:
                print(f"⚠️  Telemetry failed to initialize: {e}")
                self.enable_telemetry = False'''

content = re.sub(quality_init_pattern, telemetry_init, content)

# 5. Add telemetry to compress_pdf method start
compress_start_pattern = r'(    def compress_pdf\(self, pdf_path: Path\) -> Dict:\n        original_mb = pdf_path\.stat\(\)\.st_size / \(1024 \* 1024\)\n        output_name = self\.output_dir / f"\{pdf_path\.stem\}_optimized\.pdf"\n\n        print\(f"📊 Original size: \{original_mb:\.2f\} MB"\))'

new_compress_start = '''    def compress_pdf(self, pdf_path: Path) -> Dict:
        # Generate anonymous document ID for telemetry (if enabled)
        doc_id = None
        if self.telemetry:
            try:
                doc_id = self.telemetry.analyze_document(pdf_path)
            except Exception as e:
                print(f"⚠️ Telemetry analysis failed: {e}")

        original_mb = pdf_path.stat().st_size / (1024 * 1024)
        output_name = self.output_dir / f"{pdf_path.stem}_optimized.pdf"

        print(f"📊 Original size: {original_mb:.2f} MB")'''

content = re.sub(compress_start_pattern, new_compress_start, content)

# 6. Add telemetry before return result
return_pattern = r'(            # cleanup temps\n            for method, temp in candidates:\n                try:\n                    if temp\.exists\(\):\n                        temp\.unlink\(\)\n                except Exception:\n                    pass\n\n            return result)'

new_return = '''            # cleanup temps
            for method, temp in candidates:
                try:
                    if temp.exists():
                        temp.unlink()
                except Exception:
                    pass

            # Record compression result for telemetry (if enabled)
            if self.telemetry and doc_id:
                try:
                    self.telemetry.record_compression_result(doc_id, result)
                except Exception as e:
                    print(f"⚠️ Telemetry recording failed: {e}")

            return result'''

content = re.sub(return_pattern, new_return, content)

# 7. Add telemetry to error case
error_pattern = r'(        except Exception as e:\n            print\(f"❌ Error: \{e\}"\)\n            return \{"original_file": pdf_path\.name, "error": str\(e\)\})'

new_error = '''        except Exception as e:
            print(f"❌ Error: {e}")
            error_result = {"original_file": pdf_path.name, "error": str(e)}
            
            # Record error for telemetry (if enabled)
            if self.telemetry and doc_id:
                try:
                    self.telemetry.record_compression_result(doc_id, error_result)
                except Exception as telemetry_error:
                    print(f"⚠️ Telemetry recording failed: {telemetry_error}")
            
            return error_result'''

content = re.sub(error_pattern, new_error, content)

# 8. Add CLI argument
cli_pattern = r'(    parser\.add_argument\("--advanced-gates", action="store_true",\n                       help="Enable advanced quality gates \(SSIM \+ LPIPS\)"\))'

new_cli = '''    parser.add_argument("--advanced-gates", action="store_true",
                       help="Enable advanced quality gates (SSIM + LPIPS)")
    parser.add_argument("--disable-telemetry", action="store_true",
                       help="Disable anonymous telemetry for algorithm improvement")'''

content = re.sub(cli_pattern, new_cli, content)

# 9. Update constructor call
constructor_call_pattern = r'(        c = PDFCompressor\(\n            input_dir=args\.input,\n            output_dir=args\.output, \n            enable_advanced_gates=args\.advanced_gates\n        \))'

new_constructor_call = '''        c = PDFCompressor(
            input_dir=args.input,
            output_dir=args.output, 
            enable_advanced_gates=args.advanced_gates,
            enable_telemetry=not args.disable_telemetry
        )'''

content = re.sub(constructor_call_pattern, new_constructor_call, content)

print("Modified file length:", len(content))

# Write the modified file
with open('compressor.py', 'w') as f:
    f.write(content)

print("✅ Integration complete")
