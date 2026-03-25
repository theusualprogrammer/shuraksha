# Shuraksha Security Vault

A personal encrypted security vault for Windows.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Encryption](https://img.shields.io/badge/encryption-AES--256--GCM-green)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What is Shuraksha

Shuraksha (Sanskrit for Protection) is a personal encrypted security vault for Windows. It protects your files, photos, videos, passwords, and private notes using military-grade AES-256-GCM encryption.

Everything stays only on your computer. Nothing is ever sent to any cloud, server, or external service.

---

## Key Features

- AES-256-GCM military grade encryption
- Two-layer deception system with a fully working decoy dashboard
- Encrypted file storage with secure 3-pass deletion
- Credential manager with clipboard auto-clear
- Encrypted secure notes
- Access log viewer
- Panic lock button (Ctrl+Shift+X)
- Auto-lock after inactivity
- Password hints system
- Fake BODMAS challenge screen as the vault entry point
- Fake crash screen on too many wrong attempts
- No cloud sync, no internet, no telemetry
- Professional Windows installer

---

## How the Two-Layer System Works

Shuraksha opens in light mode showing a realistic decoy file manager. It shows real system files and behaves like a normal application. Anyone watching your screen sees nothing suspicious.

To reach the real vault:

1. Slide the theme toggle at the top right to dark mode
2. A BODMAS arithmetic question appears on screen
3. Do not solve the maths question
4. Type your date of birth in DD/MM/YYYY format
5. The real vault opens immediately

---

## Installation

Download the latest installer from the releases page:
```
Shuraksha_Setup_v1.0.0.exe
```

Run the installer and follow the wizard. Registration happens automatically after installation.

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| Interface | PyQt6 |
| Encryption | AES-256-GCM via cryptography library |
| Key Derivation | PBKDF2-SHA256 480,000 rounds |
| Packaging | PyInstaller |
| Installer | Inno Setup 6 |

---

## Project Structure
```
shuraksha/
├── src/
│   ├── core/crypto.py              AES-256-GCM encryption engine
│   ├── installer/registration.py  Registration wizard
│   ├── ui/login.py                 Login screen
│   ├── ui/fake_dashboard.py        Decoy file manager
│   ├── ui/bodmas.py                BODMAS challenge screen
│   ├── ui/vault_dashboard.py       Real vault dashboard
│   └── main.py                     Application controller
├── tools/
│   ├── make_icon.py                Icon generator
│   └── build.py                    PyInstaller build script
├── assets/icons/                   Application icons
├── docs/GUIDE.md                   Full user guide
├── installer.iss                   Inno Setup script
└── requirements.txt                Python dependencies
```

---

## Building from Source
```bash
git clone https://github.com/theusualprogrammer/shuraksha
cd shuraksha
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

---

## Building the Installer
```bash
python tools\make_icon.py
python tools\build.py
```

Then open `installer.iss` in Inno Setup and press F9.

---

## Security

- Passwords are never stored in plain text
- PBKDF2 with 480,000 SHA-256 rounds for key derivation
- AES-256-GCM authenticated encryption
- 3-pass secure file deletion
- Clipboard auto-clear after 30 seconds
- Memory cleared on vault lock

---

## Disclaimer

> Shuraksha is a final year cybersecurity project. It is designed for personal use on a trusted machine. It provides strong protection against casual access and shoulder surfing. It is not designed to withstand forensic analysis by a determined adversary with physical access to the machine.

---

## About the Name

Shuraksha (शुरक्षा) is derived from the Sanskrit word for protection. The logo features the traditional Hindu Svastika, an ancient symbol of good fortune used for thousands of years across Hindu, Buddhist, and Jain traditions.

---

*Built with Python and PyQt6  |  AES-256-GCM  |  Local Only  |  No Cloud*
```

Save with `Ctrl+S`.

---

**STEP 4: Connect and push to GitHub**

Run these commands one by one in the VS Code terminal:
```
git remote add origin https://github.com/theusualprogrammer/shuraksha.git
```
```
git branch -M main
```
```
git add .
```
```
git commit -m "Initial commit - Shuraksha Security Vault v1.0.0"
```
```
git push -u origin main
```

When you run the push command a browser window or a credentials popup will appear asking you to sign in to GitHub. Sign in with your GitHub account and the push will complete.

---

**STEP 5: Verify**

Go to:
```
https://github.com/theusualprogrammer/shuraksha