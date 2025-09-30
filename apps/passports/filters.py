import django_filters as df
from django.db.models import Q

from .models import Passport
from apps.common.models import Breed, Region
from apps.parties.models import Organization

OWNER_KIND_CHOICES = (
    ("PHYS", "Физическое лицо"),
    ("ORG_STATE", "Юридическое лицо (гос)"),
    ("ORG_PRIVATE", "Юридическое лицо (частное)"),
)

class PassportFilter(df.FilterSet):
    status = df.ChoiceFilter(choices=Passport.Status.choices, label='Статус')
    year = df.NumberFilter(field_name='issue_date', lookup_expr='year', label='Год')
    breed = df.ModelChoiceFilter(field_name='horse__breed', queryset=Breed.objects.all(), to_field_name='id', label='Порода')
    region = df.ModelChoiceFilter(field_name='horse__place_of_birth', queryset=Region.objects.all(), to_field_name='id', label='Регион')
    microchip = df.CharFilter(field_name='horse__microchip', lookup_expr='icontains', label='Микрочип')
    owner_kind = df.ChoiceFilter(
        label="Тип владельца",
        choices=OWNER_KIND_CHOICES,
        method="filter_owner_kind",
    )
    passport_kind = df.ChoiceFilter(
        label="Тип паспорта",
        choices=(("", "Все"), ("import", "Паспорт старого формата"), ("new", "Паспорт нового формата")),
        method="filter_passport_kind"
    )

    def filter_owner_kind(self, qs, name, value):
        """
        PHYS        -> у владельца заполнено person (а organization пуст)
        ORG_STATE   -> organization.org_type = STATE
        ORG_PRIVATE -> organization.org_type = PRIVATE
        """
        if value == "PHYS":
            return qs.filter(horse__owner_current__person__isnull=False)
        elif value == "ORG_STATE":
            return qs.filter(
                horse__owner_current__organization__isnull=False,
                horse__owner_current__organization__org_type=Organization.OrgType.STATE,
            )
        elif value == "ORG_PRIVATE":
            return qs.filter(
                horse__owner_current__organization__isnull=False,
                horse__owner_current__organization__org_type=Organization.OrgType.PRIVATE,
            )
        return qs

    def filter_passport_kind(self, qs, name, value):
        if value == "import":
            return qs.filter(old_passport_number__isnull=False).exclude(old_passport_number__exact="")
        if value == "new":
            return qs.filter(Q(old_passport_number__isnull=True) | Q(old_passport_number__exact=""))
        return qs

    class Meta:
        model = Passport
        fields = ["status", "year", "breed", "region", "microchip", "owner_kind", "passport_kind"]
