# -----------------------------------------------
# Shuraksha - Environment Setup Test
# -----------------------------------------------
# This file checks that all required libraries
# are installed and working correctly.
# Run this file once to confirm your setup.
# You can safely delete it after confirmation.
# -----------------------------------------------

# Test 1: Check PyQt6 (our graphical interface library)
try:
    from PyQt6.QtWidgets import QApplication
    print("PyQt6 is installed correctly.")
except ImportError:
    print("PyQt6 FAILED. Run: pip install PyQt6")

# Test 2: Check cryptography (our encryption library)
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    print("cryptography is installed correctly.")
except ImportError:
    print("cryptography FAILED. Run: pip install cryptography")

# Test 3: Check pycryptodome (additional cryptographic tools)
try:
    from Crypto.Hash import SHA256
    print("pycryptodome is installed correctly.")
except ImportError:
    print("pycryptodome FAILED. Run: pip install pycryptodome")

# Test 4: Check pywin32 (Windows API access)
try:
    import win32api
    print("pywin32 is installed correctly.")
except ImportError:
    print("pywin32 FAILED. Run: pip install pywin32")

# Test 5: Check Pillow (image processing)
try:
    from PIL import Image
    print("Pillow is installed correctly.")
except ImportError:
    print("Pillow FAILED. Run: pip install pillow")

# -----------------------------------------------
print("\nSetup check complete.")
# -----------------------------------------------
