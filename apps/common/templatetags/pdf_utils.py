from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from urllib.parse import urljoin
from pathlib import Path
import os

register = template.Library()

def _to_file_uri(abs_path: str) -> str:
    # Надёжно и кроссплатформенно: file:///D:/... на Windows, file:///... на *nix
    return Path(abs_path).resolve(strict=False).as_uri()

@register.simple_tag
def static_file(path: str) -> str:
    """
    Вернуть file:// к статическому файлу.
    Работает и в dev (через staticfiles finders), и в prod (через STATIC_ROOT).
    """
    found = finders.find(path)
    if isinstance(found, (list, tuple)) and found:
        found = found[0]
    if found and os.path.exists(found):
        return _to_file_uri(found)

    static_root = getattr(settings, "STATIC_ROOT", "")
    if static_root:
        candidate = os.path.join(static_root, path.lstrip("/"))
        if os.path.exists(candidate):
            return _to_file_uri(candidate)

    # Крайний случай: вернём URL — с base_url+url_fetcher тоже может работать
    static_url = getattr(settings, "STATIC_URL", "/static/")
    return urljoin(static_url, path.lstrip("/"))

@register.simple_tag
def media_file(path: str) -> str:
    """
    file:// к файлу из MEDIA_ROOT по относительному пути
    """
    media_root = getattr(settings, "MEDIA_ROOT", "")
    candidate = os.path.join(media_root, path.lstrip("/"))
    if os.path.exists(candidate):
        return _to_file_uri(candidate)
    media_url = getattr(settings, "MEDIA_URL", "/media/")
    return urljoin(media_url, path.lstrip("/"))

@register.filter
def fileuri(field):
    """
    Превратить ImageField/FileField в правильный file:// URI (или http/https).
    """
    if not field:
        return ""
    path = getattr(field, "path", None)
    if path and os.path.exists(path):
        return _to_file_uri(path)

    url = getattr(field, "url", "") or ""
    if url.startswith(("http://", "https://", "file://")):
        return url

    media_url = getattr(settings, "MEDIA_URL", "/media/")
    media_root = getattr(settings, "MEDIA_ROOT", "")
    if media_root and url.startswith(media_url):
        rel = url[len(media_url):].lstrip("/")
        candidate = os.path.join(media_root, rel)
        if os.path.exists(candidate):
            return _to_file_uri(candidate)

    return url  # fallback

@register.filter
def dmy(value):
    from datetime import date, datetime
    return value.strftime("%d.%m.%Y") if isinstance(value, (date, datetime)) else ""

@register.filter
def dash(value):
    return value if (value is not None and f"{value}".strip()) else "—"

# Опционально: data-uri на случай жёсткой песочницы
@register.filter
def data_uri(field):
    try:
        path = field.path
        mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
        with open(path, "rb") as f:
            import base64
            return f"data:{mime};base64,{base64.b64encode(f.read()).decode('ascii')}"
    except Exception:
        return ""
