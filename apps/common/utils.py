from datetime import date
from .models import NumberSequence


def make_horse_registry_no(region_name: str = "") -> str:
    y = date.today().year
    seq = NumberSequence.next("HORSE", y, region_name or "")
    return f"H-{y}-{seq:06d}"


def make_passport_number(region_code: str = "") -> str:
    """
    Генерирует номер паспорта в формате UZ-<REG>-<YYYY>-<######>.
    region_code — трёхбуквенный код региона (FAR, NMG, TSV, ...).
    Счётчик ведём отдельно по scope='PASSPORT', году и region_code.
    """
    year = date.today().year
    reg = (region_code or "FAL").upper()  # FAL — безопасный fallback
    seq = NumberSequence.next("PASSPORT", year, reg)  # ВАЖНО: позиционные аргументы!
    return f"UZ-{reg}-{year}-{seq:06d}"
