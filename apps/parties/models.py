from django.core.exceptions import ValidationError
from django.db import models
from apps.common.models import Region, District

class Person(models.Model):
    last_name = models.CharField("Фамилия", max_length=120)
    first_name = models.CharField("Имя", max_length=120)
    middle_name = models.CharField("Отчество", max_length=120, blank=True)
    doc_no = models.CharField("Документ (№)", max_length=64, blank=True)   # паспорт/ID
    inn = models.CharField("ИНН", max_length=20, blank=True)
    phone = models.CharField("Телефон", max_length=30, blank=True)
    address = models.CharField("Адрес", max_length=255, blank=True)
    region = models.ForeignKey(Region, verbose_name="Регион", on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.PROTECT, verbose_name="Район", null=True)

    def clean(self):
        super().clean()
        if self.district and self.district.region_id != self.region_id:
            raise ValidationError({"district": "Выбранный район не относится к указанному региону."})

    class Meta:
        verbose_name = "Физическое лицо"
        verbose_name_plural = "Физические лица"

    def __str__(self):
        return f"{self.last_name} {self.first_name}".strip()

class Organization(models.Model):
    class OrgType(models.TextChoices):
        STATE = "STATE", "Государственная"
        PRIVATE = "PRIVATE", "Частная"

    name = models.CharField("Наименование", max_length=200)
    reg_no = models.CharField("Рег. номер", max_length=64, blank=True)
    inn = models.CharField("ИНН", max_length=20, blank=True)
    phone = models.CharField("Телефон", max_length=30, blank=True)
    address = models.CharField("Адрес", max_length=255, blank=True)
    region = models.ForeignKey(Region, verbose_name="Регион", on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.PROTECT, verbose_name="Район", null=True)
    org_type = models.CharField(
        "Тип организации",
        max_length=20,
        choices=OrgType.choices,
        default=OrgType.PRIVATE,
        db_index=True,
        help_text="Гос. организация или частная"
    )

    def clean(self):
        super().clean()
        if self.district and self.district.region_id != self.region_id:
            raise ValidationError({"district": "Выбранный район не относится к указанному региону."})

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"

    def __str__(self): return self.name

class Veterinarian(models.Model):
    person = models.OneToOneField(Person, verbose_name="Персона", on_delete=models.CASCADE)
    license_no = models.CharField("Лицензия (№)", max_length=64)
    class Meta:
        verbose_name = "Ветеринарный врач"
        verbose_name_plural = "Ветеринарные врачи"
    def __str__(self): return f"{self.person} (лиц. {self.license_no})"

class Owner(models.Model):
    # Владелец может быть физлицом или организацией
    person = models.ForeignKey(Person, verbose_name="Физлицо", on_delete=models.SET_NULL, null=True, blank=True)
    organization = models.ForeignKey(Organization, verbose_name="Организация", on_delete=models.SET_NULL, null=True,
                                     blank=True)
    class Meta:
        verbose_name = "Владелец"
        verbose_name_plural = "Владельцы"

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.person and not self.organization:
            raise ValidationError("Укажите физлицо или организацию.")
        if self.person and self.organization:
            raise ValidationError("Укажите только один тип владельца.")

    def __str__(self):
        return str(self.person or self.organization)
