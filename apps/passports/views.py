from datetime import timedelta, date

from django.db.models.functions import TruncDate, TruncMonth
from django.shortcuts import get_object_or_404, render
from django.utils.timezone import now
from django.views.generic import ListView, TemplateView
from django.db.models import Count, Prefetch, DateField

from config.settings import PUBLIC_BASE_URL
from web_project import TemplateLayout
from .models import Passport
from .filters import PassportFilter
from apps.vet.models import Vaccination, LabTest
from ..horses.models import Horse
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

        # KPI
        total = qs.count()
        issued = qs.filter(status__in=[Passport.Status.ISSUED, Passport.Status.REISSUED]).count()
        revoked = qs.filter(status=Passport.Status.REVOKED).count()
        ctx["kpi"] = {"total": total, "issued": issued, "revoked": revoked}

        # Статусы с человекочитаемыми лейблами
        status_map = dict(Passport.Status.choices)  # {"DRAFT":"Черновик", ...}
        status_raw = qs.values("status").annotate(c=Count("id")).order_by("-c")
        ctx["by_status"] = [
            {"status": x["status"], "label": status_map.get(x["status"], x["status"]), "c": x["c"]}
            for x in status_raw
        ]

        # ТОП породы / регионы рождения (как было)
        ctx["by_breed"]  = list(qs.values("horse__breed__name").annotate(c=Count("id")).order_by("-c")[:10])
        ctx["by_region"] = list(qs.values("horse__place_of_birth__name").annotate(c=Count("id")).order_by("-c")[:10])

        # НОВОЕ: срез по ТИПАМ ЛОШАДЕЙ (sport/service/expo)
        type_map = dict(Horse.HORSE_TYPE_CHOICES)  # {"SPORT":"Спортивная", ...}
        type_raw = qs.values("horse__horse_type").annotate(c=Count("id")).order_by("-c")
        ctx["by_horse_type"] = [
            {"code": (x["horse__horse_type"] or ""), "label": type_map.get(x["horse__horse_type"], "Не указан"), "c": x["c"]}
            for x in type_raw
        ]

        # Срез по типу владельца (как было)
        phys        = qs.filter(horse__owner_current__person__isnull=False).count()
        org_state   = qs.filter(horse__owner_current__organization__org_type=Organization.OrgType.STATE).count()
        org_private = qs.filter(horse__owner_current__organization__org_type=Organization.OrgType.PRIVATE).count()
        ctx["by_owner_kind"] = [
            {"label": "Физические лица", "value": phys},
            {"label": "Юр. лица (гос)", "value": org_state},
            {"label": "Юр. лица (частные)", "value": org_private},
        ]

        # Динамика за 30 дней (с НОЛЕФИЛЛЕНИЕМ)
        start = now().date() - timedelta(days=29)
        daily_q = (qs.filter(issue_date__gte=start)
                     .annotate(d=TruncDate("issue_date"))
                     .values("d").annotate(c=Count("id")).order_by("d"))
        # заполняем отсутствующие дни нулями
        day_index = {x["d"]: x["c"] for x in daily_q}
        by_day = []
        for i in range(30):
            d = start + timedelta(days=i)
            by_day.append({"d": d.strftime("%d.%m"), "c": int(day_index.get(d, 0))})
        ctx["by_day"] = by_day

        # НОВОЕ: Динамика по месяцам (последние 12 мес) с нолефиллом
        today = now().date().replace(day=1)
        start_m = (today - timedelta(days=365)).replace(day=1)

        monthly_q = (
            qs.filter(issue_date__isnull=False, issue_date__gte=start_m)
            .annotate(m=TruncMonth("issue_date", output_field=DateField()))  # ← форсируем DATE
            .values("m").annotate(c=Count("id")).order_by("m")
        )

        month_index = {x["m"]: x["c"] for x in monthly_q}

        by_month = []
        cur = start_m
        for _ in range(12):
            label = cur.strftime("%m.%y")  # например 09.25
            by_month.append({"m": label, "c": int(month_index.get(cur, 0))})
            # шаг на следующий месяц
            if cur.month == 12:
                cur = date(cur.year + 1, 1, 1)
            else:
                cur = date(cur.year, cur.month + 1, 1)
        ctx["by_month"] = by_month

        # ===== ВЛАДЕЛЬЦЫ: физ, гос-орг, частные =====
        persons_q = (
            qs.filter(horse__owner_current__person__isnull=False)
            .values(
                "horse__owner_current__person__id",
                "horse__owner_current__person__last_name",
                "horse__owner_current__person__first_name",
                "horse__owner_current__person__middle_name",
            )
            .annotate(c=Count("id")).order_by("-c")
        )

        owners_person = []
        for x in persons_q:
            ln = (x["horse__owner_current__person__last_name"] or "").strip()
            fn = (x["horse__owner_current__person__first_name"] or "").strip()
            mn = (x["horse__owner_current__person__middle_name"] or "").strip()
            label = " ".join([p for p in (ln, fn, mn) if p]) or "—"
            owners_person.append({
                "id": x["horse__owner_current__person__id"],
                "label": label,
                "kind": "PERSON",
                "count": x["c"],
            })

        # Гос. организации
        state_q = (
            qs.filter(horse__owner_current__organization__org_type=Organization.OrgType.STATE)
            .values(
                "horse__owner_current__organization__id",
                "horse__owner_current__organization__name",
            )
            .annotate(c=Count("id")).order_by("-c")
        )
        owners_state = [{
            "id": x["horse__owner_current__organization__id"],
            "label": x["horse__owner_current__organization__name"] or "—",
            "kind": "STATE",
            "count": x["c"],
        } for x in state_q]

        # Частные организации
        private_q = (
            qs.filter(horse__owner_current__organization__org_type=Organization.OrgType.PRIVATE)
            .values(
                "horse__owner_current__organization__id",
                "horse__owner_current__organization__name",
            )
            .annotate(c=Count("id")).order_by("-c")
        )
        owners_private = [{
            "id": x["horse__owner_current__organization__id"],
            "label": x["horse__owner_current__organization__name"] or "—",
            "kind": "PRIVATE",
            "count": x["c"],
        } for x in private_q]

        # Общий массив для фронта
        ctx["owners"] = owners_person + owners_state + owners_private

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
