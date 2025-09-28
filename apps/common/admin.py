from django.contrib import admin
from .models import Region, Breed, Color, Vaccine, LabTestType, NumberSequence, District, Country


class DistrictInline(admin.TabularInline):
    model = District
    extra = 0
    classes = ("tab", "tab-identity")


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")
    inlines = (DistrictInline, )

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Vaccine)
class VaccineAdmin(admin.ModelAdmin):
    list_display = ("name", "batch_number", "vaccine_for_grip", "manufacture_date", "manufacturer_address")
    search_fields = ("name", "batch_number")


@admin.register(LabTestType)
class LabTestTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(NumberSequence)
class NumberSequenceAdmin(admin.ModelAdmin):
    list_display = ("scope", "year", "region_name", "value")
    list_filter = ("scope", "year")
    search_fields = ("region_name",)
