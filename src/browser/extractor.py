# -----------------------------------------------
# Shuraksha - Browser Password Extractor
# File: src/browser/extractor.py
# -----------------------------------------------

import os
import re
import json
import base64
import sqlite3
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Optional

try:
    import win32crypt
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

try:
    from Crypto.Cipher import AES
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# -----------------------------------------------
# BROWSER PATHS
# -----------------------------------------------
LOCAL = Path(os.environ.get('LOCALAPPDATA', ''))
ROAM  = Path(os.environ.get('APPDATA', ''))

CHROMIUM_BROWSERS = {
    'Chrome'     : LOCAL / 'Google'        / 'Chrome'       / 'User Data',
    'Edge'       : LOCAL / 'Microsoft'     / 'Edge'          / 'User Data',
    'Brave'      : LOCAL / 'BraveSoftware' / 'Brave-Browser' / 'User Data',
    'Opera'      : ROAM  / 'Opera Software' / 'Opera Stable',
    'Vivaldi'    : LOCAL / 'Vivaldi'       / 'User Data',
    'Chrome Beta': LOCAL / 'Google'        / 'Chrome Beta'   / 'User Data',
    'Chrome Dev' : LOCAL / 'Google'        / 'Chrome Dev'    / 'User Data',
}

FIREFOX_PATH = ROAM / 'Mozilla' / 'Firefox' / 'Profiles'


class BrowserExtractor:
    """
    Extracts saved credentials from all installed browsers.
    Handles multiple profiles per browser correctly.
    Garbled or unreadable passwords are silently skipped.
    """

    def __init__(self):
        self.errors = []

    # -----------------------------------------------
    # PUBLIC
    # -----------------------------------------------

    def extract_all(self) -> List[Dict]:
        """
        Extract credentials from all available browsers.
        Returns a combined deduplicated list.
        Only includes passwords that decrypted cleanly.
        """
        results = []
        seen    = set()

        for browser_name, base_path in CHROMIUM_BROWSERS.items():
            if base_path.exists():
                try:
                    creds = self._extract_chromium(
                        browser_name, base_path
                    )
                    for c in creds:
                        key = (
                            c.get('site', ''),
                            c.get('username', '')
                        )
                        if key not in seen and c.get('password'):
                            seen.add(key)
                            results.append(c)
                except Exception as e:
                    self.errors.append(
                        f"{browser_name}: {str(e)}"
                    )

        try:
            ff_creds = self._extract_firefox()
            for c in ff_creds:
                key = (
                    c.get('site', ''),
                    c.get('username', '')
                )
                if key not in seen:
                    seen.add(key)
                    results.append(c)
        except Exception as e:
            self.errors.append(f"Firefox: {str(e)}")

        return results

    def get_available_browsers(self) -> List[str]:
        """
        Return list of browsers that are installed
        and have at least one Login Data file.
        """
        available = []

        for name, path in CHROMIUM_BROWSERS.items():
            if not path.exists():
                continue
            profiles = self._get_all_profiles(path)
            for p in profiles:
                db = path / p / 'Login Data'
                if db.exists():
                    if name not in available:
                        available.append(name)
                    break

        if FIREFOX_PATH.exists():
            for p in FIREFOX_PATH.iterdir():
                if p.is_dir() and (p / 'logins.json').exists():
                    available.append('Firefox')
                    break

        return available

    def get_profile_count(self, browser_name: str) -> int:
        """Return the number of profiles found for a browser."""
        base = CHROMIUM_BROWSERS.get(browser_name)
        if not base or not base.exists():
            return 0
        return len(self._get_all_profiles(base))

    def get_extraction_summary(self) -> dict:
        """
        Return a summary of browsers and profile counts
        without extracting any passwords.
        Shown to the user before they confirm the import.
        """
        summary = {}

        for name, path in CHROMIUM_BROWSERS.items():
            if not path.exists():
                continue
            profiles = self._get_all_profiles(path)
            count    = len(profiles)
            if count > 0:
                summary[name] = {
                    'profiles'     : count,
                    'profile_names': profiles,
                }

        if FIREFOX_PATH.exists():
            ff_profiles = [
                p.name for p in FIREFOX_PATH.iterdir()
                if p.is_dir() and
                (p / 'logins.json').exists()
            ]
            if ff_profiles:
                summary['Firefox'] = {
                    'profiles'     : len(ff_profiles),
                    'profile_names': ff_profiles,
                }

        return summary

    # -----------------------------------------------
    # VALIDATION
    # -----------------------------------------------

    def _is_valid_password(self, text: str) -> bool:
        """
        Strictly validate that a decrypted string is a
        real password and not garbled binary data.

        Rules:
          - Must not be empty
          - Every character must be in the ASCII printable
            range (32-126) or common accented Latin (160-382)
          - Must contain at least one ASCII letter or digit
          - Must not start with a null byte or control char

        This rejects box-drawing characters, diamond symbols,
        and other unicode blocks that appear when decryption
        fails with the wrong key.
        """
        if not text or len(text) == 0:
            return False

        # Reject if starts with a null or control character
        if ord(text[0]) < 32:
            return False

        for c in text:
            code = ord(c)
            # Standard ASCII printable (space through tilde)
            if 32 <= code <= 126:
                continue
            # Common accented Latin characters
            if 160 <= code <= 382:
                continue
            # Everything else means bad decryption
            return False

        # Must have at least one ASCII letter or digit
        has_alnum = any(
            c.isascii() and c.isalnum()
            for c in text
        )
        if not has_alnum:
            return False

        return True

    # -----------------------------------------------
    # CHROMIUM
    # -----------------------------------------------

    def _get_encryption_key(
        self, base_path: Path
    ) -> Optional[bytes]:
        """
        Extract and decrypt the AES key from Local State.
        This key decrypts all passwords stored by the browser.
        The key itself is encrypted with Windows DPAPI.
        """
        if not WIN32_AVAILABLE or not CRYPTO_AVAILABLE:
            return None

        local_state = base_path / 'Local State'
        if not local_state.exists():
            return None

        try:
            with open(local_state, 'r', encoding='utf-8') as f:
                state = json.load(f)

            b64_key       = state['os_crypt']['encrypted_key']
            encrypted_key = base64.b64decode(b64_key)

            # First 5 bytes are the literal ASCII 'DPAPI'
            # Remove them before passing to CryptUnprotectData
            encrypted_key = encrypted_key[5:]

            key = win32crypt.CryptUnprotectData(
                encrypted_key, None, None, None, 0
            )[1]

            return key

        except Exception:
            return None

    def _decrypt_password(
        self, encrypted: bytes, key: Optional[bytes]
    ) -> str:
        """
        Decrypt a single browser-stored password.

        Chrome 80+ format:
            Bytes 0-2  : b'v10', b'v11', or b'v20' prefix
            Bytes 3-14 : 12-byte AES-GCM nonce
            Bytes 15+  : ciphertext + 16-byte GCM auth tag

        Older Chrome format:
            Raw Windows DPAPI encrypted blob.

        Returns empty string if:
            - Decryption fails
            - Result contains box-drawing or symbol characters
            - Result has no ASCII letters or digits
        """
        if not encrypted:
            return ""

        try:
            # Chrome 80+ AES-GCM encrypted format
            if encrypted[:3] in (b'v10', b'v11', b'v20'):
                if not key or not CRYPTO_AVAILABLE:
                    return ""

                nonce      = encrypted[3:15]
                ciphertext = encrypted[15:]

                cipher    = AES.new(key, AES.MODE_GCM, nonce=nonce)
                decrypted = cipher.decrypt(ciphertext)

                # Remove the 16-byte GCM authentication tag
                decrypted = decrypted[:-16]

                decoded = decrypted.decode('utf-8', errors='replace')

                # Strict validation - reject garbled results
                if not self._is_valid_password(decoded):
                    return ""

                return decoded

            else:
                # Older Chrome: raw DPAPI encryption
                if not WIN32_AVAILABLE:
                    return ""

                result  = win32crypt.CryptUnprotectData(
                    encrypted, None, None, None, 0
                )[1]
                decoded = result.decode('utf-8', errors='replace')

                if not self._is_valid_password(decoded):
                    return ""

                return decoded

        except Exception:
            return ""

    def _get_all_profiles(self, base_path: Path) -> List[str]:
        """
        Find all profile folders inside a browser User Data dir.
        Always checks Default first, then Profile 1, Profile 2...
        """
        profiles = []

        if not base_path.exists():
            return profiles

        if (base_path / 'Default').exists():
            profiles.append('Default')

        try:
            for item in sorted(base_path.iterdir()):
                if not item.is_dir():
                    continue
                name = item.name
                if re.match(r'^Profile \d+$', name):
                    profiles.append(name)
                elif re.match(r'^Profile_\d+$', name):
                    profiles.append(name)
        except Exception:
            pass

        return profiles

    def _extract_chromium(
        self, browser_name: str, base_path: Path
    ) -> List[Dict]:
        """
        Extract saved passwords from ALL profiles of a
        Chromium-based browser.

        For each profile:
            1. Copy Login Data SQLite db to temp file
               (browser locks the original while running)
            2. Query the logins table
            3. Decrypt each password
            4. Skip any that fail validation
        """
        results  = []
        key      = self._get_encryption_key(base_path)
        profiles = self._get_all_profiles(base_path)

        if not profiles:
            if (base_path / 'Login Data').exists():
                profiles = ['']

        for profile in profiles:
            if profile:
                login_db      = base_path / profile / 'Login Data'
                profile_label = profile
            else:
                login_db      = base_path / 'Login Data'
                profile_label = 'Default'

            if not login_db.exists():
                continue

            tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix='.db'
            )
            tmp.close()

            try:
                shutil.copy2(str(login_db), tmp.name)
                conn   = sqlite3.connect(tmp.name)
                cursor = conn.cursor()

                try:
                    cursor.execute(
                        "SELECT origin_url, username_value, "
                        "password_value, date_last_used "
                        "FROM logins "
                        "WHERE username_value != '' "
                        "ORDER BY date_last_used DESC"
                    )
                    rows = cursor.fetchall()
                except Exception:
                    try:
                        cursor.execute(
                            "SELECT origin_url, username_value, "
                            "password_value "
                            "FROM logins "
                            "WHERE username_value != ''"
                        )
                        rows = [
                            (r[0], r[1], r[2], 0)
                            for r in cursor.fetchall()
                        ]
                    except Exception:
                        rows = []

                for row in rows:
                    url      = row[0] or ''
                    username = row[1] or ''
                    enc_pwd  = row[2]

                    if not username:
                        continue

                    password = self._decrypt_password(enc_pwd, key)

                    # Skip empty or garbled passwords entirely
                    if not password:
                        continue

                    results.append({
                        'browser' : (
                            f"{browser_name} ({profile_label})"
                            if profile_label != 'Default'
                            else browser_name
                        ),
                        'site'    : self._clean_url(url),
                        'username': username,
                        'password': password,
                        'url'     : url,
                    })

                conn.close()

            except Exception as e:
                self.errors.append(
                    f"{browser_name}/{profile_label}: {str(e)}"
                )
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
        Extract credentials from all Firefox profiles.
        Full password decryption requires Mozilla NSS library.
        We extract site and attempt to decode username.
        """
        results = []

        if not FIREFOX_PATH.exists():
            return results

        for profile_dir in FIREFOX_PATH.iterdir():
            if not profile_dir.is_dir():
                continue

            logins_file = profile_dir / 'logins.json'
            if not logins_file.exists():
                continue

            try:
                with open(
                    logins_file, 'r', encoding='utf-8'
                ) as f:
                    data = json.load(f)

                for login in data.get('logins', []):
                    hostname = (
                        login.get('hostname', '') or
                        login.get('formSubmitURL', '')
                    )

                    if not hostname:
                        continue

                    enc_user = login.get('encryptedUsername', '')
                    username = '(Firefox encrypted)'

                    if enc_user:
                        try:
                            decoded = base64.b64decode(
                                enc_user
                            ).decode('utf-8', errors='ignore')
                            printable = ''.join(
                                c for c in decoded
                                if c.isprintable() and
                                c not in '\x00\x01\x02\x03'
                            )
                            if len(printable) > 3:
                                username = printable
                        except Exception:
                            pass

                    results.append({
                        'browser' : 'Firefox',
                        'site'    : self._clean_url(hostname),
                        'username': username,
                        'password': '(Firefox - requires NSS)',
                        'url'     : hostname,
                    })

            except Exception as e:
                self.errors.append(
                    f"Firefox/{profile_dir.name}: {str(e)}"
                )

        return results

    # -----------------------------------------------
    # UTILITIES
    # -----------------------------------------------

    def _clean_url(self, url: str) -> str:
        """
        Extract just the domain from a full URL.
        https://www.accounts.google.com/login
        -> accounts.google.com
        """
        if not url:
            return ''
        try:
            url = re.sub(r'^https?://', '', url)
            url = re.sub(r'^www\.', '', url)
            url = url.split('/')[0]
            url = url.split('?')[0]
            url = url.split(':')[0]
            return url.strip()
        except Exception:
            return url