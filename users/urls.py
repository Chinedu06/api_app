from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "users"


router = DefaultRouter()
# registers endpoints under /operators/profile/
router.register(r'operators/profile', views.SupplierProfileViewSet, basename='operator-profile')

urlpatterns = [
    path('', views.index, name='user_index'),

    # Operator-only authentication endpoints
    path('operators/signup/', views.OperatorRegisterView.as_view(), name='operator-register'),
    path('operators/login/', views.OperatorLoginView.as_view(), name='operator-login'),

    # include viewset router urls at this path
    path('', include(router.urls)),
]
