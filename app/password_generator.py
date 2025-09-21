import random
import string
import secrets
import html


def generate_yandex_like_password(length=12):
    """
    Генерирует пароль похожий на те, что предлагает Яндекс.Менеджер паролей.
    Состоит из букв (верхний и нижний регистр), цифр и специальных символов.
    """
    # Наборы символов
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?'

    # Минимальное количество каждого типа символов
    min_lowercase = 2
    min_uppercase = 2
    min_digits = 2
    min_symbols = 2

    # Генерируем обязательные символы
    password = [
        *[secrets.choice(lowercase) for _ in range(min_lowercase)],
        *[secrets.choice(uppercase) for _ in range(min_uppercase)],
        *[secrets.choice(digits) for _ in range(min_digits)],
        *[secrets.choice(symbols) for _ in range(min_symbols)],
    ]

    # Заполняем оставшуюся длину случайными символами из всех наборов
    all_characters = lowercase + uppercase + digits + symbols
    remaining_length = length - len(password)

    if remaining_length > 0:
        password.extend([secrets.choice(all_characters)
                        for _ in range(remaining_length)])

    # Перемешиваем список, чтобы порядок был случайным
    random.shuffle(password)

    return ''.join(password)


def generate_readable_password(length=10):
    """
    Генерирует более читаемый пароль, используя чередование согласных и гласных.
    """
    consonants = 'bcdfghjklmnpqrstvwxz'
    vowels = 'aeiouy'
    digits = string.digits
    symbols = '!@#$%^&*'

    password = []

    # Начинаем с согласной для лучшей читаемости
    for i in range(length):
        if i % 3 == 0:  # Каждый третий символ - цифра или специальный символ
            if i % 6 == 0:
                password.append(secrets.choice(symbols))
            else:
                password.append(secrets.choice(digits))
        elif i % 2 == 0:
            password.append(secrets.choice(consonants).upper() if i %
                            4 == 0 else secrets.choice(consonants))
        else:
            password.append(secrets.choice(vowels))

    return ''.join(password)


def safe_display_password(password):
    """
    Безопасно отображает пароль в Telegram, избегая проблем с HTML-разметкой.
    """
    # Экранируем HTML-символы
    escaped = html.escape(password)

    # Заменяем потенциально проблемные последовательности
    # Например, "&p" может интерпретироваться как начало HTML-entity
    safe_password = escaped.replace('&', '&amp;')

    return f"<code>{safe_password}</code>"
