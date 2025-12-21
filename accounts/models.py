from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Tenant(models.Model):
    """
    This is a company/client, who is using our app
    """

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # simple plan field for the future
    PLAN_FREE = "free"
    PLAN_PRO = "pro"
    PLAN_ENTERPRISE = "enterprise"
    PLAN_CHOICES = [
        (PLAN_FREE, "Free"),
        (PLAN_PRO, "Pro"),
        (PLAN_ENTERPRISE, "Enterprise"),
    ]
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default=PLAN_FREE,
    )

    def __str__(self):
        return self.name

class User(AbstractUser):
    """
    Custom user model bound to a tenant (multi-tenant)
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True
    )

    # optional: simple role system
    ROLE_ADMIN = "admin"
    ROLE_ANALYST = "analyst"
    ROLE_VIEWER = "viewer"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_ANALYST, "Analyst"),
        (ROLE_VIEWER, "Viewer"),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_ADMIN,
    )

    def __str__(self):
        return f"{self.username} ({self.tenant})" if self.tenant else self.username
    
    