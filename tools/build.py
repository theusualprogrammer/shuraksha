# -----------------------------------------------
# Shuraksha - PyInstaller Build Script
# File: tools/build.py
# -----------------------------------------------
# This script packages the entire Shuraksha project
# into a standalone Windows .exe file.
#
# The output is a single folder in dist\Shuraksha
# containing the .exe and all required files.
# The Inno Setup installer then packages that folder
# into a professional Windows installer.
#
# Run this script from the project root:
#   python tools\build.py
# -----------------------------------------------

import subprocess
import sys
import shutil
from pathlib import Path

# -----------------------------------------------
# PATHS
# -----------------------------------------------
ROOT       = Path(__file__).parent.parent
MAIN_PY    = ROOT / 'src' / 'main.py'
ICON_ICO   = ROOT / 'assets' / 'icons' / 'icon.ico'
DIST_DIR   = ROOT / 'dist'
BUILD_DIR  = ROOT / 'build'
SPEC_FILE  = ROOT / 'shuraksha.spec'


def clean():
    """Remove previous build output."""
    print("Cleaning previous build output...")
    for path in [DIST_DIR, BUILD_DIR, SPEC_FILE]:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    print("  Done.")


def build():
    """
    Run PyInstaller to create the standalone executable.

    Key flags explained:
    --onedir        : output is a folder, not a single file.
                      Faster startup than --onefile.
    --windowed      : no terminal window appears when app runs.
    --name          : name of the output exe and folder.
    --icon          : the .ico file applied to the exe.
    --add-data      : copy the assets folder into the bundle.
    --hidden-import : force-include modules PyInstaller
                      might miss during analysis.
    --clean         : clear the PyInstaller cache before build.
    --noconfirm     : overwrite existing output without asking.
    """
    print("Building Shuraksha executable...")
    print("This takes 1 to 3 minutes. Please wait.")
    print("")

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        str(MAIN_PY),
        '--onedir',
        '--windowed',
        '--name',           'Shuraksha',
        '--icon',           str(ICON_ICO),
        '--add-data',       f'{ROOT / "assets"};assets',
        '--hidden-import',  'PyQt6',
        '--hidden-import',  'PyQt6.QtWidgets',
        '--hidden-import',  'PyQt6.QtCore',
        '--hidden-import',  'PyQt6.QtGui',
        '--hidden-import',  'cryptography',
        '--hidden-import',  'cryptography.hazmat.primitives.ciphers.aead',
        '--hidden-import',  'cryptography.hazmat.primitives.kdf.pbkdf2',
        '--hidden-import',  'cryptography.hazmat.primitives.hashes',
        '--hidden-import',  'Crypto.Hash.SHA256',
        '--clean',
        '--noconfirm',
        '--distpath',       str(DIST_DIR),
        '--workpath',       str(BUILD_DIR),
        '--specpath',       str(ROOT),
    ]

    result = subprocess.run(cmd, cwd=str(ROOT))

    if result.returncode == 0:
        print("")
        print("Build successful.")
        print(f"Output: {DIST_DIR / 'Shuraksha'}")
    else:
        print("")
        print("Build FAILED. Check the output above for errors.")
        sys.exit(1)


def verify():
    """Check that the expected output files exist."""
    print("")
    print("Verifying build output...")

    exe = DIST_DIR / 'Shuraksha' / 'Shuraksha.exe'
    if exe.exists():
        size_mb = exe.stat().st_size / (1024 * 1024)
        print(f"  Shuraksha.exe found  ({size_mb:.1f} MB)")
    else:
        print("  ERROR: Shuraksha.exe not found.")
        sys.exit(1)

    print("  Verification complete.")


if __name__ == '__main__':
    clean()
    build()
    verify()
    print("")
    print("Ready for Inno Setup packaging.")
