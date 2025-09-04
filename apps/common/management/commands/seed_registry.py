from django.core.management.base import BaseCommand
from apps.common.models import Region, Breed, Color, Vaccine, LabTestType
from apps.parties.models import Person, Veterinarian, Owner
from apps.horses.models import Horse
from apps.passports.models import Passport
from datetime import date

class Command(BaseCommand):
    help = "Seed minimal data for demo"

    def handle(self, *args, **kwargs):
        r, _ = Region.objects.get_or_create(name="Ташкент")
        b, _ = Breed.objects.get_or_create(name="Чистокровная верховая")
        c, _ = Color.objects.get_or_create(name="Гнедая")
        Vaccine.objects.get_or_create(name="Грипп (инактив.)", manufacturer="VetCo")
        LabTestType.objects.get_or_create(name="РТП на инфекц. анемию")

        p, _ = Person.objects.get_or_create(last_name="Иванов", first_name="Пётр")
        vet, _ = Veterinarian.objects.get_or_create(person=p, defaults={"license_no":"VET-001"})
        owner, _ = Owner.objects.get_or_create(person=p)

        h, _ = Horse.objects.get_or_create(
            name="Альтаир",
            defaults=dict(birth_date=date(2021,5,20), breed=b, color=c,
                          place_of_birth=r, microchip="123456789012345",
                          owner_current=owner)
        )
        Passport.objects.get_or_create(horse=h, defaults={"status": Passport.Status.DRAFT})
        self.stdout.write(self.style.SUCCESS("Seed done"))
