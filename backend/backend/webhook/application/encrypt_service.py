import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.padding import PKCS7


class GDPRCompliantEncryptor:
    def __init__(self, password: str, salt: bytes = None):
        """
        Initializes the encryptor with a password and an optional salt.

        :param password: Password for key derivation.
        :param salt: Optional salt for key derivation. If not provided, a new salt will be generated.
        """
        self.password = password.encode()
        self.salt = salt or os.urandom(16)
        self.key = self._derive_key()

    def _derive_key(self) -> bytes:
        """Derives a cryptographic key from the password and salt using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(self.password)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypts plaintext data.

        :param plaintext: The plaintext data to encrypt.
        :return: Base64-encoded string containing the salt, IV, and ciphertext.
        """
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Pad plaintext to block size
        padder = PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(plaintext.encode()) + padder.finalize()

        # Encrypt data
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        # Combine salt, IV, and ciphertext
        encrypted_data = base64.b64encode(self.salt + iv + ciphertext).decode()
        return encrypted_data

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypts Base64-encoded encrypted data.

        :param encrypted_data: The encrypted data to decrypt.
        :return: The decrypted plaintext data.
        """
        encrypted_data_bytes = base64.b64decode(encrypted_data)

        # Extract salt, IV, and ciphertext
        salt = encrypted_data_bytes[:16]
        iv = encrypted_data_bytes[16:32]
        ciphertext = encrypted_data_bytes[32:]

        # Derive key using extracted salt
        self.salt = salt
        self.key = self._derive_key()

        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt and unpad data
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = PKCS7(algorithms.AES.block_size).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()

        return plaintext.decode()
