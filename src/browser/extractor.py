# -----------------------------------------------
# Shuraksha - Browser Password Extractor
# File: src/browser/extractor.py
# -----------------------------------------------
# Extracts saved passwords from:
#   - Google Chrome    (all profiles)
#   - Microsoft Edge   (all profiles)
#   - Brave Browser    (all profiles)
#   - Mozilla Firefox  (all profiles)
#   - Opera
#   - Vivaldi
#
# Handles multiple profiles per browser:
#   Default, Profile 1, Profile 2, etc.
#
# How Chromium extraction works:
#   1. Each profile has its own Login Data SQLite db
#   2. The AES key is in Local State (encrypted with DPAPI)
#   3. We copy the db to a temp file (Chrome locks it)
#   4. Decrypt each password with the AES key
# -----------------------------------------------

import os
import re
import json
import base64
import sqlite3
import shutil
import tempfile
import traceback
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
LOCAL  = Path(os.environ.get('LOCALAPPDATA', ''))
ROAM   = Path(os.environ.get('APPDATA', ''))

CHROMIUM_BROWSERS = {
    'Chrome': LOCAL / 'Google'       / 'Chrome'         / 'User Data',
    'Edge'  : LOCAL / 'Microsoft'    / 'Edge'            / 'User Data',
    'Brave' : LOCAL / 'BraveSoftware'/ 'Brave-Browser'   / 'User Data',
    'Opera' : ROAM  / 'Opera Software'/ 'Opera Stable',
    'Vivaldi': LOCAL / 'Vivaldi'     / 'User Data',
    'Chrome Beta': LOCAL / 'Google'  / 'Chrome Beta'     / 'User Data',
    'Chrome Dev' : LOCAL / 'Google'  / 'Chrome Dev'      / 'User Data',
}

FIREFOX_PATH = ROAM / 'Mozilla' / 'Firefox' / 'Profiles'


class BrowserExtractor:
    """
    Extracts saved credentials from all installed browsers.
    Handles multiple profiles per browser correctly.
    """

    def __init__(self):
        self.errors = []

    def extract_all(self) -> List[Dict]:
        """
        Extract credentials from all available browsers.
        Returns a combined deduplicated list.
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

    # -----------------------------------------------
    # CHROMIUM
    # -----------------------------------------------

    def _get_encryption_key(self, base_path: Path) -> Optional[bytes]:
        """
        Extract the AES encryption key from Local State.
        This key is used to decrypt all passwords in the browser.
        """
        if not WIN32_AVAILABLE or not CRYPTO_AVAILABLE:
            return None

        local_state = base_path / 'Local State'
        if not local_state.exists():
            return None

        try:
            with open(local_state, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # The key is base64 encoded in os_crypt.encrypted_key
            b64_key       = state['os_crypt']['encrypted_key']
            encrypted_key = base64.b64decode(b64_key)

            # First 5 bytes are the literal string 'DPAPI'
            # Remove them before decrypting
            encrypted_key = encrypted_key[5:]

            # Decrypt with Windows DPAPI
            key = win32crypt.CryptUnprotectData(
                encrypted_key,
                None, None, None, 0
            )[1]

            return key

        except Exception:
            return None

    def _decrypt_password(self, encrypted: bytes,
                          key: Optional[bytes]) -> str:
        """
        Decrypt a single password value.

        Chrome 80+ format:
            Bytes 0-2   : b'v10' or b'v11' prefix
            Bytes 3-14  : 12-byte nonce
            Bytes 15:-16: ciphertext
            Last 16     : GCM auth tag (included in ciphertext)

        Older format uses raw DPAPI encryption.
        """
        if not encrypted:
            return ""

        try:
            # Chrome 80+ AES-GCM format
            if encrypted[:3] in (b'v10', b'v11', b'v20'):
                if not key or not CRYPTO_AVAILABLE:
                    return ""

                nonce      = encrypted[3:15]
                ciphertext = encrypted[15:]

                cipher   = AES.new(key, AES.MODE_GCM, nonce=nonce)
                password = cipher.decrypt(ciphertext)

                # Strip the 16-byte GCM tag from the end
                password = password[:-16]

                return password.decode('utf-8', errors='replace')

            else:
                # Older DPAPI format
                if not WIN32_AVAILABLE:
                    return ""
                result = win32crypt.CryptUnprotectData(
                    encrypted, None, None, None, 0
                )[1]
                return result.decode('utf-8', errors='replace')

        except Exception:
            return ""

    def _get_all_profiles(self, base_path: Path) -> List[str]:
        """
        Find all profile folders inside a browser's User Data dir.
        Returns names like: Default, Profile 1, Profile 2, etc.
        Also includes Guest Profile and System Profile if present.
        """
        profiles = []

        if not base_path.exists():
            return profiles

        # Always check Default first
        if (base_path / 'Default').exists():
            profiles.append('Default')

        # Find all numbered profiles
        try:
            for item in sorted(base_path.iterdir()):
                if not item.is_dir():
                    continue
                name = item.name
                # Profile 1, Profile 2, Profile 3...
                if re.match(r'^Profile \d+$', name):
                    profiles.append(name)
                # Some browsers use different naming
                elif re.match(r'^Profile_\d+$', name):
                    profiles.append(name)
        except Exception:
            pass

        return profiles

    def _extract_chromium(self, browser_name: str,
                          base_path: Path) -> List[Dict]:
        """
        Extract saved passwords from ALL profiles of a
        Chromium-based browser.

        Steps:
        1. Get the shared AES key from Local State
        2. Find every profile folder
        3. For each profile, copy Login Data to a temp file
        4. Query the logins table
        5. Decrypt each password
        """
        results = []

        # Get the decryption key (shared across all profiles)
        key = self._get_encryption_key(base_path)

        # Get all profiles
        profiles = self._get_all_profiles(base_path)

        if not profiles:
            # Some browsers store Login Data directly in base_path
            if (base_path / 'Login Data').exists():
                profiles = ['']

        for profile in profiles:
            if profile:
                login_db = base_path / profile / 'Login Data'
                profile_label = profile
            else:
                login_db = base_path / 'Login Data'
                profile_label = 'Default'

            if not login_db.exists():
                continue

            # Copy the database to a temp file
            # Chrome keeps Login Data locked while running
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
                        "password_value, date_last_used, "
                        "times_used "
                        "FROM logins "
                        "WHERE username_value != '' "
                        "ORDER BY date_last_used DESC"
                    )
                    rows = cursor.fetchall()
                except Exception:
                    # Older schema without date_last_used
                    try:
                        cursor.execute(
                            "SELECT origin_url, username_value, "
                            "password_value "
                            "FROM logins "
                            "WHERE username_value != ''"
                        )
                        rows = [
                            (r[0], r[1], r[2], 0, 0)
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

                    if not password:
                        continue

                    results.append({
                        'browser' : (
                            f"{browser_name} "
                            f"({profile_label})"
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

        Firefox logins.json contains:
            hostname       : the website URL
            encryptedUsername : base64 encoded username
            encryptedPassword : base64 encoded password

        Full decryption requires Mozilla NSS library.
        We extract the site and encoded data and attempt
        basic decoding where possible.
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

                    # Try to get username from
                    # encryptedUsername field
                    enc_user = login.get(
                        'encryptedUsername', ''
                    )
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
            url = url.split(':')[0]   # Remove port
            return url.strip()
        except Exception:
            return url

    def get_available_browsers(self) -> List[str]:
        """
        Return a list of browsers that are installed
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
        Return a summary of what was found without
        extracting passwords. Useful for showing the
        user what will be imported before they confirm.
        """
        summary = {}

        for name, path in CHROMIUM_BROWSERS.items():
            if not path.exists():
                continue
            profiles = self._get_all_profiles(path)
            count    = len(profiles)
            if count > 0:
                summary[name] = {
                    'profiles': count,
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
                    'profiles': len(ff_profiles),
                    'profile_names': ff_profiles,
                }

        return summary  