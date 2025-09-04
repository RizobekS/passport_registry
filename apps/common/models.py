from django.db import models, transaction


class Region(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)

    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"

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

