from aiogram import Router
from .start import router as start_router
from .add_password import router as add_password_router
from .replace_password import router as replace_password_router
from .delete_password import router as delete_password_router
from .view_passwords import router as view_passwords_router
from .common import router as common_router
from .master_password import router as master_password_router
from ..auth_middleware import AuthMiddleware

router = Router()

# Подключаем middleware для проверки аутентификации
router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

router.include_router(start_router)
router.include_router(master_password_router)
router.include_router(add_password_router)
router.include_router(replace_password_router)
router.include_router(delete_password_router)
router.include_router(view_passwords_router)
router.include_router(common_router)
