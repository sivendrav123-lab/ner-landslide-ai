import json
import os
from datetime import timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from django.db.models import Avg
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

from .models import *
from .serializers import *
from .risk_engine import calculate_risk


NER_LOCATIONS = [
    ("Agartala", "Tripura", "West Tripura", 23.8315, 91.2868, 50, 18, .55),
    ("Guwahati", "Assam", "Kamrup", 26.1445, 91.7362, 55, 22, .70),
    ("Itanagar", "Arunachal Pradesh", "Papum Pare", 27.0844, 93.6053, 350, 28, .80),
    ("Gangtok", "Sikkim", "East Sikkim", 27.3389, 88.6065, 1650, 38, .90),
    ("Imphal", "Manipur", "Imphal West", 24.8170, 93.9368, 790, 24, .55),
    ("Kohima", "Nagaland", "Kohima", 25.6751, 94.1086, 1444, 35, .80),
    ("Aizawl", "Mizoram", "Aizawl", 23.7271, 92.7176, 1132, 40, .85),
    ("Shillong", "Meghalaya", "East Khasi Hills", 25.5788, 91.8933, 1496, 30, .70),
    ("Cherrapunji", "Meghalaya", "East Khasi Hills", 25.2840, 91.7220, 1484, 42, .90),
]


def action(level):
    return {
        "LOW": "Continue routine monitoring.",
        "MODERATE": "Increase monitoring frequency and verify local conditions.",
        "HIGH": "Issue a precautionary warning and notify responsible authorities.",
        "CRITICAL": "Trigger emergency early-warning protocol and immediate field verification.",
    }[level]


def ensure_locations():
    for d in NER_LOCATIONS:
        Location.objects.update_or_create(
            name=d[0], defaults=dict(state=d[1], district=d[2], latitude=d[3],
            longitude=d[4], elevation=d[5], slope_angle=d[6],
            geological_risk=d[7])
        )


def open_meteo(lat, lon):
    params = urlencode({
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,rain,wind_speed_10m",
        "hourly": "rain",
        "past_days": 7, "forecast_days": 1,
        "timezone": "Asia/Kolkata",
    })
    req = Request(
        "https://api.open-meteo.com/v1/forecast?" + params,
        headers={"User-Agent": "NER-Landslide-Intelligence/1.0"}
    )
    with urlopen(req, timeout=8) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_weather_for_location(location):
    data = open_meteo(location.latitude, location.longitude)
    current = data.get("current", {})
    rains = [float(x or 0) for x in data.get("hourly", {}).get("rain", [])]
    # past_days=7 plus today's hours; use completed/present observations for rolling totals.
    last24 = sum(rains[-24:]) if rains else float(current.get("rain", 0) or 0)
    last7 = sum(rains[:-1]) if len(rains) > 1 else last24
    rainfall_1h = float(current.get("rain", 0) or 0)
    return {
        "temperature": float(current.get("temperature_2m", 0) or 0),
        "humidity": float(current.get("relative_humidity_2m", 0) or 0),
        "rainfall_1h": rainfall_1h,
        "rainfall_24h": round(last24, 2),
        "rainfall_7d": round(last7, 2),
        "rainfall_intensity": rainfall_1h,
        "wind_speed": float(current.get("wind_speed_10m", 0) or 0),
    }


@api_view(["GET"])
def health(request):
    return Response({
        "success": True, "status": "online", "demo_data": False,
        "weather_source": "Open-Meteo", "sensor_mode": "ESP32/API ingestion",
    })


@api_view(["GET"])
def dashboard(request):
    ensure_locations()
    avg = round(float(RiskAssessment.objects.aggregate(x=Avg("risk_score"))["x"] or 0), 2)
    return Response({
        "success": True, "regional_risk": avg,
        "active_alerts": Alert.objects.filter(status="ACTIVE").count(),
        "monitored_locations": Location.objects.count(),
        "total_sensors": Sensor.objects.count(),
        "online_sensors": Sensor.objects.filter(status="ONLINE").count(),
        "offline_sensors": Sensor.objects.exclude(status="ONLINE").count(),
        "average_risk": avg,
        "critical_locations": RiskAssessment.objects.filter(risk_level="CRITICAL").values("location").distinct().count(),
    })


@api_view(["GET"])
def locations(request):
    ensure_locations()
    return Response(LocationSerializer(Location.objects.all(), many=True).data)


@api_view(["GET"])
def map_risk(request):
    ensure_locations()
    result = []
    for l in Location.objects.all():
        r = l.risks.order_by("-created_at").first()
        result.append({
            "location": l.name, "state": l.state, "latitude": l.latitude,
            "longitude": l.longitude, "risk_score": r.risk_score if r else None,
            "risk_level": r.risk_level if r else "NO DATA",
        })
    return Response(result)


@api_view(["GET"])
def sensors(request):
    return Response(SensorSerializer(
        Sensor.objects.select_related("location").all(), many=True
    ).data)


@api_view(["POST"])
@csrf_exempt
def sensor_ingest(request):
    # Real-device endpoint: POST {"sensor_id":"ESP32-01","sensor_type":"SOIL",
    # "location_id":1,"value":67.2,"unit":"%","battery_level":91}
    expected = os.environ.get("DEVICE_API_KEY")
    supplied = request.headers.get("X-Device-Key")
    if expected and supplied != expected:
        return Response({"error": "Invalid device key"}, status=401)
    try:
        p = json.loads(request.body.decode("utf-8"))
        sid = str(p["sensor_id"])
        loc = Location.objects.get(pk=int(p["location_id"]))
        sensor, _ = Sensor.objects.update_or_create(
            sensor_id=sid,
            defaults={
                "sensor_type": str(p.get("sensor_type", "CUSTOM")).upper(),
                "location": loc, "value": float(p["value"]),
                "unit": str(p.get("unit", "")),
                "status": "ONLINE",
                "battery_level": float(p.get("battery_level", 100)),
            },
        )
        SensorReading.objects.create(sensor=sensor, value=sensor.value)
        return Response({"success": True, "sensor": SensorSerializer(sensor).data})
    except (KeyError, ValueError, TypeError, Location.DoesNotExist, json.JSONDecodeError) as e:
        return Response({"success": False, "error": str(e)}, status=400)


@api_view(["GET"])
def weather(request):
    ensure_locations()
    force = request.GET.get("refresh") == "1"
    out = []
    for l in Location.objects.all():
        cached = l.weather.order_by("-timestamp").first()
        fresh = cached and timezone.now() - cached.timestamp < timedelta(minutes=10)
        if fresh and not force:
            w = cached
        else:
            try:
                data = fetch_weather_for_location(l)
                w = WeatherData.objects.create(location=l, **data)
            except Exception:
                if not cached:
                    continue
                w = cached
        # Turn the live weather + terrain + connected-sensor inputs into a fresh
        # explainable risk assessment. This is the value shown on the map/dashboard.
        payload = inputs_for_location(l, w)
        risk_result = calculate_risk(**payload)
        RiskAssessment.objects.create(location=l, **risk_result)
        if risk_result["risk_level"] in ("HIGH", "CRITICAL"):
            active = Alert.objects.filter(location=l, status="ACTIVE").first()
            if not active:
                ra = l.risks.order_by("-created_at").first()
                Alert.objects.create(
                    alert_id=f"ALT-{l.id}-{timezone.now().strftime('%Y%m%d%H%M%S%f')}",
                    location=l, risk_assessment=ra, alert_level=risk_result["risk_level"],
                    title=f"{risk_result['risk_level']} landslide risk at {l.name}",
                    message=f"Risk score {risk_result['risk_score']}/100",
                    reason=risk_result["explanation"], recommended_action=action(risk_result["risk_level"])
                )
        out.append(WeatherSerializer(w).data)
    return Response(out)


def inputs_for_location(location, weather_obj=None):
    if weather_obj is None:
        weather_obj = location.weather.order_by("-timestamp").first()
    ss = list(location.sensors.all())
    def avg(kind):
        a = [float(s.value) for s in ss if s.sensor_type == kind and s.status == "ONLINE"]
        return sum(a) / len(a) if a else 0.0
    # If soil/ground sensors are absent, soil stress is a conservative rainfall-derived proxy.
    soil = avg("SOIL")
    if soil == 0 and weather_obj:
        soil = min(100, float(weather_obj.rainfall_24h) * 0.55)
    return dict(
        rainfall_intensity=weather_obj.rainfall_intensity if weather_obj else avg("RAIN"),
        rainfall_24h=weather_obj.rainfall_24h if weather_obj else 0,
        rainfall_7d=weather_obj.rainfall_7d if weather_obj else 0,
        soil_moisture=soil,
        slope_angle=location.slope_angle,
        ground_movement=avg("GROUND"),
        tilt=avg("TILT"),
        vibration=avg("VIBRATION"),
        geological_risk=location.geological_risk,
        elevation=location.elevation,
    )


@api_view(["GET"])
def risks(request):
    return Response(RiskSerializer(
        RiskAssessment.objects.select_related("location").order_by("-created_at")[:500],
        many=True
    ).data)


@api_view(["GET"])
def risk_detail(request, location_id):
    return Response(RiskSerializer(
        RiskAssessment.objects.filter(location_id=location_id).order_by("-created_at")[:20],
        many=True
    ).data)


@api_view(["POST"])
def predict(request):
    try:
        loc = Location.objects.get(pk=int(request.data.get("location_id")))
    except (Location.DoesNotExist, TypeError, ValueError):
        return Response({"error": "Valid location_id is required"}, status=400)

    weather_obj = loc.weather.order_by("-timestamp").first()
    if not weather_obj:
        try:
            weather_obj = WeatherData.objects.create(location=loc, **fetch_weather_for_location(loc))
        except Exception:
            weather_obj = None

    payload = inputs_for_location(loc, weather_obj)
    r = calculate_risk(**payload)
    obj = RiskAssessment.objects.create(location=loc, **r)
    PredictionHistory.objects.create(
        location=loc, predicted_score=r["risk_score"],
        predicted_level=r["risk_level"], confidence=r["ai_confidence"]
    )
    if r["risk_level"] in ("HIGH", "CRITICAL"):
        active = Alert.objects.filter(location=loc, status="ACTIVE").first()
        if not active:
            Alert.objects.create(
                alert_id=f"ALT-{loc.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                location=loc, risk_assessment=obj, alert_level=r["risk_level"],
                title=f"{r['risk_level']} landslide risk at {loc.name}",
                message=f"Risk score {r['risk_score']}/100",
                reason=r["explanation"], recommended_action=action(r["risk_level"])
            )
    return Response(r)


@api_view(["GET"])
def alerts(request):
    qs = Alert.objects.select_related("location").order_by("-created_at")
    if request.GET.get("status"):
        qs = qs.filter(status=request.GET["status"].upper())
    return Response(AlertSerializer(qs[:100], many=True).data)


@api_view(["PATCH"])
def resolve_alert(request, pk):
    a = Alert.objects.filter(pk=pk).first()
    if not a:
        return Response({"error": "Not found"}, status=404)
    a.status = "RESOLVED"
    a.resolved_at = timezone.now()
    a.save(update_fields=["status", "resolved_at"])
    return Response(AlertSerializer(a).data)


@api_view(["GET"])
def trend(request):
    return Response([
        {"timestamp": r.created_at, "risk_score": r.risk_score, "risk_level": r.risk_level}
        for r in RiskAssessment.objects.order_by("-created_at")[:100]
    ][::-1])
