import io, uuid
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.common.models import NumberSequence
from apps.common.utils import make_passport_number
from apps.horses.models import Horse
import barcode, qrcode
from barcode.writer import ImageWriter

class Passport(models.Model):
    class Status(models.TextChoices):
        DRAFT='DRAFT','Черновик'
        ISSUED='ISSUED','Выдан'
        REISSUED='REISSUED','Переоформлен'
        REVOKED='REVOKED','Аннулирован'

    number = models.CharField("Номер паспорта", max_length=32, unique=True, blank=True)
    horse = models.OneToOneField(Horse, verbose_name="Лошадь", on_delete=models.PROTECT, related_name="passport")
    status = models.CharField("Статус", max_length=12, choices=Status.choices, default=Status.DRAFT)
    issue_date = models.DateField("Дата выдачи", null=True, blank=True)
    qr_public_id = models.UUIDField("Публичный QR-ID", default=uuid.uuid4, unique=True, editable=False)
    barcode_value = models.CharField(
        "Значение штрих-кода (автоматически заполнится по номеру микрочипа)",
        max_length=32,
        blank=True
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


        # ---- Автонумерация ----
    def _detect_region_code(self) -> str:
        # определяет место рождения -> регион владельца -> 'FAL')
        if self.horse and self.horse.place_of_birth and getattr(self.horse.place_of_birth, "code", None):
            return self.horse.place_of_birth.code
        owner = getattr(self.horse, "owner_current", None)
        if owner and getattr(owner, "region", None) and getattr(owner.region, "code", None):
            return owner.region.code
        return "FAL"

    def _ensure_number(self):
        """
        Если номер не задан — сгенерировать по схеме: UZ-<REG>-<YEAR>-<####>
        через общий утилитарный генератор (под капотом — NumberSequence.next).
        Также заполняем barcode_value номером, если он пустой.
        """
        if self.number:
            return
        # Год берём из issue_date, если уже задан, иначе — текущий (на уровне utils это не критично)
        # Основное — корректно определить код региона:
        region_code = self._detect_region_code()
        self.number = make_passport_number(region_code)

    def _ensure_barcode(self):
        """
        Если значение штрих-кода не задано – берём microchip лошади.
        Если задано, но отличается от microchip, приводим к microchip (жёсткое правило).
        """
        mc = (self.horse.microchip or "").strip() if self.horse_id else ""
        if mc:
            if self.barcode_value != mc:
                self.barcode_value = mc



    def save(self, *args, **kwargs):
        self._ensure_number()
        self._ensure_barcode()
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.number} → {self.horse}"

    @property
    def public_url(self):
        base = getattr(settings, "PUBLIC_BASE_URL", "http://127.0.0.1:8000")
        return f"{base}/p/{self.qr_public_id}/"

    def generate_codes(self):
        # Штрих-код (Code128)
        b_png = io.BytesIO()
        barcode.Code128(self.barcode_value, writer=ImageWriter()).write(b_png)
        self.barcode_image.save(f'{self.number}.png', ContentFile(b_png.getvalue()), save=False)

        # QR-код с публичной ссылкой
        qr_img = qrcode.make(self.public_url)
        q_png = io.BytesIO()
        qr_img.save(q_png, format='PNG')
        self.qr_image.save(f'{self.number}.png', ContentFile(q_png.getvalue()), save=False)
