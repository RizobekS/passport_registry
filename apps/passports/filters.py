import django_filters as df
from .models import Passport
from apps.common.models import Breed, Region

class PassportFilter(df.FilterSet):
    status = df.ChoiceFilter(choices=Passport.Status.choices, label='Статус')
    year = df.NumberFilter(field_name='issue_date', lookup_expr='year', label='Год')
    breed = df.ModelChoiceFilter(field_name='horse__breed', queryset=Breed.objects.all(), to_field_name='id', label='Порода')
    region = df.ModelChoiceFilter(field_name='horse__place_of_birth', queryset=Region.objects.all(), to_field_name='id', label='Регион')
    microchip = df.CharFilter(field_name='horse__microchip', lookup_expr='icontains', label='Микрочип')
    class Meta:
        model = Passport
        fields = ["status", "year", "breed", "region", "microchip"]
