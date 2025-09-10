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
        """
        Для паспорта приоритетно использовать регион ВЛАДЕЛЬЦА.
        Если нет владельца/региона — fallback: место рождения лошади.
        """
        owner = getattr(self.horse, "owner_current", None)
        if owner and getattr(owner, "region", None) and getattr(owner.region, "code", None):
            return owner.region.code
        if self.horse and self.horse.place_of_birth and getattr(self.horse.place_of_birth, "code", None):
            return self.horse.place_of_birth.code
        return "FAL"

    def _detect_district_number(self) -> int:
        """
        Ищем номер района у владельца (Organization/Person).
        Если район не указан — вернём 0 (номер будет с RR=00).
        """
        owner = getattr(self.horse, "owner_current", None)
        if not owner:
            return 0
        # Прямое поле district
        d = getattr(owner, "district", None)
        if d and getattr(d, "number", None):
            return int(d.number or 0)

        # На случай обёрток (если Owner ссылается на person/organization/party)
        for attr in ("organization", "person", "party"):
            obj = getattr(owner, attr, None)
            if obj:
                d2 = getattr(obj, "district", None)
                if d2 and getattr(d2, "number", None):
                    return int(d2.number or 0)

        return 0

    def _ensure_number(self):
        """
        Если номер не задан — генерируем по новой схеме UZ-<REG>-<RR><NNNN>.
        Также заполняем barcode_value microchip’ом, если пустой.
        """
        if self.number:
            return
        region_code = self._detect_region_code()
        district_number = self._detect_district_number()
        self.number = make_passport_number(region_code, district_number)

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
