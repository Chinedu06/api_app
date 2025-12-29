from django.urls import path
from .views import (
    ServiceListView,
    ServiceDetailView,
    PackageListView,
    PackageDetailView,
)

app_name = "services"

urlpatterns = [
    # Services
    path("", ServiceListView.as_view(), name="service-list"),
    path("<slug:slug>/", ServiceDetailView.as_view(), name="service-detail"),

    # Packages
    path("packages/", PackageListView.as_view(), name="package-list"),
    path("packages/<int:id>/", PackageDetailView.as_view(), name="package-detail"),
]
