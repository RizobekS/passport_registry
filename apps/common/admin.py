from django.contrib import admin
from .models import Region, Breed, Color, Vaccine, LabTestType, NumberSequence


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Vaccine)
class VaccineAdmin(admin.ModelAdmin):
    list_display = ("name", "manufacturer")
    search_fields = ("name", "manufacturer")


@admin.register(LabTestType)
class LabTestTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(NumberSequence)
class NumberSequenceAdmin(admin.ModelAdmin):
    list_display = ("scope", "year", "region_name", "value")
    list_filter = ("scope", "year")
    search_fields = ("region_name",)
