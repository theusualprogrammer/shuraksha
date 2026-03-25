# Shuraksha Security Vault
## Final Year Project Report
### Cybersecurity  |  2025-2026

---

## 1. Project Overview

**Project Title:** Shuraksha Security Vault

**Project Type:** Desktop Security Application

**Platform:** Windows 10 / Windows 11 (64-bit)

**GitHub:** https://github.com/theusualprogrammer/shuraksha

**Version:** 1.0.0

### 1.1 Abstract

Shuraksha is a personal encrypted security vault designed for non-technical users on Windows. It addresses the real-world problem of protecting sensitive personal data against casual threats including shoulder surfing, unauthorized device access, and browser credential theft. The application uses AES-256-GCM military-grade encryption combined with a two-layer deception system to protect files, passwords, photos, videos, and private notes. All data is stored exclusively on the local machine with no cloud synchronization or external network connections of any kind.

### 1.2 Motivation

Most ordinary users store sensitive files in plain folders, save passwords in browsers without master password protection, and keep private notes in unencrypted text files. When a device is accessed by an unauthorized person, whether a family member, colleague, or attacker, all this data is immediately visible. Existing solutions like VeraCrypt are powerful but require technical knowledge. Shuraksha is designed to be accessible to anyone while providing serious security through deception rather than complexity.

---

## 2. Problem Statement

### 2.1 Threats Addressed

**Shoulder Surfing**
An observer watching the screen of a device can see files, passwords, and sensitive information. Shuraksha addresses this by showing a completely convincing decoy file manager to any observer while hiding the real vault behind a hidden trigger.

**Unauthorized Physical Access**
When a device is left unattended or picked up by another person, all files are immediately accessible. Shuraksha requires a master password on every launch and auto-locks after inactivity.

**Browser Credential Theft**
Passwords saved in browsers are stored with minimal protection and can be extracted by malware or an attacker with physical access. Shuraksha extracts these credentials and stores them in an encrypted vault.

**Screenshot and Screen Recording Surveillance**
Malware or an observer using screen recording software can capture sensitive information displayed on screen. Shuraksha blocks the Windows screenshot API and detects screen recording processes.

**File Recovery After Deletion**
Standard file deletion does not remove data from disk. Data recovery tools can recover deleted files. Shuraksha overwrites deleted vault files with random data three times before deletion.

### 2.2 Target Users

Shuraksha is designed for the general public with no technical background. The interface uses familiar concepts (a file manager, a theme toggle, a maths question) to hide its true security mechanisms from observers while remaining usable by the person who set it up.

---

## 3. Features

### 3.1 Core Security Features

| Feature | Implementation |
|---|---|
| File encryption | AES-256-GCM with PBKDF2-SHA256 key derivation |
| Password hashing | PBKDF2 with 480,000 rounds of SHA-256 |
| Secure file deletion | 3-pass random overwrite before unlink |
| Clipboard protection | Auto-clear after 30 seconds |
| Screenshot blocking | Windows SetWindowDisplayAffinity API |
| Print Screen blocking | Low-level keyboard hook via SetWindowsHookEx |
| Anti-debug | IsDebuggerPresent + CheckRemoteDebuggerPresent |
| Process scanning | Background thread scanning for keyloggers |
| Auto-lock | Configurable inactivity timeout (default 5 min) |
| Panic lock | Ctrl+Shift+X instant lock from any screen |

### 3.2 Deception Layer Features

| Feature | Description |
|---|---|
| Decoy dashboard | Fully functional light mode file manager showing real system files |
| Hidden trigger | Theme toggle in top-right corner activates vault layer |
| BODMAS screen | Fake maths challenge that accepts date of birth as the real answer |
| Fake crash screen | Displayed after too many wrong answers on BODMAS screen |
| Lockout system | 5-minute lockout after repeated wrong password attempts |

### 3.3 Vault Features

| Feature | Description |
|---|---|
| Encrypted file storage | Any file type, AES-256-GCM encrypted |
| Credential manager | Sites, usernames, passwords with show/hide/copy |
| Secure notes | AES-256-GCM encrypted private notepad |
| Access log | Encrypted timestamped log of all vault operations |
| Browser import | Extract credentials from Chrome, Edge, Brave, Firefox |
| Password hints | Three personal clues for password recovery |
| Emergency wipe | Complete vault destruction if password forgotten |

---

## 4. System Architecture

### 4.1 Application Flow
```
Launch
  |
  v
Registration check
  |
  +-- Not registered --> Registration Wizard --> user.dat created
  |
  +-- Registered --> Login Screen
                        |
                        v
                   Master password verified
                        |
                        v
                   Fake Dashboard (Light Mode)
                        |
                   Theme toggle --> dark mode
                        |
                        v
                   BODMAS Screen
                        |
                   Date of birth entered
                        |
                        v
                   Real Vault Dashboard
                        |
                   Lock / Panic / Auto-lock
                        |
                        v
                   Login Screen
```

### 4.2 Data Structure
```
user.dat (stored in AppData\Roaming\Shuraksha\)
{
    "password_hash": "...",    <- Outside encrypted blob
    "password_salt": "...",    <- Outside encrypted blob
    "encrypted": {             <- AES-256-GCM encrypted
        "ciphertext": "...",
        "nonce": "...",
        "salt": "..."
    }
}
```

The encrypted blob contains:
```
{
    "username": "...",
    "hints": ["...", "...", "..."],
    "dob_hash": "...",
    "dob_salt": "...",
    "setup_complete": true
}
```

### 4.3 Module Structure
```
src/
├── core/
│   ├── crypto.py       AES-256-GCM engine, PBKDF2 key derivation
│   └── security.py     Anti-screenshot, anti-debug, process scanner
├── installer/
│   └── registration.py Nine-page registration wizard
├── ui/
│   ├── login.py        Login screen, lockout, hints overlay
│   ├── fake_dashboard.py  Decoy light mode file manager
│   ├── bodmas.py       Fake BODMAS challenge screen
│   └── vault_dashboard.py Real encrypted vault
├── browser/
│   └── extractor.py    Browser credential extractor
└── main.py             Application controller
```

---

## 5. Cryptographic Implementation

### 5.1 Key Derivation

Password-Based Key Derivation Function 2 (PBKDF2) is used to convert the master password into a 256-bit AES encryption key.
```
Key = PBKDF2(
    password  = master_password,
    salt      = random_32_bytes,
    iterations = 480000,
    hash      = SHA-256,
    length    = 32 bytes
)
```

480,000 iterations is the NIST recommended minimum for PBKDF2-SHA256 as of 2023. This means an attacker must perform 480,000 hash computations for every password they attempt, making brute force attacks computationally expensive.

### 5.2 Encryption

AES-256-GCM (Advanced Encryption Standard, 256-bit key, Galois/Counter Mode) is used for all data encryption.

GCM mode provides authenticated encryption. This means:
- The data is encrypted (confidentiality)
- A cryptographic tag is generated (integrity)
- If any bit of the ciphertext is modified, decryption fails

This prevents both reading and tampering with vault data.

### 5.3 Password Hashing

Passwords and dates of birth are never stored in plain text. Only a hash is stored:
```
hash, salt = PBKDF2(value, random_salt, 480000, SHA-256)
```

During verification:
```
computed = PBKDF2(input, stored_salt, 480000, SHA-256)
correct  = (computed == stored_hash)
```

### 5.4 Data Structure Separation

A critical design decision is that `password_hash` and `password_salt` are stored outside the encrypted blob. This allows password verification without first decrypting the blob, which would require the password we are trying to verify. The inner data (username, hints, DOB) is only accessible after the password is verified.

---

## 6. The Two-Layer Deception System

### 6.1 Design Rationale

Traditional security applications announce their presence. A visible vault application tells an attacker exactly where to focus their efforts. Shuraksha takes the opposite approach: hide the existence of the vault entirely by making the application look like something else.

### 6.2 Layer One: The Decoy Dashboard

The decoy is a fully functional Windows file manager built with PyQt6. It reads real files and folders from the system using Python's pathlib module. The interface matches the aesthetic of modern file managers with a sidebar, search bar, sort controls, and file grid. It is indistinguishable from a real application to a casual observer.

The only hidden element is the sun/moon theme toggle in the top-right corner. This looks identical to the theme toggle found on modern applications. Nobody watching a screen would identify it as a vault trigger.

### 6.3 Layer Two: The BODMAS Screen

The BODMAS screen appears when the theme toggle is switched to dark mode. It shows a randomly generated arithmetic expression using the BODMAS rules format. The right panel shows a session timer counting down, encryption status, and security parameters. The entire presentation is designed to look like a legitimate security challenge.

The actual vault entry mechanism is typing the date of birth in DD/MM/YYYY format into the answer field. This is verified against the stored hash. Nobody observing the screen would guess that a date format is the expected input.

### 6.4 Fake Crash Screen

After four wrong inputs on the BODMAS screen a fake crash screen appears showing error codes, stack traces, and module names. This looks like a genuine application crash. Clicking Restart Application resets the challenge with a new question. This prevents brute force attempts while maintaining the deception.

---

## 7. Security Analysis

### 7.1 Threat Model

**Threat:** Shoulder surfer observing the screen
**Mitigation:** Decoy dashboard shows nothing sensitive. Real vault is hidden behind two non-obvious triggers.

**Threat:** Someone picking up the device
**Mitigation:** Master password required on every launch. Auto-lock after 5 minutes. Panic lock on Ctrl+Shift+X.

**Threat:** Brute force password attack
**Mitigation:** 5-attempt lockout with 5-minute timer. PBKDF2 with 480,000 iterations makes each attempt computationally expensive.

**Threat:** Screenshot or screen recording
**Mitigation:** Windows SetWindowDisplayAffinity makes vault window appear black in screenshots. Print Screen key is blocked via low-level keyboard hook. Screen recording processes are detected and vault locks.

**Threat:** Memory forensics or debugger analysis
**Mitigation:** IsDebuggerPresent and CheckRemoteDebuggerPresent checks. Plain password cleared from memory immediately after use. Vault locks if debugger detected.

**Threat:** File recovery after deletion
**Mitigation:** 3-pass random overwrite before file deletion.

**Threat:** Browser credential theft
**Mitigation:** Credentials extracted from browsers and stored in encrypted vault, reducing reliance on browser-stored passwords.

### 7.2 Limitations

- Shuraksha does not protect against a determined attacker with administrative access to the machine and forensic tools
- The Windows DPAPI used for browser credential extraction can be bypassed by an attacker running as the same Windows user
- The keyboard hook for blocking Print Screen operates at the application level and can be bypassed by kernel-level screen capture tools
- Auto-lock does not protect against an attacker who waits for the vault to be open and then accesses the machine

### 7.3 Comparison with Existing Solutions

| Feature | Shuraksha | VeraCrypt | KeePass | Windows BitLocker |
|---|---|---|---|---|
| Target user | General public | Technical | Technical | General |
| Deception layer | Yes | No | No | No |
| File encryption | Yes | Yes | No | Yes |
| Credential storage | Yes | No | Yes | No |
| Browser import | Yes | No | Yes | No |
| No cloud | Yes | Yes | Optional | Yes |
| Installer | Yes | Yes | Yes | Built-in |
| Anti-screenshot | Yes | No | No | No |

---

## 8. Tech Stack

| Component | Technology | Version | Reason |
|---|---|---|---|
| Language | Python | 3.11 | Readable, cross-library support, beginner accessible |
| GUI framework | PyQt6 | 6.10 | Native Windows look, custom styling, signals |
| Encryption | cryptography | 46.0 | AES-256-GCM, PBKDF2, industry standard library |
| Additional crypto | pycryptodome | 3.23 | AES-GCM for browser password decryption |
| Windows API | pywin32 | 311 | DPAPI, keyboard hooks, window APIs |
| Process scanning | psutil | latest | Cross-platform process enumeration |
| Image processing | Pillow | 12.1 | Icon generation |
| Packaging | PyInstaller | 6.19 | Standalone exe without Python installation |
| Installer | Inno Setup | 6 | Professional Windows installer |
| Version control | Git + GitHub | - | Code management and backup |

---

## 9. Installation and Deployment

### 9.1 Building from Source
```bash
git clone https://github.com/theusualprogrammer/shuraksha
cd shuraksha
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python tools\make_icon.py
python tools\build.py
```

Then compile `installer.iss` with Inno Setup to produce the installer.

### 9.2 End User Installation

The end user receives a single file: `Shuraksha_Setup_v1.0.0.exe`. Running it:

1. Copies application files to Program Files
2. Creates desktop and Start Menu shortcuts
3. Registers in Windows Add/Remove Programs
4. Automatically launches the registration wizard
5. User completes one-time setup
6. Application is ready to use

No Python installation required on the end user machine.

---

## 10. Testing

### 10.1 Functional Tests

| Test | Expected | Result |
|---|---|---|
| Registration with valid data | user.dat created, login screen shown | Pass |
| Login with correct password | Fake dashboard opens | Pass |
| Login with wrong password | Error message, dot turns red | Pass |
| 5 wrong passwords | Lockout screen with countdown | Pass |
| Theme toggle to dark | BODMAS screen appears | Pass |
| Correct DOB on BODMAS | Real vault opens | Pass |
| Wrong answer on BODMAS | Error, dot turns red | Pass |
| 4 wrong BODMAS answers | Fake crash screen | Pass |
| Add file to vault | File encrypted and listed | Pass |
| Export file from vault | File decrypted and saved | Pass |
| Delete file from vault | 3-pass overwrite, removed | Pass |
| Add credential | Stored encrypted | Pass |
| Copy password | Clipboard cleared after 30s | Pass |
| Save notes | Encrypted and stored | Pass |
| Ctrl+Shift+X | Instant lock | Pass |
| Auto-lock | Locks after 5 minutes | Pass |
| Forgot password hints | Revealed one at a time | Pass |
| Emergency wipe | All data deleted | Pass |

### 10.2 Security Tests

| Test | Expected | Result |
|---|---|---|
| Print Screen while vault open | Nothing captured | Pass |
| Snipping Tool on vault window | Black window | Pass |
| user.dat opened in text editor | Unreadable ciphertext | Pass |
| vault files opened directly | Unreadable ciphertext | Pass |
| Wrong password after registration | Access denied | Pass |

---

## 11. Future Improvements

- USB pairing: vault locks if a paired USB drive is removed
- Steganography: hide files inside ordinary-looking images
- Time-locked files: files only accessible within set hours
- Biometric option: fingerprint as an additional factor
- Mobile companion app for credential viewing
- Encrypted backup to local USB drive
- File integrity monitoring with checksums
- Network block enforcement at the firewall level

---

## 12. Conclusion

Shuraksha successfully demonstrates that strong personal data security does not require technical knowledge from the end user. By combining military-grade AES-256-GCM encryption with a two-layer deception system, the application protects sensitive data not only through cryptographic strength but through misdirection. An observer, casual attacker, or someone who picks up the device sees a normal file manager and has no indication that an encrypted vault exists on the system.

The project covers all major aspects of applied cybersecurity: symmetric encryption, key derivation, secure deletion, anti-forensics, process monitoring, Windows API security controls, and user interface deception. It is packaged as a professional Windows application installable by any end user.

---

*Shuraksha Security Vault  |  Final Year Cybersecurity Project  |  2025-2026*
*AES-256-GCM  |  Python 3.11  |  PyQt6  |  Local Only  |  No Cloud*
```

