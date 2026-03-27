from django.urls import path
from .views import CheckInView

urlpatterns = [
    path("checkin/<uuid:token>/", CheckInView.as_view(), name="checkin"),
]
