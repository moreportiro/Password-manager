"""
app/xml_manager.py
Модуль для выгрузки и загрузки паролей в формате XML.

ВАЖНО: XML хранит данные в открытом виде (расшифрованные login/password),
поэтому файл нужно хранить в безопасном месте.
Шифрование/дешифрование выполняется через app.crypto.cipher,
как и в остальных частях проекта.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime


# ─── Экспорт ──────────────────────────────────────────────────────────────────

def export_passwords_to_xml(passwords: list[dict]) -> bytes:
    """
    Генерирует XML-файл из списка записей паролей.

    passwords — список словарей с ключами:
        id (int), site (str), login (str), password (str)
        Данные уже расшифрованы (как они отображаются пользователю).

    Возвращает bytes — содержимое XML-файла.
    """
    root = ET.Element("passwords")
    root.set("exported_at", datetime.utcnow().isoformat(timespec="seconds") + "Z")
    root.set("version", "1")
    root.set("count", str(len(passwords)))

    for entry in passwords:
        item = ET.SubElement(root, "entry")
        item.set("id", str(entry["id"]))
        ET.SubElement(item, "site").text = str(entry["site"])
        ET.SubElement(item, "login").text = str(entry["login"])
        ET.SubElement(item, "password").text = str(entry["password"])

    raw_xml = ET.tostring(root, encoding="unicode")
    pretty = minidom.parseString(raw_xml).toprettyxml(indent="  ", encoding="utf-8")
    return pretty


# ─── Импорт ───────────────────────────────────────────────────────────────────

class XMLImportError(Exception):
    """Ошибка при разборе XML-файла паролей."""


def import_passwords_from_xml(xml_bytes: bytes) -> list[dict]:
    """
    Разбирает XML-файл и возвращает список записей.

    Каждая запись — словарь:
        site (str), login (str), password (str)

    Поднимает XMLImportError при проблемах с форматом.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        raise XMLImportError(f"Невалидный XML: {e}")

    if root.tag != "passwords":
        raise XMLImportError("Неверный формат файла: ожидался корневой тег <passwords>")

    entries = []
    for i, item in enumerate(root.findall("entry"), start=1):
        site_el = item.find("site")
        login_el = item.find("login")
        password_el = item.find("password")

        if site_el is None or login_el is None or password_el is None:
            raise XMLImportError(
                f"Запись #{i}: отсутствует один из обязательных тегов <site>, <login>, <password>"
            )

        site = (site_el.text or "").strip()
        login = (login_el.text or "").strip()
        password = (password_el.text or "").strip()

        if not site:
            raise XMLImportError(f"Запись #{i}: пустое поле <site>")
        if not login:
            raise XMLImportError(f"Запись #{i} ({site}): пустое поле <login>")
        if not password:
            raise XMLImportError(f"Запись #{i} ({site}): пустое поле <password>")

        entries.append({
            "site": site,
            "login": login,
            "password": password,
        })

    return entries
