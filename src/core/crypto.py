# -----------------------------------------------
# Shuraksha - Encryption Utilities
# File: src/core/crypto.py
# -----------------------------------------------

import json
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def derive_key(password: str, salt: bytes) -> bytes:
    # Turn a plain text password into a 256-bit AES encryption key.
    # PBKDF2 runs 480,000 rounds of SHA-256 to make brute force very slow.
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return kdf.derive(password.encode('utf-8'))


def hash_value(value: str) -> tuple:
    # Hash any text value with a random salt.
    # We never store the actual password - only the hash.
    # Returns a tuple of (hash_hex, salt_hex)
    salt = secrets.token_bytes(32)
    key  = derive_key(value, salt)
    return key.hex(), salt.hex()


def verify_value(value: str, stored_hash: str, stored_salt: str) -> bool:
    # Check if a value matches its stored hash.
    # Returns True if correct, False if wrong.
    salt = bytes.fromhex(stored_salt)
    key  = derive_key(value, salt)
    return key.hex() == stored_hash


def encrypt_json(data: dict, password: str) -> dict:
    # Encrypt a Python dictionary using AES-256-GCM.
    # Returns a dictionary with ciphertext, nonce, and salt as hex strings.
    plaintext = json.dumps(data)
    salt      = secrets.token_bytes(32)
    nonce     = secrets.token_bytes(12)
    key       = derive_key(password, salt)
    aesgcm    = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    return {
        'ciphertext': ciphertext.hex(),
        'nonce'     : nonce.hex(),
        'salt'      : salt.hex()
    }


def decrypt_json(encrypted: dict, password: str) -> dict:
    # Decrypt data that was encrypted with encrypt_json.
    # Raises an exception if the password is wrong or data was tampered with.
    salt       = bytes.fromhex(encrypted['salt'])
    nonce      = bytes.fromhex(encrypted['nonce'])
    ciphertext = bytes.fromhex(encrypted['ciphertext'])
    key        = derive_key(password, salt)
    aesgcm     = AESGCM(key)
    plaintext  = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext.decode('utf-8'))

