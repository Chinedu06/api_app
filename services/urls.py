from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, PackageViewSet

app_name = "services"

router = DefaultRouter()
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"packages", PackageViewSet, basename="package")

urlpatterns = router.urls
