# services.py
from django.template.loader import get_template
from django.conf import settings
from weasyprint import HTML
from pathlib import Path
from django.core.files.base import File
from datetime import date

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

def render_passport_pdf(passport):
    ctx = {
        "passport": passport,
        "horse": passport.horse,
        "diagram_label": _diagram_label(_age_years(getattr(passport.horse, "birth_date", None))),
        # любые доп. вычисленные поля:
        "marks": {
            "head": getattr(passport.horse, "ident_notes_head", ""),
            "left_foreleg": getattr(passport.horse, "marks_left_foreleg", ""),
            "right_foreleg": getattr(passport.horse, "marks_right_foreleg", ""),
            "left_hindleg": getattr(passport.horse, "marks_left_hindleg", ""),
            "right_hindleg": getattr(passport.horse, "marks_right_hindleg", ""),
            "extra": getattr(passport.horse, "marks_extra", ""),
        },
    }
    html = get_template("passports/pdf/base.html").render(ctx)  # один потоковый HTML
    out_dir = Path(settings.MEDIA_ROOT) / "passports"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{passport.number}.pdf"
    HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf(str(pdf_path))
    with open(pdf_path, "rb") as f:
        passport.pdf_file.save(pdf_path.name, File(f), save=False)
