from django.urls import path
from .views import upload_customers_view, customer_list_view, run_risk_scoring_view, churn_dashboard_view, high_risk_focus_view


urlpatterns = [
    path('upload/', upload_customers_view, name='customer_upload'),
    path('list/', customer_list_view, name='customer_list'),
    path("churn/run/", run_risk_scoring_view, name="run_churn_scoring"),
    path("churn/", churn_dashboard_view, name="churn_dashboard"),
    path("churn/high-risk/", high_risk_focus_view, name="high_risk_focus"),

]
