from django.contrib import admin
from .models import Person, Organization, Veterinarian, Owner


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "doc_no", "inn", "phone", "region")
    search_fields = ("last_name", "first_name", "doc_no", "inn", "phone")
    list_filter = ("region",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "org_type", "region", "inn", "phone")
    list_filter = ("org_type", "region")
    search_fields = ("name", "inn", "reg_no")


@admin.register(Veterinarian)
class VeterinarianAdmin(admin.ModelAdmin):
    list_display = ("last_name", 'first_name', 'org_name', "license_no")
    search_fields = ("last_name", "first_name", "org_name", "license_no")


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ("person", "organization")
    search_fields = ("person__last_name", "organization__name")
