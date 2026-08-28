from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health),
    path("dashboard/", views.dashboard),
    path("locations/", views.locations),
    path("map/risk/", views.map_risk),
    path("sensors/", views.sensors),
    path("sensors/ingest/", views.sensor_ingest),
    path("weather/", views.weather),
    path("risk/", views.risks),
    path("risk/<int:location_id>/", views.risk_detail),
    path("risk/predict/", views.predict),
    path("alerts/", views.alerts),
    path("alerts/<int:pk>/resolve/", views.resolve_alert),
    path("analytics/risk-trend/", views.trend),
]
