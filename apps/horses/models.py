from django.db import models
from django.core.validators import RegexValidator
from apps.common.models import Breed, Color, Region
from apps.parties.models import Owner, Veterinarian
from apps.common.utils import make_horse_registry_no

MICROCHIP_VALIDATOR = RegexValidator(r'^\d{15}$', 'Микрочип должен содержать 15 цифр (ISO 11784/11785).')

class Horse(models.Model):
    HORSE_TYPE_CHOICES = [
        ("SPORT", "Спортивная"),
        ("SERVICE", "Служебная"),
        ("EXPO", "Выставочная"),
    ]
    registry_no = models.CharField("Реестровый номер (Генерируется автоматически)", max_length=32, unique=True, blank=True)
    name = models.CharField("Кличка", max_length=120)
    sex = models.CharField("Пол", max_length=1, choices=[('M','Жеребец'),('F','Кобыла')])
    horse_type = models.CharField("Тип лошади", max_length=10, choices=HORSE_TYPE_CHOICES, default="SPORT",
                                  db_index=True)
    birth_date = models.DateField("Дата рождения")
    breed = models.ForeignKey(Breed, verbose_name="Порода", on_delete=models.PROTECT)
    color = models.ForeignKey(Color, verbose_name="Масть", on_delete=models.PROTECT)
    place_of_birth = models.ForeignKey(Region, verbose_name="Место рождения (регион)", on_delete=models.SET_NULL, null=True, blank=True)
    microchip = models.CharField("Микрочип", max_length=15, unique=True, validators=[MICROCHIP_VALIDATOR])
    brand_mark = models.CharField("Клеймо/тавро", max_length=64, blank=True)
    sire = models.ForeignKey('self', verbose_name="Отец", null=True, blank=True, related_name='offspring_sire', on_delete=models.SET_NULL)
    dam = models.ForeignKey('self', verbose_name="Мать", null=True, blank=True, related_name='offspring_dam', on_delete=models.SET_NULL)
    owner_current = models.ForeignKey(Owner, verbose_name="Текущий владелец", null=True, blank=True, on_delete=models.SET_NULL, related_name="horses")

    ident_notes = models.TextField("Особые приметы", blank=True)

    photo_right_side = models.ImageField("Фото: правая сторона", upload_to="horses/", blank=True)
    photo_left_side = models.ImageField("Фото: левая сторона", upload_to="horses/", blank=True)
    photo_upper_eye_level = models.ImageField("Фото: уровень выше глаз", upload_to="horses/", blank=True)
    photo_muzzle = models.ImageField("Фото: морда (крупно)", upload_to="horses/", blank=True)
    photo_neck_lower_view = models.ImageField("Фото: шея (снизу)", upload_to="horses/", blank=True)
    photo_front_view_forelegs = models.ImageField("Фото: передние ноги (спереди)", upload_to="horses/", blank=True)
    photo_front_view_hind_legs = models.ImageField("Фото: задние ноги (спереди)", upload_to="horses/", blank=True)
    photo_hind_view_forelegs = models.ImageField("Фото: передние ноги (сзади)", upload_to="horses/", blank=True)
    photo_hind_view_hind_legs = models.ImageField("Фото: задние ноги (сзади)", upload_to="horses/", blank=True)

    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Лошадь"
        verbose_name_plural = "Лошади"

    def __str__(self): return f"{self.name} [{self.registry_no}]"

    def save(self, *args, **kwargs):
        if not self.registry_no:
            reg_code = self.place_of_birth.code if self.place_of_birth and getattr(self.place_of_birth, "code",
                                                                                   None) else ""
            self.registry_no = make_horse_registry_no(reg_code)
        super().save(*args, **kwargs)

class IdentificationEvent(models.Model):
    horse = models.ForeignKey(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name="ident_events")
    date = models.DateField("Дата")
    veterinarian = models.ForeignKey(Veterinarian, verbose_name="Ветеринарный врач", on_delete=models.SET_NULL, null=True, blank=True)
    microchip = models.CharField("Микрочип", max_length=15, validators=[MICROCHIP_VALIDATOR])
    note = models.CharField("Примечание", max_length=255, blank=True)

    class Meta:
        verbose_name = "Событие идентификации"
        verbose_name_plural = "События идентификации"

class Ownership(models.Model):
    horse = models.ForeignKey(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name="ownerships")
    owner = models.ForeignKey(Owner, verbose_name="Владелец", on_delete=models.PROTECT)
    start_date = models.DateField("Начало владения")
    end_date = models.DateField("Окончание владения", null=True, blank=True)
    document = models.FileField("Документ", upload_to="ownership_docs/", blank=True)
    class Meta:
        verbose_name = "История владения"
        verbose_name_plural = "История владения"
        ordering = ["-start_date"]


class HorseMeasurements(models.Model):
    horse = models.OneToOneField(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name='meas')
    withers_height_cm = models.DecimalField("Высота в холке, см", max_digits=5, decimal_places=1, null=True, blank=True)
    torso_oblique_len_cm = models.DecimalField("Косая длина туловища, см", max_digits=5, decimal_places=1, null=True, blank=True)
    chest_girth_cm = models.DecimalField("Обхват груди, см", max_digits=5, decimal_places=1, null=True, blank=True)
    metacarpus_girth_cm = models.DecimalField("Обхват пясти, см", max_digits=5, decimal_places=1, null=True, blank=True)
    bonitation_i = models.PositiveSmallIntegerField("Бонитировка I", null=True, blank=True)
    bonitation_ii = models.PositiveSmallIntegerField("Бонитировка II", null=True, blank=True)
    bonitation_iii = models.PositiveSmallIntegerField("Бонитировка III", null=True, blank=True)
    class Meta:
        verbose_name = "Промеры лошади"
        verbose_name_plural = "Промеры лошадей"


class DiagnosticCheck(models.Model):
    horse = models.ForeignKey(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name='diagnostics')
    veterinarian = models.ForeignKey(Veterinarian, verbose_name="Ветеринарный врач", on_delete=models.DO_NOTHING, related_name='diagnostics')
    date = models.DateField("Дата")
    result = models.CharField("Результат", max_length=200)
    expertise_no = models.CharField("№ экспертизы", max_length=64, blank=True)
    class Meta:
        verbose_name = "Диагностическое исследование"
        verbose_name_plural = "Диагностические исследования"

class SportAchievement(models.Model):
    horse = models.ForeignKey(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name='achievements')
    year = models.PositiveSmallIntegerField("Год")
    place = models.CharField("Место", max_length=160, blank=True)
    info = models.CharField("Сведения", max_length=255, blank=True)
    class Meta:
        verbose_name = "Спортивное достижение"
        verbose_name_plural = "Спортивные достижения"

class ExhibitionEntry(models.Model):
    horse = models.ForeignKey(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name='exhibitions')
    year = models.PositiveSmallIntegerField("Год")
    place = models.CharField("Место", max_length=160, blank=True)
    info = models.CharField("Сведения", max_length=255, blank=True)
    class Meta:
        verbose_name = "Участие в выставке"
        verbose_name_plural = "Участия в выставках"

class Offspring(models.Model):
    horse = models.ForeignKey(Horse, verbose_name="Родитель", on_delete=models.CASCADE, related_name='offspring')
    sire_name = models.CharField("Отец (кличка)", max_length=120, blank=True)
    dam_name = models.CharField("Мать (кличка)", max_length=120, blank=True)
    sire_breed = models.CharField("Порода отца", max_length=120, blank=True)
    dam_breed = models.CharField("Порода матери", max_length=120, blank=True)
    colour = models.CharField("Масть", max_length=120, blank=True)
    sex = models.CharField("Пол", max_length=10, blank=True)
    brand_no = models.CharField("Тавро №", max_length=64, blank=True)
    birth_year = models.PositiveSmallIntegerField("Год рождения", null=True, blank=True)
    class Meta:
        verbose_name = "Потомок"
        verbose_name_plural = "Потомство"
