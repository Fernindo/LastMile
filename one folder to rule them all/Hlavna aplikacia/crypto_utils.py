# crypto_utils.py
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode, urlsafe_b64decode

def derive_key(password: str, salt: bytes) -> bytes:
    # PBKDF2 to derive a 32-byte key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    return urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_bytes(data: bytes, password: str) -> bytes:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    f = Fernet(key)
    token = f.encrypt(data)
    # store salt || token
    return salt + token

def decrypt_bytes(blob: bytes, password: str) -> bytes:
    salt, token = blob[:16], blob[16:]
    key = derive_key(password, salt)
    f = Fernet(key)
    return f.decrypt(token)
