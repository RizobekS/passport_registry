# services.py
from django.template.loader import get_template
from django.conf import settings
from weasyprint import HTML
from pathlib import Path
from django.core.files.base import File
from datetime import date

def _fmt_region(r):
    return getattr(r, "name", "") if r else ""

def _fmt_district(d):
    # В District обычно есть name/number — берём name если есть
    return getattr(d, "name", "") if d else ""

def _owner_full_address(owner) -> str:
    """
    Owner -> Person | Organization: берём ФИО/название и адрес с регионом/районом, если заданы.
    """
    if not owner:
        return ""
    # Организация?
    org = getattr(owner, "organization", None)
    if org:
        parts = [org.name, org.address, _fmt_district(getattr(org, "district", None)), _fmt_region(getattr(org, "region", None))]
        return ", ".join([p for p in parts if p])

    # Физлицо?
    person = getattr(owner, "person", None)
    if person:
        fio = " ".join([person.last_name, person.first_name, (person.middle_name or "")]).strip()
        parts = [fio, person.address, _fmt_district(getattr(person, "district", None)), _fmt_region(getattr(person, "region", None))]
        return ", ".join([p for p in parts if p])

    return ""

def _marks_from_models(horse):
    """
    Верхняя таблица «Описание примет».
    Берём из HorseMeasurements, если есть; иначе — пусто/из horse.ident_notes в extra.
    """
    meas = getattr(horse, "meas", None)  # OneToOne: HorseMeasurements
    if meas:
        return {
            "head": meas.head,
            "left_foreleg": meas.left_foreleg,
            "right_foreleg": meas.right_foreleg,
            "left_hindleg": meas.left_hindleg,
            "right_hindleg": meas.right_hindleg,
            "extra": meas.extra_signs or horse.ident_notes,
            "stable_address": meas.address_stable or "",
        }
    # fallback
    return {
        "head": "",
        "left_foreleg": "",
        "right_foreleg": "",
        "left_hindleg": "",
        "right_hindleg": "",
        "extra": getattr(horse, "ident_notes", ""),
        "stable_address": "",
    }

def _age_years(birth_date, ref=None):
    if not birth_date:
        return None
    ref = ref or date.today()
    months = (ref.year - birth_date.year) * 12 + (ref.month - birth_date.month)
    if ref.day < birth_date.day:
        months -= 1
    return months / 12.0

def _diagram_label(age_years: float | None) -> str:
    # Диапазоны по ТЗ (десятичная запятая для подписи)
    if age_years is None:
        return "0 — 1,5"
    if age_years < 1.5:
        return "0 — 1,5"
    elif age_years < 3:
        return "1,5 — 3"
    else:
        return "3 — 7"  # по ТЗ — последний диапазон

def _vaccinations_other_first_page(passport):
    """
    Возвращает ровно page_size записей для 1-й страницы (остальное выводим пустым).
    Маппинг полей под шаблон page_vaccinations_other.html
    """
    horse = passport.horse
    qs = horse.vaccinations.select_related("vaccine", "veterinarian").order_by("date")  # модель Vaccination
    rows = []

    for rec in qs:
        vac = rec.vaccine
        vet = rec.veterinarian
        rows.append({
            "date": rec.date,
            "vaccine_name": getattr(vac, "name", "") or "",
            "reg_no": getattr(vac, "registration_number", "") or getattr(vac, "reg_no", "") or "",
            "manufactured": getattr(vac, "manufactured_date", None) or getattr(vac, "manufactured", None),
            "batch": getattr(rec, "batch_no", "") or getattr(rec, "series", "") or "",
            "mfr_address": getattr(vac, "manufacturer_address", "") or getattr(vac, "mfr_address", "") or "",
            "country": getattr(vac, "country_name", "") or getattr(vac, "country", "") or "",
            "vet_full": (getattr(vet, "full_name", None) or (str(vet) if vet else "")),
        })
    return rows

def _paginate_fixed(items, page_size: int, pages: int):
    """Разбивает items на pages страниц по page_size, дополняя None до полной страницы."""
    arr = list(items or [])
    out, i = [], 0
    for _ in range(pages):
        chunk = arr[i:i+page_size]
        i += page_size
        if len(chunk) < page_size:
            chunk += [None] * (page_size - len(chunk))
        out.append(chunk)
    return out

def render_passport_pdf(passport):
    horse = passport.horse
    marks = _marks_from_models(horse)

    ROWS_PER_PAGE = 10
    filled = _vaccinations_other_first_page(passport)[:ROWS_PER_PAGE]
    if len(filled) < ROWS_PER_PAGE:
        filled += [None] * (ROWS_PER_PAGE - len(filled))
    empty_page = [None] * ROWS_PER_PAGE
    vacc_other_pages = [filled] + [empty_page for _ in range(8)]  # 1 + 8 = 9 страниц

    ctx = {
        "passport": passport,
        "horse": horse,
        "diagram_label": _diagram_label(_age_years(getattr(horse, "birth_date", None))),
        "marks": marks,
        "owner_full_address": _owner_full_address(getattr(horse, "owner_current", None)),
        "stable_address": marks.get("stable_address") or "",
        "vacc_other_pages": vacc_other_pages,
    }
    html = get_template("passports/pdf/base.html").render(ctx)  # один потоковый HTML
    out_dir = Path(settings.MEDIA_ROOT) / "passports"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{passport.number}.pdf"
    HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf(str(pdf_path))
    with open(pdf_path, "rb") as f:
        passport.pdf_file.save(pdf_path.name, File(f), save=False)
