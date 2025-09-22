import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidTag


class AESCipher:
    def __init__(self):
        # Соль должна быть постоянной для одного приложения
        self.salt = b'password_manager_salt_16bytes'

    def _derive_key(self, tg_id: int) -> bytes:
        """Создает ключ из Telegram ID пользователя"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # AES-256 требует 32 байта
            salt=self.salt,
            iterations=100000,
        )
        return kdf.derive(str(tg_id).encode())

    def encrypt(self, plaintext: str, tg_id: int) -> str:
        """Шифрует текст и возвращает base64 строку"""
        if plaintext is None:
            return None

        key = self._derive_key(tg_id)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # 12 bytes для GCM

        # Шифруем данные
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

        # Объединяем nonce и ciphertext в одну строку
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode()

    def decrypt(self, ciphertext_b64: str, tg_id: int) -> str:
        """Расшифровывает base64 строку в исходный текст"""
        if not ciphertext_b64:
            return None

        try:
            key = self._derive_key(tg_id)
            aesgcm = AESGCM(key)
            combined = base64.b64decode(ciphertext_b64)

            # Разделяем nonce и ciphertext
            nonce = combined[:12]
            ciphertext = combined[12:]

            # Расшифровываем
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode()
        except (InvalidTag, Exception):
            # Если расшифровка не удалась, возвращаем исходную строку
            # для совместимости с уже существующими незашифрованными данными
            return ciphertext_b64


# Глобальный экземпляр для использования во всем приложении
cipher = AESCipher()
