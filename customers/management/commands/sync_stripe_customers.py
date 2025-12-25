from django.core.management.base import BaseCommand, CommandError

from customers.stripe_sync import fetch_stripe_customers_with_mrr, map_stripe_customers_to_internal


class Command(BaseCommand):
    help = "Fetch read-only Stripe customers and active subscriptions for churn analysis."

    def handle(self, *args, **options):
        try:
            stripe_customers = fetch_stripe_customers_with_mrr()
        except Exception as exc:  # pragma: no cover - operational path
            raise CommandError(str(exc))

        mapped_customers = map_stripe_customers_to_internal(stripe_customers)

        if not mapped_customers:
            self.stdout.write(self.style.WARNING("No Stripe customers returned."))
            return

        for customer in mapped_customers:
            name = customer.get("name") or "(no name)"
            email = customer.get("email") or "(no email)"
            mrr = customer.get("mrr") or 0.0
            plan = customer.get("plan") or "Unknown plan"
            matched = (
                f"linked to internal customer #{customer['matched_customer_id']}"
                if customer.get("matched_customer_id")
                else "no internal match"
            )

            self.stdout.write(f"{name} | {email} | {plan} | MRR: {mrr} | {matched}")
