import csv
import io
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.timezone import now

from .forms import CustomerUploadForm
from .models import Customer, ChurnPrediction
from .risk_engine import calculate_churn_risk
from .recommendations import recommend_action
from .trends import analyze_trend, calculate_days_in_risk
from .analytics import risk_level_distribution, revenue_at_risk_chart, trend_overview


def generate_churn_predictions(tenant):
    customers = Customer.objects.filter(tenant=tenant)

    for customer in customers:
        score, level, reasons = calculate_churn_risk(customer)
        monthly_spend = customer.monthly_spend or 0
        revenue_at_risk = score * monthly_spend
        action = recommend_action(customer, level, reasons)

        last_prediction = (
            ChurnPrediction.objects
            .filter(customer=customer)
            .order_by("-created_at")
            .first()
        )

        prev_score = last_prediction.risk_score if last_prediction else None
        trend, early_warning = analyze_trend(prev_score, score)

        first_seen = (
            ChurnPrediction.objects
            .filter(customer=customer)
            .order_by("created_at")
            .first()
        )

        days_in_risk = calculate_days_in_risk(
            first_seen.created_at if first_seen else None
        )

        ChurnPrediction.objects.create(
            customer=customer,
            tenant=tenant,
            risk_score=score,
            risk_level=level,
            reasons=reasons,
            revenue_at_risk=revenue_at_risk,
            recommended_action=action,
            risk_trend=trend,
            early_warning=early_warning,
            days_in_risk=days_in_risk,
        )

@never_cache
@login_required
def upload_customers_view(request):
    if request.method == "POST":
        form = CustomerUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']

            try:
                decoded = file.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(decoded))
                raw_fieldnames = reader.fieldnames or []
                normalized_fieldnames = [normalize_csv_header(name) for name in raw_fieldnames]
                required_columns = {"external_id"}
                missing_columns = required_columns - set(normalized_fieldnames)
                if missing_columns:
                    messages.error(
                        request,
                        "Missing required columns: "
                        + ", ".join(sorted(missing_columns))
                    )
                    return render(request, "customers/upload.html", {"form": form})

                count = 0
                skipped = 0

                for row in reader:
                    normalized_row = {
                        normalize_csv_header(key): value
                        for key, value in row.items()
                    }
                    external_id = (normalized_row.get("external_id") or "").strip()
                    if not external_id:
                        skipped += 1
                        continue

                    Customer.objects.update_or_create(
                        tenant=request.tenant,
                        external_id=external_id,
                        defaults={
                            "email": normalized_row.get("email"),
                            "signup_date": parse_date(normalized_row.get("signup_date")),
                            "last_active_date": parse_date(normalized_row.get("last_active_date")),
                            "subscription_type": normalized_row.get("subscription_type"),
                            "monthly_spend": safe_float(normalized_row.get("monthly_spend")),
                            "feature_usage_score": safe_float(
                                normalized_row.get("feature_usage_score")
                            ),
                            "churned": parse_bool(normalized_row.get("churned")),
                        }
                    )
                    count += 1

                generate_churn_predictions(request.tenant)
                if skipped:
                    messages.warning(
                        request,
                        f"Skipped {skipped} rows missing external_id."
                    )
                messages.success(
                    request,
                    f"Successfully imported {count} customers and updated churn risk."
                )
                return redirect("churn_dashboard")

            except Exception as e:
                messages.error(request, f"Error parsing CSV: {e}")

    else:
        form = CustomerUploadForm()

    return render(request, "customers/upload.html", {"form": form})

@never_cache
@login_required
def run_risk_scoring_view(request):
    generate_churn_predictions(request.tenant)

    messages.success(request, "Churn trends updated successfully.")
    return redirect("churn_dashboard")


@never_cache
@login_required
def churn_dashboard_view(request):
    from django.db.models import Max

    latest_ids = (
        ChurnPrediction.objects
        .filter(tenant=request.tenant)
        .values("customer_id")
        .annotate(latest_id=Max("id"))
        .values_list("latest_id", flat=True)
    )

    predictions = (
        ChurnPrediction.objects
        .filter(id__in=latest_ids)
        .select_related("customer")
        .order_by("-risk_score")
    )

    total_revenue_at_risk = sum(p.revenue_at_risk for p in predictions)
    has_early_warnings = any(p.early_warning for p in predictions)

    context = {
        "predictions": predictions,
        "total_revenue_at_risk": total_revenue_at_risk,
        "risk_chart": risk_level_distribution(predictions),
        "revenue_chart": revenue_at_risk_chart(predictions),
        "trend_chart": trend_overview(predictions),
        "last_updated": now(),
        "has_early_warnings": has_early_warnings
    }

    return render(request, "customers/churn_dashboard.html", context)

@never_cache
@login_required
def high_risk_focus_view(request):
    predictions = (
        ChurnPrediction.objects
        .filter(
            tenant=request.tenant,
            risk_level="high"
        )
        .select_related("customer")
        .order_by("-revenue_at_risk")
    )

    return render(
        request,
        "customers/high_risk_focus.html",
        {"predictions": predictions}
    )

@never_cache
@login_required
def customer_list_view(request):
    customers = Customer.objects.filter(tenant=request.tenant)
    return render(request, "customers/list.html", {"customers": customers})


@never_cache
@login_required
def customer_detail_view(request, customer_id):
    # Mock data; replace with real lookup later
    customer = {
        "id": customer_id,
        "name": "Acme Health",
        "risk_level": "High",
        "risk_score": 82,
        "at_risk_since": "2025-03-03",
        "plan_name": "Pro",
        "monthly_revenue": "$12,400 MRR",
        "confidence": "High",
    }

    risk_reasons = [
        "Login frequency dropped 62% in the last 30 days",
        "Core feature “Exports” has never been used",
        "Last activity was 21 days ago",
        "Two invoices paid late this quarter",
    ]

    risk_reduction = [
        "If this customer logs in twice this week, churn risk drops to ~42%",
        "Completing onboarding reduces churn risk by ~31%",
        "Schedule a success review to surface quick wins",
    ]

    timeline = [
        "Jan 10 – Account created",
        "Jan 12 – First login",
        "Jan 14 – Onboarding started",
        "Feb 10 – Usage decline begins",
        "Feb 22 – Last activity",
        "Mar 03 – High churn risk detected",
    ]

    actions = [
        "Personal email from founder",
        "Offer a 15-minute onboarding call",
    ]

    context = {
        "customer": customer,
        "risk_reasons": risk_reasons,
        "risk_reduction": risk_reduction,
        "timeline": timeline,
        "actions": actions,
    }

    return render(request, "customers/customer_detail.html", context)


@never_cache
@login_required
def at_risk_customers_view(request):
    customers = [
        {
            "id": 101,
            "name": "Acme Health",
            "risk_level": "High",
            "risk_score": 82,
            "monthly_revenue": "€12,400",
            "reason": "Usage dropped 35% vs last month",
        },
        {
            "id": 102,
            "name": "OrbitSoft",
            "risk_level": "High",
            "risk_score": 76,
            "monthly_revenue": "€9,800",
            "reason": "NPS fell to 4 — waiting on support fix",
        },
        {
            "id": 103,
            "name": "BrightBank",
            "risk_level": "Medium",
            "risk_score": 61,
            "monthly_revenue": "€7,200",
            "reason": "Executive sponsor left",
        },
        {
            "id": 104,
            "name": "Northwind Retail",
            "risk_level": "Medium",
            "risk_score": 58,
            "monthly_revenue": "€6,450",
            "reason": "Late invoices flagged",
        },
        {
            "id": 105,
            "name": "Pioneer Labs",
            "risk_level": "Medium",
            "risk_score": 54,
            "monthly_revenue": "€5,900",
            "reason": "Support tickets rising week-over-week",
        },
    ]

    context = {"customers": customers}
    return render(request, "customers/at_risk_customers.html", context)


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except:
        return None


def safe_float(value):
    try:
        return float(value)
    except:
        return None


def parse_bool(value):
    if not value:
        return False
    return value.lower() in ("1", "true", "yes")


def normalize_csv_header(value):
    if value is None:
        return ""
    return value.strip().lstrip("\ufeff").lower()
