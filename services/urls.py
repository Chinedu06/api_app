from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, PackageViewSet

app_name = "services"

router = DefaultRouter()
router.register(r"", ServiceViewSet, basename="service")      # /services/
router.register(r"packages", PackageViewSet, basename="package")

urlpatterns = router.urls
