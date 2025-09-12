# services.py
from django.template.loader import get_template
from django.conf import settings
from weasyprint import HTML
from pathlib import Path
from django.core.files.base import File

def render_passport_pdf(passport):
    ctx = {
        "passport": passport,
        "horse": passport.horse,
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
