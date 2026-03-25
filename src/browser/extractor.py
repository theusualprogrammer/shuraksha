# -----------------------------------------------
# Shuraksha - Browser Password Extractor
# File: src/browser/extractor.py
# -----------------------------------------------
# Extracts saved passwords from:
#   - Google Chrome
#   - Microsoft Edge
#   - Brave Browser
#   - Mozilla Firefox
#
# How Chrome/Edge/Brave extraction works:
#   1. Chrome stores passwords in a SQLite database
#      at AppData\Local\Google\Chrome\User Data\
#      Default\Login Data
#   2. Passwords are encrypted using Windows DPAPI
#      (Data Protection API) with an additional
#      AES-256-GCM layer added in Chrome 80+
#   3. The AES key is stored in a file called
#      Local State, encrypted with Windows DPAPI
#   4. We decrypt the DPAPI layer first to get the
#      AES key, then decrypt each password
#
# How Firefox extraction works:
#   1. Firefox stores passwords in logins.json
#   2. Encrypted with a master password using NSS
#   3. We read the logins.json directly for
#      sites and usernames (passwords need NSS
#      which requires Firefox libraries)
# -----------------------------------------------

import os
import re
import json
import base64
import sqlite3
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict

# Windows DPAPI for Chrome password decryption
try:
    import win32crypt
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

# AES-256-GCM for Chrome 80+ passwords
try:
    from Crypto.Cipher import AES
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# -----------------------------------------------
# BROWSER PROFILE PATHS
# -----------------------------------------------
LOCAL_APP  = Path(os.environ.get('LOCALAPPDATA', ''))
ROAMING    = Path(os.environ.get('APPDATA', ''))

BROWSER_PATHS = {
    'Chrome': LOCAL_APP / 'Google'  / 'Chrome'  / 'User Data',
    'Edge'  : LOCAL_APP / 'Microsoft'/ 'Edge'   / 'User Data',
    'Brave' : LOCAL_APP / 'BraveSoftware' / 'Brave-Browser' / 'User Data',
}

FIREFOX_PATH = ROAMING / 'Mozilla' / 'Firefox' / 'Profiles'


class BrowserExtractor:
    """
    Extracts saved credentials from installed browsers.

    Usage:
        extractor = BrowserExtractor()
        results   = extractor.extract_all()

    Returns a list of dicts:
        [
            {
                'browser' : 'Chrome',
                'site'    : 'https://example.com',
                'username': 'user@example.com',
                'password': 'mypassword',
            },
            ...
        ]
    """

    def extract_all(self) -> List[Dict]:
        """
        Extract credentials from all available browsers.
        Returns a combined list from all sources.
        """
        results = []

        # Chrome-based browsers
        for browser_name, base_path in BROWSER_PATHS.items():
            if base_path.exists():
                try:
                    creds = self._extract_chromium(
                        browser_name, base_path
                    )
                    results.extend(creds)
                except Exception:
                    continue

        # Firefox
        try:
            creds = self._extract_firefox()
            results.extend(creds)
        except Exception:
            pass

        return results

    # -----------------------------------------------
    # CHROMIUM-BASED BROWSERS
    # -----------------------------------------------

    def _get_chrome_key(self, base_path: Path) -> bytes:
        """
        Extract and decrypt the AES key from Local State.

        Chrome 80+ stores an AES-256-GCM key in the
        Local State file. This key is encrypted with
        Windows DPAPI. We decrypt it to get the raw
        AES key used for password encryption.
        """
        if not WIN32_AVAILABLE or not CRYPTO_AVAILABLE:
            return None

        local_state_path = base_path / 'Local State'
        if not local_state_path.exists():
            return None

        try:
            with open(local_state_path, 'r',
                      encoding='utf-8') as f:
                local_state = json.load(f)

            # The encrypted key is base64-encoded in Local State
            encrypted_key = base64.b64decode(
                local_state['os_crypt']['encrypted_key']
            )

            # Remove the DPAPI prefix (first 5 bytes: DPAPI)
            encrypted_key = encrypted_key[5:]

            # Decrypt with Windows DPAPI
            key = win32crypt.CryptUnprotectData(
                encrypted_key, None, None, None, 0
            )[1]

            return key

        except Exception:
            return None

    def _decrypt_chrome_password(
        self, encrypted_pwd: bytes, key: bytes
    ) -> str:
        """
        Decrypt a Chrome-encrypted password.

        Chrome 80+ format:
            Bytes 0-2:   'v10' or 'v11' prefix
            Bytes 3-14:  12-byte nonce (IV)
            Bytes 15:-16 ciphertext
            Last 16:     GCM authentication tag

        Older Chrome format uses Windows DPAPI directly.
        """
        if not encrypted_pwd:
            return ""

        try:
            # Check for Chrome 80+ format (v10 or v11 prefix)
            if (encrypted_pwd[:3] == b'v10' or
                    encrypted_pwd[:3] == b'v11'):

                if not CRYPTO_AVAILABLE or not key:
                    return ""

                # Extract nonce and ciphertext
                nonce      = encrypted_pwd[3:15]
                ciphertext = encrypted_pwd[15:]

                # Decrypt with AES-256-GCM
                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                password = cipher.decrypt(ciphertext)

                # Remove the 16-byte GCM tag from the end
                password = password[:-16].decode('utf-8')
                return password

            else:
                # Older format: decrypt with Windows DPAPI
                if not WIN32_AVAILABLE:
                    return ""
                password = win32crypt.CryptUnprotectData(
                    encrypted_pwd, None, None, None, 0
                )[1]
                return password.decode('utf-8')

        except Exception:
            return ""

    def _extract_chromium(
        self, browser_name: str, base_path: Path
    ) -> List[Dict]:
        """
        Extract saved passwords from a Chromium-based browser.

        Steps:
        1. Get the AES decryption key from Local State
        2. Find all profile folders (Default, Profile 1, etc.)
        3. Copy the Login Data SQLite database to a temp file
           (Chrome locks the file while running)
        4. Query the logins table
        5. Decrypt each password
        """
        results = []
        key     = self._get_chrome_key(base_path)

        # Find all profile directories
        profiles = ['Default']
        for item in base_path.iterdir():
            if (item.is_dir() and
                    item.name.startswith('Profile')):
                profiles.append(item.name)

        for profile in profiles:
            login_db = base_path / profile / 'Login Data'
            if not login_db.exists():
                continue

            # Copy to temp file because Chrome locks the db
            tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix='.db'
            )
            tmp.close()

            try:
                shutil.copy2(str(login_db), tmp.name)

                conn   = sqlite3.connect(tmp.name)
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT origin_url, username_value, "
                    "password_value FROM logins "
                    "WHERE username_value != ''"
                )

                for url, username, enc_pwd in cursor.fetchall():
                    if not username:
                        continue

                    password = self._decrypt_chrome_password(
                        enc_pwd, key
                    )

                    if password:
                        results.append({
                            'browser' : browser_name,
                            'site'    : self._clean_url(url),
                            'username': username,
                            'password': password,
                        })

                conn.close()

            except Exception:
                pass

            finally:
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass

        return results

    # -----------------------------------------------
    # FIREFOX
    # -----------------------------------------------

    def _extract_firefox(self) -> List[Dict]:
        """
        Extract saved credentials from Firefox.

        Firefox stores logins in logins.json inside
        each profile folder. The passwords are encrypted
        using Mozilla NSS (Network Security Services).

        We extract the site and username from logins.json.
        Full password decryption requires the Firefox
        NSS library which varies by installation.
        We attempt decryption where possible.
        """
        results = []

        if not FIREFOX_PATH.exists():
            return results

        # Find all Firefox profiles
        for profile_dir in FIREFOX_PATH.iterdir():
            if not profile_dir.is_dir():
                continue

            logins_file = profile_dir / 'logins.json'
            if not logins_file.exists():
                continue

            try:
                with open(logins_file, 'r',
                          encoding='utf-8') as f:
                    logins_data = json.load(f)

                for login in logins_data.get('logins', []):
                    hostname = login.get(
                        'hostname', ''
                    ) or login.get('formSubmitURL', '')

                    username = login.get(
                        'usernameField', ''
                    )

                    # Try to get the encrypted username value
                    enc_username = login.get(
                        'encryptedUsername', ''
                    )

                    if not hostname:
                        continue

                    results.append({
                        'browser' : 'Firefox',
                        'site'    : self._clean_url(hostname),
                        'username': (
                            enc_username[:32]
                            if enc_username
                            else '(encrypted)'
                        ),
                        'password': '(requires Firefox NSS)',
                    })

            except Exception:
                continue

        return results

    # -----------------------------------------------
    # UTILITIES
    # -----------------------------------------------

    def _clean_url(self, url: str) -> str:
        """
        Clean a URL to extract just the domain name.
        https://www.example.com/login -> example.com
        """
        if not url:
            return url
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'^www\.', '', url)
        url = url.split('/')[0]
        url = url.split('?')[0]
        return url

    def get_available_browsers(self) -> List[str]:
        """
        Return a list of browser names that are
        installed and have credential databases.
        """
        available = []

        for name, path in BROWSER_PATHS.items():
            if path.exists():
                login_db = path / 'Default' / 'Login Data'
                if login_db.exists():
                    available.append(name)

        if FIREFOX_PATH.exists():
            for p in FIREFOX_PATH.iterdir():
                if (p.is_dir() and
                        (p / 'logins.json').exists()):
                    available.append('Firefox')
                    break

        return available