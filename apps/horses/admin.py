from django.contrib import admin
from .models import Horse, IdentificationEvent, Ownership, HorseMeasurements, DiagnosticCheck, SportAchievement, ExhibitionEntry, Offspring
from apps.vet.models import Vaccination, LabTest

class IdentificationEventInline(admin.TabularInline):
    model = IdentificationEvent
    extra = 0
    classes = ("tab", "tab-identity")  # <-- вкладка «Идентификация»

class OwnershipInline(admin.TabularInline):
    model = Ownership
    extra = 0
    classes = ("tab", "tab-ownership")  # <-- вкладка «Владение»

class VaccinationInline(admin.TabularInline):
    model = Vaccination
    extra = 0
    classes = ("tab", "tab-vet")  # <-- вкладка «Ветеринария»

class LabTestInline(admin.TabularInline):
    model = LabTest
    extra = 0
    classes = ("tab", "tab-vet")  # <-- вкладка «Ветеринария»

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
                "microchip", "brand_mark",
                "owner_current",
                "ident_notes",
            ),
        }),
        ("Родословная", {
            "classes": ("tab", "tab-pedigree"),
            "fields": ("sire", "dam",),
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
                "photo_front_view_hind_legs",
                "photo_hind_view_forelegs",
                "photo_hind_view_hind_legs",
            ),
        }),
    )

    inlines = [
        IdentificationEventInline,
        OwnershipInline,
        VaccinationInline,
        LabTestInline,
    ]

@admin.register(HorseMeasurements)
class HorseMeasurementsAdmin(admin.ModelAdmin):
    list_display = ("horse", "withers_height_cm", "chest_girth_cm", "metacarpus_girth_cm")

@admin.register(DiagnosticCheck)
class DiagnosticCheckAdmin(admin.ModelAdmin):
    list_display = ("horse", "date", "result", "expertise_no")

@admin.register(SportAchievement)
class SportAchievementAdmin(admin.ModelAdmin):
    list_display = ("horse", "year", "place", "info")

@admin.register(ExhibitionEntry)
class ExhibitionEntryAdmin(admin.ModelAdmin):
    list_display = ("horse", "year", "place", "info")

@admin.register(Offspring)
class OffspringAdmin(admin.ModelAdmin):
    list_display = ("horse", "birth_year", "colour", "sex", "brand_no")
