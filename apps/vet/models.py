from django.core.exceptions import ValidationError
from django.db import models
from apps.common.models import Vaccine, LabTestType
from apps.horses.models import Horse
from apps.parties.models import Veterinarian

class Vaccination(models.Model):
    horse = models.ForeignKey(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name="vaccinations")
    date = models.DateField("Дата вакцинации")
    vaccine = models.ForeignKey(Vaccine, verbose_name="Наименование вакцина", on_delete=models.PROTECT)
    registration_number = models.CharField("Номер регистрации вакцины", max_length=100, null=True)
    vaccine_for_grip = models.BooleanField("Вакцина для гриппа", null=True, default=False)
    veterinarian = models.ForeignKey(Veterinarian, verbose_name="Ф.И.О. ветеринарного врача", on_delete=models.SET_NULL, null=True, blank=True)
    place = models.CharField("Страна", max_length=160, blank=True)

    class Meta:
        verbose_name = "Отметки о вакцинации лошади"
        verbose_name_plural = "Отметки о вакцинации лошади"

    def __str__(self):
        return f"{self.date:%d.%m.%Y} — {self.horse} — {self.vaccine}"

    def clean(self):
        super().clean()
        # Требуем выбор Да/Нет в самой записи
        if self.vaccine_for_grip is None:
            raise ValidationError({"vaccine_for_grip": "Укажите: вакцина для гриппа (Да/Нет)."})

        # Требуем, чтобы в справочнике Vaccine тоже было задано Да/Нет
        if self.vaccine_id and self.vaccine.vaccine_for_grip is None:
            raise ValidationError({"vaccine": "В выбранной вакцине не указано поле «для гриппа». Заполните справочник."})

        # Если оба заданы — значения должны совпадать
        if self.vaccine_id and self.vaccine.vaccine_for_grip is not None:
            if bool(self.vaccine.vaccine_for_grip) != bool(self.vaccine_for_grip):
                raise ValidationError({
                    "vaccine_for_grip": "Значение «для гриппа» должно совпадать со значением у выбранной вакцины.",
                    "vaccine": "Выбранная вакцина имеет другое значение «для гриппа».",
                })

    def save(self, *args, **kwargs):
        self.full_clean()  # обеспечивает правило и вне админки/форм
        return super().save(*args, **kwargs)

class LabTest(models.Model):
    horse = models.ForeignKey(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name="lab_tests")
    date = models.DateField("Дата")
    test_type = models.ForeignKey(LabTestType, verbose_name="Вид исследования", on_delete=models.PROTECT)
    name_of_disease = models.CharField("Название болезни", max_length=120, blank=True)
    result = models.CharField("Результат исследования", max_length=120)
    address_lab = models.CharField("Наименование и адрес лаборатории", max_length=80, blank=True)
    veterinarian = models.ForeignKey(Veterinarian, verbose_name="Ф.И.О. ветеринарного врача", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Лабораторное исследование"
        verbose_name_plural = "Лабораторные исследования"
