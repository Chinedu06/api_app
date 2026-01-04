from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, PackageViewSet, ServiceCalendarView

app_name = "services"

# Define urlpatterns first
urlpatterns = [
    path("<slug:slug>/calendar/", ServiceCalendarView.as_view(), name="service-calendar"),
]

# Set up the router
router = DefaultRouter()
router.register(r"", ServiceViewSet, basename="service")          # 👈 root
router.register(r"packages", PackageViewSet, basename="package")

# Add router URLs to urlpatterns
urlpatterns += router.urls


