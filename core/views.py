from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def churn_dashboard_view(request):
    metrics = {
        "customers_at_risk": 24,
        "revenue_at_risk": "$82,500",
        "new_risks": 5,
        "resolved_risks": 3,
    }

    focus_customers = [
        {
            "name": "Acme Health",
            "risk_level": "High",
            "monthly_revenue": "$12,400",
            "reason": "Usage dropped 35% vs last month",
        },
        {
            "name": "OrbitSoft",
            "risk_level": "High",
            "monthly_revenue": "$9,800",
            "reason": "NPS fell to 4 — waiting on support fix",
        },
        {
            "name": "BrightBank",
            "risk_level": "Medium",
            "monthly_revenue": "$7,200",
            "reason": "Executive sponsor left the account",
        },
        {
            "name": "Northwind Retail",
            "risk_level": "Medium",
            "monthly_revenue": "$6,450",
            "reason": "Churn risk model flagged late invoices",
        },
        {
            "name": "Pioneer Labs",
            "risk_level": "Medium",
            "monthly_revenue": "$5,900",
            "reason": "Support tickets trending up week-over-week",
        },
    ]

    trend_points = [
        {"label": "Week 1", "value": 18},
        {"label": "Week 2", "value": 21},
        {"label": "Week 3", "value": 19},
        {"label": "Week 4", "value": 17},
    ]

    weekly_summary = (
        "Great momentum this week: churn risk volume is trending down, "
        "and resolved cases outpaced new risks. Keep the focus on the top five accounts "
        "to lock in renewals."
    )

    context = {
        "metrics": metrics,
        "focus_customers": focus_customers[:5],
        "trend_points": trend_points,
        "weekly_summary": weekly_summary,
    }

    return render(request, "core/home.html", context)
