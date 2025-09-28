from decimal import Decimal

from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from apps.common.models import Breed, Color, Region, Country
from apps.parties.models import Owner, Veterinarian
from apps.common.utils import make_horse_registry_no

MICROCHIP_VALIDATOR = RegexValidator(r'^\d{15}$', 'Микрочип должен содержать 15 цифр (ISO 11784/11785).')

class Horse(models.Model):
    HORSE_TYPE_CHOICES = [
        ("SPORT", "Спортивная"),
        ("SERVICE", "Служебная"),
        ("EXPO", "Выставочная"),
    ]
    registry_no = models.CharField("№ Регистрации", max_length=32, unique=True, blank=True)
    name = models.CharField("Кличка", max_length=120)
    sex = models.CharField("Пол", max_length=1, choices=[('M','Жеребец'),('F','Кобыла')])
    horse_type = models.CharField("Тип лошади", max_length=10, choices=HORSE_TYPE_CHOICES, default="SPORT",
                                  db_index=True)
    birth_date = models.DateField("Дата рождения")
    breed = models.ForeignKey(Breed, verbose_name="Порода", on_delete=models.PROTECT)
    color = models.ForeignKey(Color, verbose_name="Масть", on_delete=models.PROTECT)
    country_of_birth = models.ForeignKey(Country, verbose_name="Страна", on_delete=models.SET_NULL, null=True, blank=True)
    place_of_birth = models.ForeignKey(Region, verbose_name="Место рождения (регион)", on_delete=models.SET_NULL, null=True, blank=True)
    microchip = models.CharField("Микрочип", max_length=15, unique=True, validators=[MICROCHIP_VALIDATOR])
    owner_current = models.ForeignKey(Owner, verbose_name="Текущий владелец", null=True, blank=True, on_delete=models.SET_NULL, related_name="horses")

    photo_right_side = models.ImageField("Фото: Правая боковая сторона", upload_to="horses/", blank=True)
    photo_left_side = models.ImageField("Фото: Левая боковая сторона", upload_to="horses/", blank=True)
    photo_upper_eye_level = models.ImageField("Фото: Верхний уровень глаз", upload_to="horses/", blank=True)
    photo_muzzle = models.ImageField("Фото: морда (крупно)", upload_to="horses/", blank=True)
    photo_neck_lower_view = models.ImageField("Фото: Нижний вид шеи", upload_to="horses/", blank=True)
    photo_front_view_forelegs = models.ImageField("Фото: Вид ног спереди (Левый и Правый)", upload_to="horses/", blank=True)
    photo_hind_view_hind_legs = models.ImageField("Фото: Вид ног с зада (Левый и Правый)", upload_to="horses/", blank=True)

    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Регистрация лошади"
        verbose_name_plural = "Регистрация лошадей"

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
        verbose_name = "Описание примет лошадей"
        verbose_name_plural = "Описание примет лошадей"

    def __str__(self):
        return f"Промеры: {self.horse}"


class DiagnosticCheck(models.Model):
    horse = models.ForeignKey(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name='diagnostics')
    date = models.DateField("Дата (число/месяц/год)", null=True)
    place_event = models.CharField("Место проведения соревнования", max_length=500, null=True, blank=True)
    urine = models.CharField("Моча", max_length=100, null=True, blank=True)
    blood = models.CharField("Кровь", max_length=100, null=True, blank=True)
    others = models.CharField("Другие", max_length=100, null=True, blank=True)
    veterinarian = models.ForeignKey(Veterinarian, verbose_name="Ветеринарный врач", on_delete=models.DO_NOTHING, related_name='diagnostics')

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
    horse = models.ForeignKey(Horse, verbose_name="Лошадь", on_delete=models.CASCADE, related_name="offspring")
    brand_no = models.CharField("Тамга/Тавро №", max_length=50, blank=True)
    shb_no = models.CharField("ДНК №", max_length=50, blank=True)
    immunity_exp_number = models.CharField("№ экспертизы иммунитета", max_length=100, blank=True)
    immunity_exp_date = models.DateField("Дата экспертизы иммунитета", blank=True, null=True)

    class Meta:
        verbose_name = "Родословная"
        verbose_name_plural = "Родословная"
        indexes = [
            models.Index(fields=["horse", "shb_no"]),
        ]

    def __str__(self):
        return f"{self.horse} | {self.shb_no}"


class HorseBonitation(models.Model):
    """
    Бонитировка/характеристика лошади за конкретный период (I/II/III).
    Числовые промеры храним в см, оценки (score) — целые 1..10.
    """
    class Period(models.IntegerChoices):
        I = 1, "I"
        II = 2, "II"
        III = 3, "III"

    horse = models.ForeignKey(
        Horse, verbose_name="Лошадь",
        on_delete=models.CASCADE, related_name="bonitations"
    )
    period = models.PositiveSmallIntegerField(
        "Период", choices=Period.choices, db_index=True
    )

    # --- Промеры (таблица «Ўлчамлари / Промеры / Measure»)
    age_years = models.PositiveSmallIntegerField("Возраст, лет", null=True, blank=True)
    height_withers_cm = models.PositiveSmallIntegerField(
        "Высота в холке",validators=[MinValueValidator(1), MaxValueValidator(10)], null=True, blank=True
    )
    torso_oblique_length_cm = models.PositiveSmallIntegerField(
        "Косая длина туловища", validators=[MinValueValidator(1), MaxValueValidator(10)], null=True, blank=True
    )
    chest_girth_cm = models.PositiveSmallIntegerField(
        "Обхват груди", validators=[MinValueValidator(1), MaxValueValidator(10)], null=True, blank=True
    )
    metacarpus_girth_cm = models.PositiveSmallIntegerField(
        "Обхват пясти", validators=[MinValueValidator(1), MaxValueValidator(10)], null=True, blank=True
    )

    # --- Показатели (баллы 1..10)
    origin_score = models.PositiveSmallIntegerField(
        "Происхождение (балл)", validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True
    )
    typicality_score = models.PositiveSmallIntegerField(
        "Типичность (балл)", validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True
    )
    measure_score = models.PositiveSmallIntegerField(
        "Промеры (балл)", validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True
    )
    exteriors_score = models.PositiveSmallIntegerField(
        "Экстерьер (балл)", validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True
    )
    capacity_score = models.PositiveSmallIntegerField(
        "Работоспособность/способности (балл)", validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True
    )
    quality_of_breed_score = models.PositiveSmallIntegerField(
        "Качество потомства (балл)", validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True
    )
    class_score = models.PositiveSmallIntegerField(
        "Класс (балл)", validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True
    )

    # Итоговая отметка «Бонитировка баллари / Bonitation mark»
    bonitation_mark = models.PositiveSmallIntegerField(
        "Итоговая оценка (1..10)", validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True
    )

    note = models.CharField("Примечание", max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Характеристика лошади (бонитировка)"
        verbose_name_plural = "Характеристики лошадей (бонитировки)"
        unique_together = (("horse", "period"),)
        indexes = [
            models.Index(fields=["horse", "period"]),
        ]
        ordering = ["-period"]

    def __str__(self):
        return f"{self.horse}"

    @property
    def average_score(self) -> Decimal | None:
        """Средний балл по заполненным показателям (без итоговой)."""
        vals = [
            self.origin_score, self.typicality_score, self.measure_score,
            self.exteriors_score, self.capacity_score,
            self.quality_of_breed_score, self.class_score,
        ]
        nums = [Decimal(v) for v in vals if isinstance(v, int)]
        return (sum(nums) / len(nums)) if nums else None
