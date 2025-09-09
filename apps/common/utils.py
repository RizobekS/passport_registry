from datetime import date
from .models import NumberSequence


def make_horse_registry_no(region_code: str = "") -> str:
    """
    H-<REG>-<YYYY>-<####$$>, счётчик раздельно по (HORSE, год, REG).
    """
    year = date.today().year
    reg = (region_code or "FAL").upper() # FAL — безопасный fallback
    seq = NumberSequence.next("HORSE", year, reg)
    return f"H-{reg}-{year}-{seq:04d}"


def make_passport_number(region_code: str = "") -> str:
    """
    Генерирует номер паспорта в формате UZ-<REG>-<YYYY>-<######>.
    region_code — трёхбуквенный код региона (FAR, NMG, TSV, ...).
    Счётчик ведём отдельно по scope='PASSPORT', году и region_code.
    """
    year = date.today().year
    reg = (region_code or "FAL").upper()
    seq = NumberSequence.next("PASSPORT", year, reg)
    return f"UZ-{reg}-{year}-{seq:04d}"
