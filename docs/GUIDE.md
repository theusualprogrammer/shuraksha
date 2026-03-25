# Shuraksha Security Vault
### User Guide  |  Version 1.0.0
### https://github.com/theusualprogrammer/shuraksha

---

## What is Shuraksha

Shuraksha (Sanskrit for Protection) is a personal encrypted security vault for Windows. It protects your files, photos, videos, passwords, and private notes using military-grade AES-256-GCM encryption. Everything stays only on your computer. Nothing is ever sent to any cloud, server, or external service.

Shuraksha uses a two-layer deception system to protect your data from shoulder surfing, unauthorized access, and casual snooping.

---

## System Requirements

- Windows 10 or Windows 11 (64-bit)
- 200 MB free disk space
- No internet connection required
- No additional software required

---

## Installation

1. Run `Shuraksha_Setup_v1.0.0.exe`
2. Follow the installation wizard
3. Choose your installation folder (default is recommended)
4. Create desktop and Start Menu shortcuts when prompted
5. After installation the Registration Wizard opens automatically

---

## Registration (First Time Setup)

Registration happens only once during installation. You will be asked to set:

**Display Name**
Any name or nickname. Used only as a greeting inside your vault.

**Master Password**
The password you type every time you open Shuraksha.
Minimum 8 characters. Use uppercase, lowercase, numbers, and symbols.

**Password Hints**
Three personal clues that only you understand.
These help you remember your password if you forget it.
Do not write the actual password or any part of it as a hint.

**Date of Birth**
This is your secret vault key in DD/MM/YYYY format.
This is the most important part of registration.
There is no recovery option if you forget this date.
Read the next section carefully before setting it.

---

## How the Two-Layer System Works

Shuraksha uses two layers of deception to protect your real vault from anyone watching your screen.

### Layer One: The Decoy Dashboard

When Shuraksha opens it always shows a light mode file manager.
This is the decoy layer. It shows real files and folders from your system.
It behaves exactly like a normal file manager.
Anyone watching your screen sees a completely ordinary application.
None of your protected vault files are visible here.

### Layer Two: The Hidden Vault

To reach your real vault you must perform two hidden steps.

**Step 1: The Dark Mode Toggle**
In the top right corner of the application there is a small sun and moon theme toggle. Slide it to dark mode. To any observer this looks like switching the app theme. It is actually the trigger that opens the second layer.

**Step 2: The BODMAS Screen**
After sliding to dark mode a BODMAS arithmetic question appears on screen. To any observer this looks like a mathematical security challenge. You do not solve the maths question. Instead type your date of birth in DD/MM/YYYY format into the answer box and press Submit. The real vault opens immediately.

---

## Daily Use: Step by Step

### Opening the Vault

1. Launch Shuraksha from the desktop shortcut
2. The login screen appears
3. Type your master password and press Enter
4. The decoy file manager opens in light mode
5. Slide the theme toggle at the top right to dark mode
6. The BODMAS screen appears
7. Type your date of birth in DD/MM/YYYY format
8. Press Submit
9. The real vault opens

### Closing the Vault

Press Ctrl+Shift+X at any time to instantly lock the vault and return to the login screen. This is the panic button. Use it any time someone approaches your screen unexpectedly.

The vault also locks automatically after 5 minutes of inactivity.

---

## The Real Vault: Features

### Encrypted Files

Store any file type in the vault. Documents, photos, videos, audio, archives, code files. All stored files are encrypted with AES-256-GCM encryption. The original file is never left on disk in plain form.

**To add a file:**
Click the plus ADD FILE button. Select any file from your computer. It is encrypted and stored in the vault immediately.

**To export a file:**
Click EXPORT next to any stored file. Choose a destination folder. The file is decrypted and saved there.

**To delete a file:**
Click DELETE next to any stored file. The encrypted file is overwritten with random data three times before deletion to prevent recovery.

### Credentials

Store usernames and passwords for websites and applications. Each credential stores the site name, username, and password. Passwords are hidden by default. Click SHOW to reveal. Click COPY to copy to clipboard. The clipboard is automatically cleared after 30 seconds.

**To add a credential:**
Click plus ADD CREDENTIAL. Enter the site name, username, and password.

### Secure Notes

A private encrypted notepad. Write anything you want to keep private. Click SAVE NOTES to encrypt and save. Content is encrypted with AES-256-GCM and stored locally.

### Access Log

Every action performed in the vault is recorded with a timestamp. Login attempts, file additions, exports, deletions, credential access, and lock events are all logged. The log is stored encrypted and only visible inside the real vault.

---

## Security Features

### Encryption
All vault data is encrypted using AES-256-GCM. This is the same encryption standard used by governments, banks, and military organizations worldwide. The encryption key is derived from your master password using PBKDF2 with 480,000 rounds of SHA-256 hashing. This makes brute force attacks extremely slow.

### Password Hashing
Your master password and date of birth are never stored in plain text anywhere on your computer. Only a cryptographic hash is stored. Even if someone finds the data files they cannot read your password from them.

### Secure File Deletion
When you delete a file from the vault it is overwritten with random data three times before being removed from disk. This prevents data recovery tools from recovering deleted vault files.

### Clipboard Auto-Clear
When you copy a password from the credentials section the clipboard is automatically cleared after 30 seconds so passwords do not persist in the clipboard.

### Auto-Lock
The vault automatically locks after 5 minutes of inactivity and returns to the login screen. All sensitive data is cleared from memory.

### Panic Button
Press Ctrl+Shift+X at any time to instantly lock the vault. This works even while you are in the middle of viewing files or credentials.

### Lockout Protection
After 5 wrong password attempts on the login screen the application locks for 5 minutes. A countdown timer is shown. Wrong date of birth entries on the BODMAS screen also count toward a lockout after 4 attempts, showing a convincing fake crash screen.

### Local Only
No network connections are made at any time. The vault process is designed to operate completely offline. No telemetry, no analytics, no updates, no cloud sync.

---

## Forgot Your Password

If you forget your master password click the Forgot password link on the login screen. Your three password hints are revealed one at a time. Click Reveal Next Hint to see each one.

If you still cannot remember your password after seeing all three hints a Wipe Vault button appears. This permanently and irreversibly deletes all vault data and allows you to start fresh with a new registration.

There is no other recovery option. This is by design. A recovery mechanism would be a security vulnerability.

---

## Forgot Your Date of Birth

Your date of birth is the key to the real vault. If you forget it there is no recovery option. The BODMAS screen will reject all incorrect dates. After 4 wrong attempts the fake crash screen appears and the application locks.

The only option if you forget your date of birth is to uninstall Shuraksha, delete the AppData folder, and reinstall and register fresh. All vault data will be lost.

This is why it is important to choose a date of birth you will never forget during registration.

---

## Uninstalling Shuraksha

Go to Windows Settings, Apps, and find Shuraksha in the list. Click Uninstall. The uninstaller will ask whether you want to delete your encrypted vault data. Click YES to delete everything permanently. Click NO to keep your vault data files on the computer even after the application is removed.

---

## Data Storage Locations

All Shuraksha data is stored in:
```
C:\Users\YourName\AppData\Roaming\Shuraksha\
```

Inside this folder:
```
user.dat          Your encrypted registration data
vault\
  meta.dat        Encrypted file metadata index
  creds.dat       Encrypted credentials database
  notes.dat       Encrypted secure notes
  access.log      Encrypted access history
  files\          Encrypted vault file storage
```

None of these files can be read without your master password.

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+Shift+X | Instantly lock the vault |
| Enter | Submit password on login screen |
| Enter | Submit answer on BODMAS screen |

---

## Troubleshooting

**The application opens but my password is not accepted**
Make sure Caps Lock is not on. Passwords are case sensitive. If you have forgotten your password use the Forgot password link.

**The BODMAS screen is not accepting my date of birth**
Make sure you are typing in DD/MM/YYYY format with forward slashes. Example: 15/08/1998. The slashes are added automatically as you type. Make sure the year is four digits.

**The vault locked itself**
The vault auto-locks after 5 minutes of inactivity. This is a security feature. Log in again with your master password and navigate to the vault.

**I see a fake crash screen**
You entered too many wrong answers on the BODMAS screen. Click Restart Application on the crash screen to try again.

**A file I exported looks corrupted**
Make sure you are exporting to a location where you have write permission. Try exporting to the Desktop or Downloads folder.

**The application will not start after installation**
Run the application as administrator once by right-clicking the desktop shortcut and choosing Run as administrator. This resolves most first-launch permission issues.

---

## Privacy Statement

Shuraksha collects no data whatsoever. No usage statistics, no crash reports, no telemetry, no analytics. The application makes no network connections of any kind. All data stays on your machine permanently.

---

## About the Name

Shuraksha (शुरक्षा) is derived from the Sanskrit word for protection and security. The application logo features the traditional Hindu Svastika, an ancient symbol of good fortune and well-being used for thousands of years across Hindu, Buddhist, and Jain traditions, completely distinct from any political symbol.

---

## Version History

| Version | Date | Notes |
|---|---|---|
| 1.0.0 | March 2026 | Initial release |

---

## Support and Source Code

GitHub: https://github.com/theusualprogrammer/shuraksha

---

*Shuraksha Security Vault  |  Version 1.0.0  |  Built with Python and PyQt6*
*AES-256-GCM Encryption  |  Local Only  |  No Cloud  |  No Servers*
```

Save with `Ctrl+S`. Now commit:
```
git add .
git commit -m "Added full user guide documentation"