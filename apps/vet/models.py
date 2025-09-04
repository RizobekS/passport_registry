from django.db import models
from apps.common.models import Vaccine, LabTestType
from apps.horses.models import Horse
from apps.parties.models import Veterinarian

class Vaccination(models.Model):
    horse = models.ForeignKey(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name="vaccinations")
    date = models.DateField("Дата")
    vaccine = models.ForeignKey(Vaccine, verbose_name="Вакцина", on_delete=models.PROTECT)
    batch_no = models.CharField("Серия/партия", max_length=64, blank=True)
    veterinarian = models.ForeignKey(Veterinarian, verbose_name="Ветеринарный врач", on_delete=models.SET_NULL, null=True, blank=True)
    place = models.CharField("Место", max_length=160, blank=True)

    class Meta:
        verbose_name = "Вакцинация"
        verbose_name_plural = "Вакцинации"

class LabTest(models.Model):
    horse = models.ForeignKey(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name="lab_tests")
    date = models.DateField("Дата")
    test_type = models.ForeignKey(LabTestType, verbose_name="Тип теста", on_delete=models.PROTECT)
    result = models.CharField("Результат", max_length=120)
    document = models.FileField("Документ", upload_to="lab_docs/", blank=True)
    veterinarian = models.ForeignKey(Veterinarian, verbose_name="Ветеринарный врач", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Лабораторный тест"
        verbose_name_plural = "Лабораторные тесты"
