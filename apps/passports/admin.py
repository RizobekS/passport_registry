from django.contrib import admin, messages
from django.utils.timezone import now
from .models import Passport
from .services import render_passport_pdf

@admin.register(Passport)
class PassportAdmin(admin.ModelAdmin):
    list_display = ("number", "horse", "status", "issue_date", "version", "created_at")
    list_filter = ("status", "issue_date", "version")
    search_fields = ("number", "horse__name", "horse__registry_no", "horse__microchip")
    readonly_fields = ("barcode_image", "qr_image", "pdf_file", "qr_public_id", "created_at")

    fieldsets = (
        ("Паспорт", {
            "classes": ("tab", "tab-main"),
            "fields": ("number", "horse", "status", "version", "issue_date"),
        }),
        ("Коды", {
            "classes": ("tab", "tab-codes"),
            "fields": ("barcode_value", "barcode_image", "qr_public_id", "qr_image"),
            "description": "Штрих-код и QR генерируются автоматически при выпуске.",
        }),
        ("Файл", {
            "classes": ("tab", "tab-file"),
            "fields": ("pdf_file",),
        }),
        ("Аннулирование / Служебное", {
            "classes": ("tab", "tab-service"),
            "fields": ("revoked_reason", "created_at"),
        }),
    )

    actions = ["issue_passport", "revoke_passport", "reissue_passport"]

    @admin.action(description="Выпустить паспорт (генерировать штрих/QR и PDF)")
    def issue_passport(self, request, queryset):
        ok = 0
        for p in queryset:
            if p.status != Passport.Status.DRAFT:
                continue
            p.barcode_value = p.barcode_value or p.horse.microchip or p.horse.registry_no
            p.generate_codes()
            render_passport_pdf(p)
            p.status = Passport.Status.ISSUED
            p.issue_date = p.issue_date or now().date()
            p.save()
            ok += 1
        messages.success(request, f"Выпущено: {ok}")

    @admin.action(description="Аннулировать паспорт")
    def revoke_passport(self, request, queryset):
        cnt = queryset.update(status=Passport.Status.REVOKED)
        messages.warning(request, f"Аннулировано: {cnt}")

    @admin.action(description="Переоформить (версию +1, статус Переоформлен)")
    def reissue_passport(self, request, queryset):
        ok = 0
        for p in queryset:
            p.version += 1
            p.status = Passport.Status.REISSUED
            p.generate_codes()
            render_passport_pdf(p)
            p.issue_date = now().date()
            p.save()
            ok += 1
        messages.success(request, f"Переоформлено: {ok}")
