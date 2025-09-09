# apps/passports/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.horses.models import Horse
from .models import Passport

@receiver(post_save, sender=Horse)
def sync_passport_barcode_on_microchip_change(sender, instance: Horse, **kwargs):
    # Если у лошади есть паспорт — синхронизируем barcode_value = microchip
    try:
        p = instance.passport
    except Passport.DoesNotExist:
        return

    if not instance.microchip:
        return

    if p.barcode_value != instance.microchip:
        p.barcode_value = instance.microchip
        # Если хранишь изображения, перегенерируем
        p.generate_codes()
        p.save(update_fields=["barcode_value", "barcode_image", "qr_image"])
