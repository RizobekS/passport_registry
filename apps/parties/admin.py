from django.contrib import admin
from .models import Person, Organization, Veterinarian, Owner


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "doc_no", "inn", "phone", "region")
    search_fields = ("last_name", "first_name", "doc_no", "inn", "phone")
    list_filter = ("region",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "reg_no", "inn", "phone", "region")
    search_fields = ("name", "reg_no", "inn")
    list_filter = ("region",)


@admin.register(Veterinarian)
class VeterinarianAdmin(admin.ModelAdmin):
    list_display = ("person", "license_no")
    search_fields = ("person__last_name", "person__first_name", "license_no")


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ("person", "organization")
    search_fields = ("person__last_name", "organization__name")
