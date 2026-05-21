"""File-level AES-256-GCM encryption with data key wrapping."""
import os
import logging
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from client.src.crypto.key_manager import KeyManager, KEY_SIZE, NONCE_SIZE, TAG_SIZE

logger = logging.getLogger(__name__)

# File header magic + version
HEADER_MAGIC = b"SBKP2\x00"  # SmartBackup Key Package v2
HEADER_SIZE = len(HEADER_MAGIC) + 1 + NONCE_SIZE + TAG_SIZE + KEY_SIZE  # ~71 bytes


class FileEncryptor:
    def __init__(self, key_manager: KeyManager):
        self.km = key_manager

    def encrypt_file(self, source_path: str, dest_path: str, chunk_size: int = 100 * 1024 * 1024) -> tuple[int, str]:
        """Encrypt a file and return (encrypted_size, md5_of_original)."""
        import hashlib
        kek = self.km.get_aes_key()
        dek = self.km.generate_data_key()
        encrypted_dek = KeyManager.encrypt_dek(dek, kek)

        original_md5 = hashlib.md5()

        with open(source_path, "rb") as src, open(dest_path, "wb") as dst:
            # Write header: magic + version + encrypted DEK
            dst.write(HEADER_MAGIC)
            dst.write(b"\x01")  # version 1
            dst.write(encrypted_dek)

            encrypted_size = len(HEADER_MAGIC) + 1 + len(encrypted_dek)

            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                original_md5.update(chunk)

                nonce = get_random_bytes(NONCE_SIZE)
                cipher = AES.new(dek, AES.MODE_GCM, nonce=nonce)
                ciphertext, tag = cipher.encrypt_and_digest(chunk)

                dst.write(nonce)
                dst.write(tag)
                dst.write(ciphertext)
                encrypted_size += NONCE_SIZE + TAG_SIZE + len(ciphertext)

        return encrypted_size, original_md5.hexdigest()

    def decrypt_file(self, source_path: str, dest_path: str, chunk_size: int = 100 * 1024 * 1024) -> int:
        """Decrypt a file and return original size."""
        kek = self.km.get_aes_key()

        with open(source_path, "rb") as src, open(dest_path, "wb") as dst:
            magic = src.read(len(HEADER_MAGIC))
            if magic != HEADER_MAGIC:
                raise ValueError("Invalid encrypted file header")

            version = src.read(1)
            encrypted_dek = src.read(NONCE_SIZE + TAG_SIZE + KEY_SIZE)
            dek = KeyManager.decrypt_dek(encrypted_dek, kek)

            original_size = 0
            chunk_header_size = NONCE_SIZE + TAG_SIZE

            while True:
                header = src.read(chunk_header_size)
                if len(header) < chunk_header_size:
                    break
                nonce = header[:NONCE_SIZE]
                tag = header[NONCE_SIZE:chunk_header_size]

                ciphertext = src.read(chunk_size + TAG_SIZE)
                if not ciphertext:
                    break

                cipher = AES.new(dek, AES.MODE_GCM, nonce=nonce)
                plaintext = cipher.decrypt_and_verify(ciphertext, tag)
                dst.write(plaintext)
                original_size += len(plaintext)

        return original_size
