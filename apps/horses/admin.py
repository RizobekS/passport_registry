# horses/admin.py
from django.contrib import admin
from .models import (
    Horse, IdentificationEvent, Ownership,
    HorseMeasurements, DiagnosticCheck,
    SportAchievement, ExhibitionEntry, Offspring, HorseBonitation, RealOffspringNode, RealOffspring
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
        "brand_no", "shb_no",
        "immunity_exp_number", "immunity_exp_date",
    )
    autocomplete_fields = ()
    show_change_link = True


class HorseBonitationInline(admin.TabularInline):
    model = HorseBonitation
    extra = 0
    classes = ("tab", "tab-bonitation")
    fields = (
        "period",
        "age_years", "height_withers_cm", "torso_oblique_length_cm",
        "chest_girth_cm", "metacarpus_girth_cm",
        "origin_score", "typicality_score", "measure_score",
        "exteriors_score", "capacity_score", "quality_of_breed_score",
        "class_score", "bonitation_mark", "note",
    )
    ordering = ("-period",)


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
                "microchip", "owner_current",
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
        HorseMeasurementsInline,
        HorseBonitationInline,
        OffspringInline,
        IdentificationEventInline,
        OwnershipInline,
        VaccinationInline,
        LabTestInline,
    ]

    class Media:
        js = (
            "https://unpkg.com/html5-qrcode/html5-qrcode.min.js",
            "js/microchip_scanner.js",
        )


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
    list_display = ("horse", "brand_no", "shb_no")
    list_filter = ("brand_no", "shb_no")
    search_fields = ("horse", "brand_no", "shb_no")


class RealOffspringNodeInline(admin.TabularInline):
    model = RealOffspringNode
    extra = 14  # чтобы было место под все 14 сразу
    fields = ("relation", "name", "brand_no", "breed")
    ordering = ("relation",)

@admin.register(RealOffspring)
class RealOffspringAdmin(admin.ModelAdmin):
    list_display = ("horse", "created_at")
    autocomplete_fields = ("horse",)
    inlines = [RealOffspringNodeInline]
