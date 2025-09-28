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

def _vaccinations_other_first_page(passport):
    """
    Ровно page_size записей для 1-й страницы «Прочие вакцинации».
    Под ваши модели:
      Vaccination: date, registration_number, vaccine(FK), veterinarian(FK)
      Vaccine: name, manufacture_date, batch_number, manufacturer_address
    """
    horse = passport.horse
    qs = horse.vaccinations.select_related("vaccine", "veterinarian").order_by("date")
    rows = []
    for rec in qs:
        vac = rec.vaccine
        vet = rec.veterinarian
        rows.append({
            "date": rec.date,
            "vaccine_name": getattr(vac, "name", "") or "",
            "reg_no": rec.registration_number or "",                           # ← из Vaccination
            "manufactured": getattr(vac, "manufacture_date", None),            # ← из Vaccine
            "batch": getattr(vac, "batch_number", "") or "",                   # ← из Vaccine
            "mfr_address": getattr(vac, "manufacturer_address", "") or "",     # ← из Vaccine
            "country": "",                                                     # в моделях нет страны
            "vet_full": (getattr(vet, "full_name", None) or (str(vet) if vet else "")),
        })
    return rows

def _lab_tests_first_page(passport):
    """
    Возвращает список записей для страницы 'Лабораторные исследования'
    в формате, который ждёт шаблон:
      { date, test_type, disease, result, lab, vet_full }
    """
    horse = passport.horse
    qs = getattr(horse, "lab_tests", None)
    if not hasattr(qs, "select_related"):
        return []

    # дата по возрастанию (можно поменять на '-date' если нужно сверху новые)
    qs = qs.select_related("test_type", "veterinarian").order_by("date")

    rows = []
    for rec in qs:
        # Наименование и адрес лаборатории -> одна строка
        if rec.address_lab:
            lab = rec.address_lab
        else:
            lab = ""

        # Тип теста из справочника (если нет .name — упадём на __str__)
        if rec.test_type:
            test_type = getattr(rec.test_type, "name", None) or str(rec.test_type)
        else:
            test_type = ""

        # ФИО ветеринара (поддержим разные варианты поля/строковое представление)
        vet = rec.veterinarian
        vet_full = (
            getattr(vet, "full_name", None)
            or getattr(vet, "fio", None)
            or getattr(vet, "name", None)
            or (str(vet) if vet else "")
        )

        rows.append({
            "date": rec.date,
            "test_type": test_type,
            "disease": rec.name_of_disease or "",
            "result": rec.result or "",
            "lab": lab,
            "vet_full": vet_full,
        })

    return rows

def _sample_flags(sample_str: str | None):
    s = (sample_str or "").lower()
    return {
        "urine": "urine" in s or "сиёдик" in s or "моча" in s or "моча" in s,
        "blood": "blood" in s or "қон" in s or "кров" in s,
        "other_text": "" if any(k in s for k in ("urine","blood","сиёдик","моч","blood","қон","кров")) else (sample_str or ""),
    }

def _diag_controls_first_page(passport):
    """
    Таблица «Диагностические/допинг-исследования».
    Модели сейчас: DiagnosticCheck (related_name='diagnostics')
      поля: date, place_event, urine, blood, others, veterinarian
    В шаблон отдаём:
      {date, place, urine(bool), blood(bool), other(text), vet_full}
    """
    horse = passport.horse
    qs = getattr(horse, "diagnostics", None)
    if hasattr(qs, "select_related"):
        qs = qs.select_related("veterinarian").order_by("date")
    else:
        return []

    rows = []
    for rec in qs:
        vet = getattr(rec, "veterinarian", None)
        rows.append({
            "date": getattr(rec, "date", None),
            "place": getattr(rec, "place_event", "") or "",
            "urine": bool(getattr(rec, "urine", None)),     # чекбоксы — True/False
            "blood": bool(getattr(rec, "blood", None)),
            "other": getattr(rec, "others", "") or "",
            "vet_full": (getattr(vet, "full_name", None) or (str(vet) if vet else "")),
        })
    return rows

def _achievements_first_page(passport):
    """
    Возвращает список словарей: {'year','place','info'} для первой страницы.
    Пытаемся быть совместимыми с разными названиями полей/related_name.
    Ожидаемые варианты моделей:
      - horse.achievements / horse.sport_results / horse.results
      - поля: date/year, place/location/venue, discipline, category, rank, result, points, title и т.п.
    """
    horse = passport.horse
    # найдём qs по возможным related_name
    qs = None
    for attr in ("achievements", "sport_results", "results"):
        qs = getattr(horse, attr, None)
        if qs is not None:
            break
    if not hasattr(qs, "all"):
        return []

    # сортировка по дате/году
    if hasattr(qs, "order_by"):
        # если у модели есть 'date' — отсортируем по ней, иначе по 'year'
        try:
            qs = qs.order_by("-date")
        except Exception:
            try:
                qs = qs.order_by("-year")
            except Exception:
                pass

    rows = []
    for rec in qs:
        # year
        year = getattr(rec, "year", None)
        if not year:
            d = getattr(rec, "date", None)
            year = d.year if d else ""
        # place
        place = (
            getattr(rec, "place", None)
            or getattr(rec, "location", None)
            or getattr(rec, "venue", None)
            or ""
        )
        # info: собираем всё полезное в одну строку
        bits = [
            getattr(rec, "info", None) or "",
            getattr(rec, "competition", None) or getattr(rec, "event", None) or "",
            getattr(rec, "discipline", None) or "",
            getattr(rec, "category", None) or "",
            getattr(rec, "result", None) or "",
            getattr(rec, "rank", None) or getattr(rec, "position", None) or "",
            getattr(rec, "points", None) or "",
            getattr(rec, "title", None) or "",
        ]
        info = ", ".join([str(b) for b in bits if b])
        rows.append({"year": year, "place": place, "info": info})
    return rows

def _exhibitions_first_page(passport):
    """
    Берём участия в выставках: ExhibitionEntry(horse, year, place, info)
    Возвращаем список словарей {year, place, info} для первой страницы.
    """
    horse = passport.horse
    qs = getattr(horse, "exhibitions", None)
    if not hasattr(qs, "all"):
        return []

    qs = qs.order_by("-year", "place")  # свежие сверху
    rows = [{"year": e.year, "place": e.place or "", "info": e.info or ""} for e in qs]
    return rows

# -------------------- Offspring helpers --------------------

def _offspring_rows_for_passport(passport):
    """
    Готовит строки для таблицы 'Приплод' под макет:
      {sire_name, dam_name, sire_breed, dam_breed, colour, sex, brand, birth_year}
      - если relation == SIRE -> отец = текущая лошадь, мать пусто
      - если relation == DAM  -> мать  = текущая лошадь, отец пусто
      - если OTHER           -> оба родителя пусто (данных нет)
    """
    horse = passport.horse
    qs = horse.offspring.all().order_by('-id')

    sire_self_name  = horse.name
    dam_self_name   = horse.name
    sire_self_breed = getattr(horse.breed, "name", "") or str(horse.breed)

    rows = []
    for o in qs:

        birth_year = o.date_birth.year if o.date_birth else ""
        rows.append({
            "colour":     o.colour_horse or "",
            "sex":        o.sex or "",
            "brand":      o.brand_no or "",
            "birth_year": birth_year,
        })
    return rows

def _ownership_rows_for_passport(passport):
    """
    Возвращает список словарей для страницы 'Change of ownership':
      {date, owner}
    date  -> Ownership.start_date (дата продажи/перехода права к новому владельцу)
    owner -> ФИО/название + адрес (читаем через _owner_full_address)
    """
    horse = passport.horse
    qs = horse.ownerships.select_related("owner").order_by("start_date")
    rows = []
    for rec in qs:
        rows.append({
            "date": rec.start_date,
            "owner": _owner_full_address(rec.owner),
        })
    return rows

def _parentage_ctx(passport):
    """Данные для страницы 'Насл-насаби / Родословная / Parentage' под текущие модели."""
    h = passport.horse
    place = getattr(h.place_of_birth, "name", "") if getattr(h, "place_of_birth", None) else ""
    sex_display = h.get_sex_display() if hasattr(h, "get_sex_display") else (h.sex or "")

    # В ваших моделях Offspring — список; возьмём первую запись, если есть
    o = None
    try:
        o = h.offspring.first()
    except Exception:
        o = None

    return {
        "place_of_birth": place,
        "name": h.name,
        "brand": getattr(o, "brand_no", "") if o else "",
        "colour": getattr(h.color, "name", "") or (str(h.color) if getattr(h, "color", None) else ""),
        "breed": getattr(h.breed, "name", "") or (str(h.breed) if getattr(h, "breed", None) else ""),
        "birth_date": getattr(h, "birth_date", None),
        "sex": sex_display,
        "dna_no": getattr(o, "shb_no", "") if o else "",                           # ДНК № / SHB №
        "reg_no": passport.number or h.registry_no or "",                          # Рег. номер
        "immunity_no": getattr(o, "immunity_exp_number", "") if o else "",
        "immunity_date": getattr(o, "immunity_exp_date", None) if o else None,
    }

def _chip_rows_for_passport(passport, rows_per_page=5):
    """
    Таблица 'Chip identification number' (1 страница).
    Берём события идентификации (IdentificationEvent) этой лошади.
    Если записей нет — подставим хотя бы текущий microchip лошади.
    Возвращает список длиной rows_per_page из словарей либо None.
    """
    horse = passport.horse
    qs = getattr(horse, "ident_events", None)
    rows = []

    if hasattr(qs, "order_by"):
        qs = qs.order_by("date")
        for ev in qs:
            rows.append({
                "date": ev.date,
                "code": ev.microchip or "",
            })

    # fallback: хотя бы одна строка из текущего microchip
    if not rows and getattr(horse, "microchip", None):
        rows.append({
            "date": getattr(passport, "issue_date", None),  # если есть; иначе пусто
            "code": horse.microchip,
        })

    # обрезаем/добиваем до фиксированного размера
    rows = rows[:rows_per_page]
    if len(rows) < rows_per_page:
        rows += [None] * (rows_per_page - len(rows))

    return rows

def render_passport_pdf(passport):
    horse = passport.horse
    marks = _marks_from_models(horse)
    ctx_parentage = _parentage_ctx(passport)

    ROWS_PER_PAGE = 6
    filled = _vaccinations_other_first_page(passport)[:ROWS_PER_PAGE]
    if len(filled) < ROWS_PER_PAGE:
        filled += [None] * (ROWS_PER_PAGE - len(filled))
    empty_page = [None] * ROWS_PER_PAGE
    vacc_other_pages = [filled] + [empty_page for _ in range(11)]  # 1 + 11 = 12 страниц

    LAB_ROWS_PER_PAGE = 7
    filled_labs = _lab_tests_first_page(passport)[:LAB_ROWS_PER_PAGE]
    if len(filled_labs) < LAB_ROWS_PER_PAGE:
        filled_labs += [None] * (LAB_ROWS_PER_PAGE - len(filled_labs))
    empty_lab_page = [None] * LAB_ROWS_PER_PAGE
    lab_pages = [filled_labs] + [empty_lab_page for _ in range(9)]  # 1 + 9 = 10

    DIAG_ROWS_PER_PAGE = 8
    filled_diag = _diag_controls_first_page(passport)[:DIAG_ROWS_PER_PAGE]
    if len(filled_diag) < DIAG_ROWS_PER_PAGE:
        filled_diag += [None] * (DIAG_ROWS_PER_PAGE - len(filled_diag))
    empty_diag_page = [None] * DIAG_ROWS_PER_PAGE
    diag_pages = [filled_diag] + [empty_diag_page for _ in range(4)]  # 1 + 4 = 5

    ACH_ROWS_PER_PAGE = 8  # строк на лист (при необходимости подгони)
    ach_filled = _achievements_first_page(passport)[:ACH_ROWS_PER_PAGE]
    if len(ach_filled) < ACH_ROWS_PER_PAGE:
        ach_filled += [None] * (ACH_ROWS_PER_PAGE - len(ach_filled))
    ach_empty_page = [None] * ACH_ROWS_PER_PAGE
    ach_pages = [ach_filled, ach_empty_page]  # 1 из БД + 1 пустая

    EXH_ROWS_PER_PAGE = 8  # сколько строк помещается на лист
    exh_filled = _exhibitions_first_page(passport)[:EXH_ROWS_PER_PAGE]
    if len(exh_filled) < EXH_ROWS_PER_PAGE:
        exh_filled += [None] * (EXH_ROWS_PER_PAGE - len(exh_filled))
    exh_empty_page = [None] * EXH_ROWS_PER_PAGE
    exh_pages = [exh_filled, exh_empty_page]

    OFFSPRING_ROWS_PER_PAGE = 7  # под макет;
    offspring_rows = _offspring_rows_for_passport(passport)[:OFFSPRING_ROWS_PER_PAGE]
    if len(offspring_rows) < OFFSPRING_ROWS_PER_PAGE:
        offspring_rows += [None] * (OFFSPRING_ROWS_PER_PAGE - len(offspring_rows))

    OWN_ROWS_PER_PAGE = 6
    ownership_rows = _ownership_rows_for_passport(passport)[:OWN_ROWS_PER_PAGE]
    if len(ownership_rows) < OWN_ROWS_PER_PAGE:
        ownership_rows += [None] * (OWN_ROWS_PER_PAGE - len(ownership_rows))

    # ---- Chip page (1 страница) ----
    CHIP_ROWS_PER_PAGE = 3
    chip_rows = _chip_rows_for_passport(passport, CHIP_ROWS_PER_PAGE)

    # Баркод: используем тот же, что на обложке (для microchip).
    chip_barcode_image = getattr(passport, "barcode_image", None)
    chip_main_code = getattr(horse, "microchip", "")

    # Дата выдачи паспорта (если поле есть). Иначе оставим пусто (линия для ручной записи).
    issue_date = getattr(passport, "issue_date", None)



    ctx = {
        "passport": passport,
        "horse": horse,
        "diagram_label": _diagram_label(_age_years(getattr(horse, "birth_date", None))),
        "marks": marks,
        "owner_full_address": _owner_full_address(getattr(horse, "owner_current", None)),
        "stable_address": marks.get("stable_address") or "",
        "vacc_other_pages": vacc_other_pages,
        "lab_pages": lab_pages,
        "diag_pages": diag_pages,
        "ach_pages": ach_pages,
        "exh_pages": exh_pages,
        "offspring_rows": offspring_rows,
        "ownership_rows": ownership_rows,
        "parentage": ctx_parentage,
        "chip_rows": chip_rows,
        "chip_barcode_image": chip_barcode_image,
        "chip_main_code": chip_main_code,
        "passport_issue_date": issue_date,
    }
    html = get_template("passports/pdf/base.html").render(ctx)  # один потоковый HTML
    out_dir = Path(settings.MEDIA_ROOT) / "passports"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{passport.number}.pdf"
    HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf(str(pdf_path))
    with open(pdf_path, "rb") as f:
        passport.pdf_file.save(pdf_path.name, File(f), save=False)
