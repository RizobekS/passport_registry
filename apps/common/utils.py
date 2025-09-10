from datetime import date
from .models import NumberSequence


def make_horse_registry_no(region_code: str = "") -> str:
    """
    H-<REG>-<YYYY>-<####$$>, счётчик раздельно по (HORSE, год, REG).
    """
    year = date.today().year
    reg = (region_code or "FAL").upper() # FAL — безопасный fallback
    seq = NumberSequence.next("HORSE", year, reg)
    return f"H-{reg}-{seq:06d}"


def make_passport_number(region_code: str, district_number: int | None = None) -> str:
    """
    Возвращает номер паспорта: UZ-<REG>-<RR><NNNN>.
    Счётчик ведём раздельно по (scope='PASSPORT', RR, REG), где:
      - REG: код региона (например, JIZ),
      - RR: номер района (01..99).
    Для совместимости district_number может быть None — тогда RR=0.
    """
    reg = (region_code or "FAL").upper()
    rr = int(district_number) if district_number is not None else 0
    # NumberSequence: year=RR, region_name=REG
    seq = NumberSequence.next("PASSPORT", rr, reg)
    return f"UZ-{reg}-{rr:02d}{seq:04d}"
