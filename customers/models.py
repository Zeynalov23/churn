from django.db import models
from accounts.models import Tenant


class Customer(models.Model):
    """
    Customer record imported by each tenant (company).
    This is the main dataset for churn prediction.
    """

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="customers"
    )

    external_id = models.CharField(max_length=255)   # SaaS system customer ID
    email = models.EmailField(null=True, blank=True)
    signup_date = models.DateField(null=True, blank=True)
    last_active_date = models.DateField(null=True, blank=True)

    subscription_type = models.CharField(max_length=100, null=True, blank=True)
    monthly_spend = models.FloatField(null=True, blank=True)
    feature_usage_score = models.FloatField(null=True, blank=True)

    churned = models.BooleanField(default=False)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "external_id")

    def __str__(self):
        return f"{self.external_id} ({self.tenant.name})"

class ChurnPrediction(models.Model):
    customer = models.ForeignKey(
        "Customer",
        on_delete=models.CASCADE,
        related_name="churn_predictions"
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="churn_predictions"
    )

    risk_score = models.FloatField()
    risk_level = models.CharField(max_length=20)

    reasons = models.JSONField()

    revenue_at_risk = models.FloatField(default=0.0)
    recommended_action = models.CharField(
        max_length=255,
        default="No action needed"
    )

    # 🔥 NEW FIELDS
    risk_trend = models.CharField(
        max_length=20,
        default="new"  # new / improving / stable / worsening
    )
    early_warning = models.BooleanField(default=False)
    days_in_risk = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
