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

                count = 0

                for row in reader:
                    Customer.objects.update_or_create(
                        tenant=request.tenant,
                        external_id=row.get("external_id"),
                        defaults={
                            "email": row.get("email"),
                            "signup_date": parse_date(row.get("signup_date")),
                            "last_active_date": parse_date(row.get("last_active_date")),
                            "subscription_type": row.get("subscription_type"),
                            "monthly_spend": safe_float(row.get("monthly_spend")),
                            "feature_usage_score": safe_float(row.get("feature_usage_score")),
                            "churned": parse_bool(row.get("churned")),
                        }
                    )
                    count += 1

                generate_churn_predictions(request.tenant)
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
