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
    head = models.CharField("Голова", max_length=255, blank=True)
    left_foreleg = models.CharField("Левая передняя нога",max_length=255, blank=True)
    right_foreleg = models.CharField("Правая передняя нога",max_length=255, blank=True)
    left_hindleg = models.CharField("Левая задняя нога",max_length=255, blank=True)
    right_hindleg = models.CharField("Правая задняя нога",max_length=255, blank=True)
    extra_signs = models.TextField("Дополнительные приметы",blank=True)
    address_stable = models.TextField("Адрес конюшни",max_length=255,blank=True)

    class Meta:
        verbose_name = "Промеры лошади"
        verbose_name_plural = "Промеры лошадей"

    def __str__(self):
        return f"Промеры: {self.horse}"


class DiagnosticCheck(models.Model):
    horse = models.ForeignKey(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name='diagnostics')
    date = models.DateField("Дата (число/месяц/год)", null=True)
    veterinarian = models.ForeignKey(Veterinarian, verbose_name="Ветеринарный врач", on_delete=models.DO_NOTHING, related_name='diagnostics')
    place_event = models.CharField("Место проведения соревнования", max_length=500, null=True, blank=True)
    urine = models.CharField("Моча", max_length=100, null=True, blank=True)
    blood = models.CharField("Кровь", max_length=100, null=True, blank=True)
    others = models.CharField("Другие", max_length=100, null=True, blank=True)

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
    class Relation(models.TextChoices):
        SIRE = "SIRE", "Отец"
        DAM  = "DAM",  "Мать"
        OTHER = "OTHER", "Иное (родословная)"

    horse = models.ForeignKey(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name="offspring")
    relation = models.CharField("Роль", max_length=10, choices=Relation.choices, default=Relation.OTHER, db_index=True)

    place_birth = models.CharField("Место рождения", max_length=120, blank=True)
    name_klichka = models.CharField("Кличка", max_length=120, blank=True)
    colour_horse = models.CharField("Масть", max_length=50, blank=True)
    brand_no = models.CharField("Тавро №", max_length=50, blank=True)
    shb_no = models.CharField("ГПК №", max_length=50, blank=True)
    reg_number = models.CharField("Регистрационный номер", max_length=50, blank=True)
    breed = models.CharField("Порода", max_length=100, blank=True)
    date_birth = models.DateField("Дата рождения", blank=True, null=True)
    sex = models.CharField("Пол", max_length=20, blank=True)
    immunity_exp_number = models.CharField("№ экспертизы иммунитета ", max_length=100, blank=True)
    immunity_exp_date = models.DateField("Дата экспертизы иммунитета ", blank=True, null=True)

    class Meta:
        verbose_name = "Родословная"
        verbose_name_plural = "Родословная"
        indexes = [
            models.Index(fields=["horse", "relation"]),
        ]

    def __str__(self):
        r = dict(self.Relation.choices).get(self.relation, self.relation)
        return f"{r}: {self.name_klichka or '—'} ({self.horse})"
