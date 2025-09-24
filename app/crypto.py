import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidTag


class AESCipher:
    def __init__(self):
        self.salt = b'password_manager_salt_16bytes'
        self.master_salt = b'master_password_salt_32_bytes_here'

    def _derive_key(self, tg_id: int, master_password: str = None) -> bytes:
        """
        Создает ключ из Telegram ID пользователя и мастер-пароля
        Если мастер-пароль не указан, использует только tg_id для обратной совместимости
        """
        if master_password:
            # комбинирует tg_id и мастер-пароль для создания более стойкого ключа
            combined_input = f"{tg_id}:{master_password}".encode()
        else:
            # для обратной совместимости с существующими данными
            combined_input = str(tg_id).encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        return kdf.derive(combined_input)

    def hash_master_password(self, master_password: str) -> str:
        """Создает хеш мастер-пароля для хранения в БД"""
        # использует отдельную соль для хеширования мастер-паролей
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.master_salt,
            iterations=200000,  # больше итераций для мастер-пароля
        )
        hash_bytes = kdf.derive(master_password.encode())
        return base64.b64encode(hash_bytes).decode()

    def verify_master_password(self, master_password: str, stored_hash: str) -> bool:
        """Проверяет мастер-пароль против сохраненного хеша"""
        try:
            computed_hash = self.hash_master_password(master_password)
            return computed_hash == stored_hash
        except Exception:
            return False

    def encrypt(self, plaintext: str, tg_id: int, master_password: str = None) -> str:
        """Шифрует текст и возвращает base64 строку"""
        if plaintext is None:
            return None

        key = self._derive_key(tg_id, master_password)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # 12 bytes для GCM

        # Шифруем данные
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

        # Объединяем nonce и ciphertext в одну строку
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode()

    def decrypt(self, ciphertext_b64: str, tg_id: int, master_password: str = None) -> str:
        """Расшифровывает base64 строку в исходный текст"""
        if not ciphertext_b64:
            return None

        try:
            key = self._derive_key(tg_id, master_password)
            aesgcm = AESGCM(key)
            combined = base64.b64decode(ciphertext_b64)

            # Разделяем nonce и ciphertext
            nonce = combined[:12]
            ciphertext = combined[12:]

            # Расшифровываем
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode()
        except (InvalidTag, Exception):
            # Если расшифровка с мастер-паролем не удалась,
            # пробуем без мастер-пароля (для обратной совместимости)
            if master_password:
                try:
                    return self.decrypt(ciphertext_b64, tg_id, None)
                except:
                    return ciphertext_b64


# Глобальный экземпляр для использования во всем приложении
cipher = AESCipher()
