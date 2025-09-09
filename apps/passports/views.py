from datetime import timedelta

from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, render
from django.utils.timezone import now
from django.views.generic import ListView, TemplateView
from django.db.models import Count, Prefetch

from config.settings import PUBLIC_BASE_URL
from web_project import TemplateLayout
from .models import Passport
from .filters import PassportFilter
from apps.vet.models import Vaccination, LabTest
from ..parties.models import Organization


class PassportListView(ListView):
    model = Passport
    template_name = "passports/list.html"
    context_object_name = "items"
    paginate_by = 25

    def get_queryset(self):
        qs = (Passport.objects
              .select_related("horse", "horse__breed", "horse__place_of_birth"))
        self.filterset = PassportFilter(self.request.GET, queryset=qs)
        return self.filterset.qs.order_by("-issue_date", "-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter"] = self.filterset
        return TemplateLayout().init(ctx)


class RegistryDashboardView(TemplateView):
    template_name = "dashboard/registry_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # База с related’ами (чтобы не ддосить БД)
        qs = (Passport.objects
              .select_related(
                  "horse",
                  "horse__breed",
                  "horse__place_of_birth",
                  "horse__owner_current",
                  "horse__owner_current__organization",
              ))

        ctx["kpi"] = {
            "total": qs.count(),
            "issued": qs.filter(status__in=[Passport.Status.ISSUED, Passport.Status.REISSUED]).count(),
            "revoked": qs.filter(status=Passport.Status.REVOKED).count(),
        }

        ctx["by_status"] = list(qs.values("status").annotate(c=Count("id")).order_by("-c"))
        ctx["by_breed"]  = list(qs.values("horse__breed__name").annotate(c=Count("id")).order_by("-c")[:10])
        ctx["by_region"] = list(qs.values("horse__place_of_birth__name").annotate(c=Count("id")).order_by("-c")[:10])

        phys        = qs.filter(horse__owner_current__person__isnull=False).count()
        org_state   = qs.filter(horse__owner_current__organization__org_type=Organization.OrgType.STATE).count()
        org_private = qs.filter(horse__owner_current__organization__org_type=Organization.OrgType.PRIVATE).count()
        ctx["by_owner_kind"] = [
            {"label": "Физические лица", "value": phys},
            {"label": "Юр. лица (гос)", "value": org_state},
            {"label": "Юр. лица (частные)", "value": org_private},
        ]

        # Динамика за 30 дней
        start = now().date() - timedelta(days=29)
        daily = (
            qs.filter(issue_date__gte=start)
              .annotate(d=TruncDate("issue_date"))
              .values("d").annotate(c=Count("id")).order_by("d")
        )
        ctx["by_day"] = [{"d": x["d"].strftime("%d.%m"), "c": x["c"]} for x in daily]

        return TemplateLayout().init(ctx)


def public_passport(request, qr_id):
    public_base_url = PUBLIC_BASE_URL
    p = get_object_or_404(
        Passport.objects.select_related('horse', 'horse__breed', 'horse__color', 'horse__place_of_birth')
        .prefetch_related(
            Prefetch('horse__vaccinations',
                     queryset=Vaccination.objects.select_related('vaccine', 'veterinarian__person').order_by('-date')),
            Prefetch('horse__lab_tests',
                     queryset=LabTest.objects.select_related('test_type', 'veterinarian__person').order_by('-date')),
        ),
        qr_public_id=qr_id,
        status__in=[Passport.Status.ISSUED, Passport.Status.REISSUED]
    )
    return render(request, 'passports/public_card.html', {'p': p, 'public_base_url': public_base_url})
