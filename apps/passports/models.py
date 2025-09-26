import io, uuid
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image as PILImage, ImageDraw, ImageFont
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

    @property
    def is_active(self) -> bool:
        return self.status in (self.Status.ISSUED, self.Status.REISSUED)

    @property
    def has_old(self) -> bool:
        return bool((self.old_passport_number or "").strip())

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
        qr = qrcode.QRCode(version=None, box_size=10, border=4)
        qr.add_data(self.public_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_w, qr_h = qr_img.size

        if not (self.is_active and self.has_old):
            buf = io.BytesIO()
            qr_img.save(buf, format="PNG")
            return buf.getvalue()

        text = (self.number or "").strip()
        pad = 7
        max_strip_w = int(qr_w * 0.45)
        max_rot_h = qr_h - 2 * pad

        font_path = getattr(settings, "QR_TEXT_FONT_PATH", None)

        def load_font(sz: int):
            try:
                if font_path:
                    return ImageFont.truetype(str(font_path), size=sz)
                return ImageFont.truetype("DejaVuSans.ttf", size=sz)
            except Exception:
                return ImageFont.load_default()

        size = int(qr_h * 0.16)
        font = load_font(size)

        # ВРЕМЕННЫЙ холст для измерений
        tmp = PILImage.new("RGB", (1, 1), "white")
        draw = ImageDraw.Draw(tmp)

        def text_wh(f):
            try:
                bbox = draw.textbbox((0, 0), text, font=f)
                return bbox[2] - bbox[0], bbox[3] - bbox[1]
            except AttributeError:
                return draw.textsize(text, font=f)

        tw, th = text_wh(font)
        while ((tw + 2 * pad) > max_rot_h or (th + 2 * pad) > max_strip_w) and size > 10:
            size -= 1
            font = load_font(size)
            tw, th = text_wh(font)

        # Рисуем горизонтально, потом поворачиваем
        text_img = PILImage.new("RGBA", (tw + 2 * pad, th + 2 * pad), (255, 255, 255, 0))
        tdraw = ImageDraw.Draw(text_img)
        tdraw.text((pad, pad), text, fill=(0, 0, 0, 255), font=font)

        rotate_deg = int(getattr(settings, "QR_TEXT_ROTATE", 90))  # 90 — снизу-вверх; 270 — сверху-вниз
        text_rot = text_img.rotate(rotate_deg, expand=True, resample=PILImage.BICUBIC)

        strip_w = text_rot.width
        strip_h = text_rot.height

        canvas = PILImage.new("RGB", (strip_w + qr_w, qr_h), "white")
        y0 = max(0, (qr_h - strip_h) // 2)
        canvas.paste(text_rot.convert("RGB"), (0, y0))
        canvas.paste(qr_img, (strip_w, 0))

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
