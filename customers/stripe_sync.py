import os
from typing import Dict, List, Optional

import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _get_stripe_api_key() -> str:
    api_key = os.getenv("STRIPE_SECRET_KEY") or getattr(settings, "STRIPE_SECRET_KEY", None)
    if not api_key:
        raise ImproperlyConfigured("STRIPE_SECRET_KEY is not configured for Stripe sync.")
    return api_key


def _format_mrr(amount_cents: Optional[int], interval: Optional[str], interval_count: Optional[int], quantity: int) -> float:
    if amount_cents is None:
        return 0.0
    interval = interval or "month"
    interval_count = interval_count or 1
    monthly_multiplier = interval_count if interval == "month" else interval_count * 12 if interval == "year" else interval_count
    monthly_amount = (amount_cents / 100.0) / monthly_multiplier
    return round(monthly_amount * quantity, 2)


def fetch_stripe_customers_with_mrr(limit: int = 100) -> List[Dict]:
    stripe.api_key = _get_stripe_api_key()

    customers = stripe.Customer.list(limit=limit).auto_paging_iter()
    customer_index: Dict[str, Dict] = {}

    for customer in customers:
        customer_index[customer.id] = {
            "stripe_customer_id": customer.id,
            "name": customer.get("name") or "",
            "email": customer.get("email") or "",
            "mrr": 0.0,
            "plan": None,
        }

    subscriptions = stripe.Subscription.list(status="active", limit=limit).auto_paging_iter()
    for subscription in subscriptions:
        customer_id = subscription.get("customer")
        if customer_id not in customer_index:
            customer_index[customer_id] = {
                "stripe_customer_id": customer_id,
                "name": "",
                "email": "",
                "mrr": 0.0,
                "plan": None,
            }

        total_mrr = 0.0
        plan_name = None

        for item in subscription.get("items", {}).get("data", []):
            price = item.get("price") or {}
            quantity = item.get("quantity") or 1
            plan_name = price.get("nickname") or price.get("product") or plan_name
            total_mrr += _format_mrr(
                amount_cents=price.get("unit_amount"),
                interval=price.get("recurring", {}).get("interval") if price.get("recurring") else None,
                interval_count=price.get("recurring", {}).get("interval_count") if price.get("recurring") else None,
                quantity=quantity,
            )

        customer_index[customer_id]["mrr"] += round(total_mrr, 2)
        if plan_name and not customer_index[customer_id]["plan"]:
            customer_index[customer_id]["plan"] = plan_name

    return list(customer_index.values())


def map_stripe_customers_to_internal(stripe_customers: List[Dict]) -> List[Dict]:
    from customers.models import Customer  # Imported lazily to avoid circular deps

    mapped = []
    for entry in stripe_customers:
        email = entry.get("email") or ""
        name = entry.get("name") or ""

        match = None
        if email:
            match = Customer.objects.filter(email__iexact=email).first()
        if not match and name:
            match = Customer.objects.filter(external_id__iexact=name).first()

        mapped.append(
            {
                "stripe_customer_id": entry.get("stripe_customer_id"),
                "name": name or email or entry.get("stripe_customer_id"),
                "email": email,
                "mrr": entry.get("mrr", 0.0),
                "plan": entry.get("plan"),
                "matched_customer_id": match.id if match else None,
                "matched_customer_name": str(match) if match else None,
            }
        )

    return mapped
