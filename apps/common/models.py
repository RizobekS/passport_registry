from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F


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
    name = models.CharField("Наименование", max_length=160)
    manufacturer = models.CharField("Производитель", max_length=160, blank=True)
    class Meta:
        unique_together = ("name", "manufacturer")
        verbose_name = "Вакцина"
        verbose_name_plural = "Вакцины"
    def __str__(self): return f"{self.name} ({self.manufacturer})" if self.manufacturer else self.name

class LabTestType(models.Model):
    name = models.CharField("Тип теста", max_length=160, unique=True)
    class Meta:
        verbose_name = "Тип лабораторного теста"
        verbose_name_plural = "Типы лабораторных тестов"
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
    def next(cls, *, scope: str, year: int, region_code: str) -> int:
        """
        Атомарно увеличивает и возвращает следующий порядковый номер
        для данного scope+year+region_code. Используем select_for_update для защиты от гонок.
        """
        with transaction.atomic():
            # region_name оставим равным region_code (чтобы не ломать существующую схему)
            obj, _ = cls.objects.select_for_update().get_or_create(
                scope=scope, year=year, region_name=region_code, defaults={"value": 0}
            )
            obj.value = F("value") + 1
            obj.save(update_fields=["value"])
            obj.refresh_from_db(fields=["value"])
            return obj.value


    def __str__(self):
        return f"{self.scope}/{self.year}/{self.region_name or '-'} = {self.value}"


    @classmethod
    def next(cls, scope: str, year: int, region_name: str = "") -> int:
        with transaction.atomic():
            seq, _ = cls.objects.select_for_update().get_or_create(
                scope=scope, year=year, region_name=region_name
            )
            seq.value += 1
            seq.save(update_fields=["value"])
            return seq.value

