from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F

class Country(models.Model):
    name = models.CharField("Название страны", max_length=120, unique=True)

    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страна"
        ordering = ["name"]

    def __str__(self): return self.name


class Region(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)
    code = models.CharField(
        "Код региона (3 буквы)",
        max_length=3,
        unique=True,
        help_text="Уникальный код региона, например: TTS, TSV, NMG, FAR",
        null=True,
        db_index=True
    )

    def clean(self):
        if self.code:
            self.code = self.code.upper()
            if len(self.code) != 3 or not self.code.isascii():
                raise ValidationError({"code": "Код должен состоять из 3 латинских символов."})

    def save(self, *args, **kwargs):
        # нормализуем код к верхнему регистру
        if self.code:
            self.code = self.code.upper()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"
        ordering = ["name"]

    def __str__(self): return self.name


class District(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="districts", verbose_name="Регион")
    number = models.PositiveSmallIntegerField("Номер района", help_text="01..99", db_index=True)
    name = models.CharField("Название района", max_length=120)

    class Meta:
        verbose_name = "Район"
        verbose_name_plural = "Районы"
        constraints = [
            models.UniqueConstraint(fields=["region", "number"], name="uniq_region_district_number"),
        ]

    def __str__(self):
        return f"{self.region.code}-{self.number:02d} {self.name}"


class Breed(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)
    class Meta:
        verbose_name = "Порода"
        verbose_name_plural = "Породы"
    def __str__(self): return self.name

class Color(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)
    class Meta:
        verbose_name = "Масть"
        verbose_name_plural = "Масти"
    def __str__(self): return self.name

class Vaccine(models.Model):
    name = models.CharField("Наименование вакцины", max_length=160)
    number = models.CharField("Номер вакцины", max_length=60, null=True)
    registration_number = models.CharField("Регистрации вакцины", max_length=100, null=True)
    manufacture_date = models.DateField("Дата изготовления вакцины", null=True)
    batch_number = models.CharField("Номер серии", max_length=60, null=True)
    manufacturer_address = models.CharField("Адрес производителя", max_length=255, null=True)

    class Meta:
        verbose_name = "Вакцина"
        verbose_name_plural = "Вакцины"
    def __str__(self): return f"{self.name} ({self.number})" if self.number else self.name

class LabTestType(models.Model):
    name = models.CharField("Вид исследования", max_length=160, unique=True)
    class Meta:
        verbose_name = "Вид исследования"
        verbose_name_plural = "Вид исследования"
    def __str__(self): return self.name


class NumberSequence(models.Model):
    scope = models.CharField("Область нумерации", max_length=40)
    year = models.PositiveIntegerField("Год")
    region_name = models.CharField("Регион (текст)", max_length=120, blank=True)
    value = models.PositiveIntegerField("Текущее значение", default=0)


    class Meta:
        unique_together = ("scope", "year", "region_name")
        verbose_name = "Счётчик номеров"
        verbose_name_plural = "Счётчики номеров"

    @classmethod
    def next(cls, scope: str, year: int, region_name: str) -> int:
        """
        Атомарно увеличивает и возвращает следующий порядковый номер
        для пары (scope, year, region_name).
        """
        with transaction.atomic():
            obj, _ = cls.objects.select_for_update().get_or_create(
                scope=scope, year=year, region_name=region_name or ""
            )
            obj.value = F("value") + 1
            obj.save(update_fields=["value"])
            obj.refresh_from_db(fields=["value"])
            return obj.value


    def __str__(self):
        return f"{self.scope}/{self.year}/{self.region_name or '-'} = {self.value}"

