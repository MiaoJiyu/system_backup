"""Key management for end-to-end encryption."""
import os
import logging
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

logger = logging.getLogger(__name__)

KEY_SIZE = 32  # AES-256
NONCE_SIZE = 12  # GCM nonce
TAG_SIZE = 16  # GCM tag


class KeyManager:
    def __init__(self, key_path: str = None):
        self.key_path = key_path or "client_key.key"
        self._aes_key: bytes | None = None
        self._load_or_generate()

    def _load_or_generate(self):
        if os.path.exists(self.key_path):
            with open(self.key_path, "rb") as f:
                self._aes_key = f.read()
            if len(self._aes_key) != KEY_SIZE:
                logger.warning("Invalid key file, regenerating")
                self._generate()
        else:
            self._generate()

    def _generate(self):
        self._aes_key = get_random_bytes(KEY_SIZE)
        with open(self.key_path, "wb") as f:
            f.write(self._aes_key)
        os.chmod(self.key_path, 0o600)
        logger.info(f"Generated new encryption key: {self.key_path}")

    def get_aes_key(self) -> bytes:
        if self._aes_key is None:
            self._load_or_generate()
        return self._aes_key

    def generate_data_key(self) -> bytes:
        """Generate a random data encryption key (DEK) for file-level encryption."""
        return get_random_bytes(KEY_SIZE)

    @staticmethod
    def encrypt_dek(dek: bytes, kek: bytes) -> bytes:
        """Encrypt data key with key encryption key using AES-GCM."""
        nonce = get_random_bytes(NONCE_SIZE)
        cipher = AES.new(kek, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(dek)
        return nonce + tag + ciphertext  # 12 + 16 + 32 = 60 bytes

    @staticmethod
    def decrypt_dek(encrypted_dek: bytes, kek: bytes) -> bytes:
        """Decrypt data key with key encryption key."""
        nonce = encrypted_dek[:NONCE_SIZE]
        tag = encrypted_dek[NONCE_SIZE:NONCE_SIZE + TAG_SIZE]
        ciphertext = encrypted_dek[NONCE_SIZE + TAG_SIZE:]
        cipher = AES.new(kek, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)
