from django.template.loader import get_template
from django.conf import settings
from weasyprint import HTML
from pathlib import Path
from django.core.files.base import File


def render_passport_pdf(passport):

    ctx = {
        "passport": passport,
        "horse": passport.horse,
        "marks": {
            "head": passport.horse.ident_notes_head if hasattr(passport.horse, "ident_notes_head") else "",
            "left_foreleg": getattr(passport.horse, "marks_left_foreleg", ""),
            "right_foreleg": getattr(passport.horse, "marks_right_foreleg", ""),
            "left_hindleg": getattr(passport.horse, "marks_left_hindleg", ""),
            "right_hindleg": getattr(passport.horse, "marks_right_hindleg", ""),
            "extra": getattr(passport.horse, "marks_extra", ""),
        }
    }

    # Собираем несколько страниц в один HTML (проще и быстрее)
    pages = []
    for tpl_name in [
        "passports/pdf/page1.html",   # если нужна
        "passports/pdf/page2.html",
        "passports/pdf/page3.html",
        "passports/pdf/page5.html",
        "passports/pdf/page6.html",
        "passports/pdf/page7.html",
        "passports/pdf/page8.html",
        "passports/pdf/page9.html",
        "passports/pdf/page10.html",
        "passports/pdf/page11.html",
        "passports/pdf/page12.html",
        "passports/pdf/page14.html",
        "passports/pdf/page15.html",
        "passports/pdf/page16.html",
        "passports/pdf/page17.html",
        "passports/pdf/page18.html",
    ]:
        tpl = get_template(tpl_name)
        pages.append(tpl.render(ctx))

    html_string = "\n<div class='page-break'></div>\n".join(pages)

    out_dir = Path(settings.MEDIA_ROOT) / "passports"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{passport.number}.pdf"

    HTML(string=html_string, base_url=str(settings.BASE_DIR)).write_pdf(str(pdf_path))

    with open(pdf_path, "rb") as f:
        passport.pdf_file.save(pdf_path.name, File(f), save=False)
