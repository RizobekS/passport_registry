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
