import io, uuid
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import barcode, qrcode
from barcode.writer import ImageWriter

from apps.common.utils import make_passport_number
from apps.horses.models import Horse


class Passport(models.Model):
    class Status(models.TextChoices):
        DRAFT='DRAFT','Черновик'
        ISSUED='ISSUED','Выдан'
        REISSUED='REISSUED','Переоформлен'
        REVOKED='REVOKED','Аннулирован'

    number = models.CharField("Новый номер паспорта", max_length=32, unique=True, blank=True)

    # Нужен только как индикатор «паспорт старый». Если заполнено —
    # на PNG с QR снизу печатаем НОВЫЙ номер (self.number).
    old_passport_number = models.CharField(
        "Старый номер паспорта",
        max_length=64, null=True, blank=True, unique=True,
        help_text="Если указан — на QR-изображении снизу будет подпись с новым номером паспорта."
    )

    horse = models.OneToOneField(Horse, verbose_name="Лошадь",
                                 on_delete=models.PROTECT, related_name="passport")
    status = models.CharField("Статус", max_length=12, choices=Status.choices, default=Status.DRAFT)
    issue_date = models.DateField("Дата выдачи", null=True, blank=True)
    qr_public_id = models.UUIDField("Публичный QR-ID", default=uuid.uuid4, unique=True, editable=False)

    barcode_value = models.CharField(
        "Значение штрих-кода (микрочип)", max_length=32, blank=True
    )
    barcode_image = models.ImageField("Штрих-код (PNG)", upload_to='barcodes/', blank=True)
    qr_image = models.ImageField("QR-код (PNG)", upload_to='qrcodes/', blank=True)
    pdf_file = models.FileField("Файл паспорта (PDF)", upload_to='passports/', blank=True)
    version = models.PositiveSmallIntegerField("Версия", default=1)
    revoked_reason = models.CharField("Причина аннулирования", max_length=255, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Паспорт"
        verbose_name_plural = "Паспорта"
        indexes = [
            models.Index(fields=["number"]),
            models.Index(fields=["old_passport_number"]),
        ]

    # ---- Автонумерация и barcode ----
    def _detect_region_code(self) -> str:
        owner = getattr(self.horse, "owner_current", None)
        if owner and getattr(owner, "region", None) and getattr(owner.region, "code", None):
            return owner.region.code
        if self.horse and self.horse.place_of_birth and getattr(self.horse.place_of_birth, "code", None):
            return self.horse.place_of_birth.code
        return "FAL"

    def _detect_district_number(self) -> int:
        owner = getattr(self.horse, "owner_current", None)
        if not owner:
            return 0
        d = getattr(owner, "district", None)
        if d and getattr(d, "number", None):
            return int(d.number or 0)
        for attr in ("organization", "person", "party"):
            obj = getattr(owner, attr, None)
            if obj:
                d2 = getattr(obj, "district", None)
                if d2 and getattr(d2, "number", None):
                    return int(d2.number or 0)
        return 0

    def _ensure_number(self):
        if not self.number:
            self.number = make_passport_number(self._detect_region_code(), self._detect_district_number())

    def _ensure_barcode(self):
        mc = (self.horse.microchip or "").strip() if self.horse_id else ""
        if mc and self.barcode_value != mc:
            self.barcode_value = mc

    # публичный URL — ВСЕГДА по новому номеру
    @property
    def public_url(self):
        base = getattr(settings, "PUBLIC_BASE_URL", "http://127.0.0.1:8000")
        return f"{base}/p/{self.number}/" if self.number else f"{base}/p/"

    # --- QR PNG: кодируем public_url; при наличии old_passport_number рисуем подпись (НОВЫЙ номер) ---
    def _build_qr_png(self) -> bytes:
        # QR по публичной ссылке (новый номер)
        qr = qrcode.QRCode(version=None, box_size=10, border=4)
        qr.add_data(self.public_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # Если паспорт старый → делаем подпись с НОВЫМ номером
        if not self.old_passport_number:
            buf = io.BytesIO()
            qr_img.save(buf, format="PNG")
            return buf.getvalue()

        text = (self.number or "").strip()
        qr_w, qr_h = qr_img.size
        pad = 12
        strip_h = int(qr_h * 0.22)

        canvas = Image.new("RGB", (qr_w, qr_h + strip_h), "white")
        canvas.paste(qr_img, (0, 0))
        draw = ImageDraw.Draw(canvas)

        # Шрифт
        font = None
        font_path = getattr(settings, "QR_TEXT_FONT_PATH", None)
        if font_path:
            try:
                font = ImageFont.truetype(font_path, size=int(strip_h * 0.5))
            except Exception:
                font = None
        if font is None:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", size=int(strip_h * 0.5))
            except Exception:
                font = ImageFont.load_default()

        def measure(f):
            try:
                bbox = draw.textbbox((0, 0), text, font=f)
                return bbox[2]-bbox[0], bbox[3]-bbox[1]
            except AttributeError:
                return draw.textsize(text, font=f)

        # Уменьшаем размер, если не влезает
        if isinstance(font, ImageFont.FreeTypeFont):
            size = font.size
            tw, th = measure(font)
            while tw > (qr_w - 2*pad) and size > 10:
                size -= 1
                try:
                    font = ImageFont.truetype(font_path or "DejaVuSans.ttf", size=size)
                except Exception:
                    font = ImageFont.load_default()
                    break
                tw, th = measure(font)
        else:
            tw, th = measure(font)

        x = (qr_w - tw) // 2
        y = qr_h + (strip_h - th) // 2
        draw.text((x, y), text, fill="black", font=font)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        return buf.getvalue()

    def generate_codes(self):
        """Штрих-код по микрочипу + QR (public_url), при наличии old_passport_number — подпись с НОВЫМ номером."""
        if self.barcode_value:
            b_png = io.BytesIO()
            barcode.Code128(self.barcode_value, writer=ImageWriter()).write(b_png)
            self.barcode_image.save(f'{self.number or "no-num"}.png', ContentFile(b_png.getvalue()), save=False)

        qr_bytes = self._build_qr_png()
        self.qr_image.save(f'{self.number or "no-num"}.png', ContentFile(qr_bytes), save=False)

    def save(self, *args, **kwargs):
        self._ensure_number()
        self._ensure_barcode()

        regenerate = not self.pk
        if self.pk and not regenerate:
            prev = type(self).objects.filter(pk=self.pk).values(
                "number", "old_passport_number", "barcode_value"
            ).first() or {}
            if (
                prev.get("number") != self.number or
                prev.get("old_passport_number") != self.old_passport_number or
                prev.get("barcode_value") != self.barcode_value
            ):
                regenerate = True

        super().save(*args, **kwargs)

        if regenerate:
            self.generate_codes()
            super().save(update_fields=["barcode_image", "qr_image"])

    def __str__(self):
        return f"{self.number} → {self.horse}"
