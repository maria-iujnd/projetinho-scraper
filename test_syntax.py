#!/usr/bin/env python3
import sys
try:
    import py_compile
    py_compile.compile('whatsapp_sender.py', doraise=True)
    print("✓ whatsapp_sender.py: syntax OK")
except SyntaxError as e:
    print(f"✗ Syntax error in whatsapp_sender.py: {e}")
    sys.exit(1)

print("All files compiled successfully!")
