from typing import Dict, Optional
import time


class AuthManager:
    def __init__(self):
        # Словарь для хранения аутентифицированных пользователей: {tg_id: (master_password, timestamp)}
        self._authenticated_users: Dict[int, tuple[str, float]] = {}
        # Время жизни сессии в секундах (до перезапуска бота)
        self.session_timeout = float('inf')  # Бессрочно до перезапуска

    def authenticate_user(self, tg_id: int, master_password: str) -> None:
        """Аутентифицирует пользователя и сохраняет мастер-пароль в сессии"""
        self._authenticated_users[tg_id] = (master_password, time.time())

    def is_authenticated(self, tg_id: int) -> bool:
        """Проверяет, аутентифицирован ли пользователь"""
        if tg_id not in self._authenticated_users:
            return False

        # Проверяем, не истекла ли сессия (в данной реализации - никогда)
        _, auth_time = self._authenticated_users[tg_id]
        if time.time() - auth_time > self.session_timeout:
            self.logout_user(tg_id)
            return False

        return True

    def get_master_password(self, tg_id: int) -> Optional[str]:
        """Получает мастер-пароль из сессии"""
        if not self.is_authenticated(tg_id):
            return None

        master_password, _ = self._authenticated_users[tg_id]
        return master_password

    def logout_user(self, tg_id: int) -> None:
        """Выходит из системы (удаляет сессию)"""
        if tg_id in self._authenticated_users:
            del self._authenticated_users[tg_id]

    def clear_all_sessions(self) -> None:
        """Очищает все сессии (при перезапуске бота)"""
        self._authenticated_users.clear()

    def get_active_sessions_count(self) -> int:
        """Возвращает количество активных сессий"""
        return len(self._authenticated_users)


# Глобальный экземпляр менеджера аутентификации
auth_manager = AuthManager()
