from django.urls import path
from .views import DestinationListView

app_name = "destinations"

urlpatterns = [
    path("", DestinationListView.as_view(), name="destination-list"),
]