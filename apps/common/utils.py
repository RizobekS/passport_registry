from datetime import date
from .models import NumberSequence


def make_horse_registry_no(region_name: str = "") -> str:
    y = date.today().year
    seq = NumberSequence.next("HORSE", y, region_name or "")
    return f"H-{y}-{seq:06d}"


def make_passport_number(region_name: str = "") -> str:
    y = date.today().year
    seq = NumberSequence.next("PASSPORT", y, region_name or "")
    return f"P-{y}-{seq:06d}"
