# horses/admin.py
from django.contrib import admin
from .models import (
    Horse, IdentificationEvent, Ownership,
    HorseMeasurements, DiagnosticCheck,
    SportAchievement, ExhibitionEntry, Offspring
)
from apps.vet.models import Vaccination, LabTest


class IdentificationEventInline(admin.TabularInline):
    model = IdentificationEvent
    extra = 0
    classes = ("tab", "tab-identity")


class OwnershipInline(admin.TabularInline):
    model = Ownership
    extra = 0
    classes = ("tab", "tab-ownership")


class VaccinationInline(admin.TabularInline):
    model = Vaccination
    extra = 0
    classes = ("tab", "tab-vet")


class LabTestInline(admin.TabularInline):
    model = LabTest
    extra = 0
    classes = ("tab", "tab-vet")


class OffspringInline(admin.TabularInline):
    model = Offspring
    extra = 0
    classes = ("tab", "tab-pedigree")
    fields = (
        "relation", "name_klichka", "sex", "breed",
        "date_birth", "place_birth",
        "colour_horse", "brand_no", "shb_no", "reg_number",
        "immunity_exp_number", "immunity_exp_date",
    )
    autocomplete_fields = ()
    show_change_link = True


class HorseMeasurementsInline(admin.StackedInline):
    model = HorseMeasurements
    extra = 0
    max_num = 1
    can_delete = True
    classes = ("tab", "tab-measure")


@admin.register(Horse)
class HorseAdmin(admin.ModelAdmin):
    list_display = ("name", "registry_no", "microchip", "breed", "color", "birth_date", "place_of_birth", "horse_type")
    search_fields = ("name", "registry_no", "microchip", "brand_mark")
    list_filter = ("breed", "color", "place_of_birth", "horse_type")
    readonly_fields = ("registry_no",)

    fieldsets = (
        ("Основная информация", {
            "classes": ("tab", "tab-main"),
            "fields": (
                "registry_no", "name", "sex", "horse_type",
                "birth_date", "breed", "color", "place_of_birth",
                "microchip", "brand_mark", 'dna_no',
                "owner_current",
                "ident_notes",
            ),
        }),
        ("Фотографии", {
            "classes": ("tab", "tab-photos"),
            "fields": (
                "photo_right_side",
                "photo_left_side",
                "photo_upper_eye_level",
                "photo_muzzle",
                "photo_neck_lower_view",
                "photo_front_view_forelegs",
                "photo_hind_view_hind_legs",
            ),
        }),
    )

    inlines = [
        HorseMeasurementsInline,   # ← удобно редактировать на карточке лошади
        OffspringInline,           # ← новая вкладка «Родословная»
        IdentificationEventInline,
        OwnershipInline,
        VaccinationInline,
        LabTestInline,
    ]


# Если хочешь оставить отдельные административные страницы — можно и так:

@admin.register(HorseMeasurements)
class HorseMeasurementsAdmin(admin.ModelAdmin):
    list_display = ("horse", "head", "left_foreleg", "right_foreleg", "left_hindleg", "right_hindleg")
    search_fields = ("horse__name", "horse__registry_no")


@admin.register(DiagnosticCheck)
class DiagnosticCheckAdmin(admin.ModelAdmin):
    list_display = ("horse", "date", "veterinarian", "place_event", "urine", "blood", "others")
    list_filter = ("date",)
    search_fields = ("horse__name", "horse__registry_no", "veterinarian__person__last_name")


@admin.register(SportAchievement)
class SportAchievementAdmin(admin.ModelAdmin):
    list_display = ("horse", "year", "place", "info")
    search_fields = ("horse__name", "place", "info")


@admin.register(ExhibitionEntry)
class ExhibitionEntryAdmin(admin.ModelAdmin):
    list_display = ("horse", "year", "place", "info")
    search_fields = ("horse__name", "place", "info")


@admin.register(Offspring)
class OffspringAdmin(admin.ModelAdmin):
    list_display = ("horse", "relation", "name_klichka", "date_birth", "breed", "colour_horse")
    list_filter = ("relation", "breed")
    search_fields = ("horse__name", "name_klichka", "reg_number", "brand_no", "shb_no")
