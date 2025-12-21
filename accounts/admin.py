from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Tenant, User


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "plan", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("plan",)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Tenant Info", {"fields": ("tenant", "role")}),
    )
    list_display = ("username", "email", "tenant", "role", "is_staff", "is_superuser")
    list_filter = ("tenant", "role", "is_staff", "is_superuser")
