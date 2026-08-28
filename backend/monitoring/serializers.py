from rest_framework import serializers
from .models import *
class LocationSerializer(serializers.ModelSerializer):
 class Meta: model=Location; fields="__all__"
class SensorSerializer(serializers.ModelSerializer):
 location_name=serializers.CharField(source="location.name",read_only=True)
 class Meta: model=Sensor; fields=["id","sensor_id","sensor_type","location","location_name","value","unit","status","battery_level","last_updated"]
class WeatherSerializer(serializers.ModelSerializer):
 location_name=serializers.CharField(source="location.name",read_only=True)
 class Meta: model=WeatherData; fields="__all__"
class RiskSerializer(serializers.ModelSerializer):
 location_name=serializers.CharField(source="location.name",read_only=True)
 class Meta: model=RiskAssessment; fields=["id","location","location_name","risk_score","risk_level","rainfall_factor","soil_moisture_factor","slope_factor","ground_movement_factor","geological_factor","ai_confidence","prediction_horizon","explanation","created_at"]
class AlertSerializer(serializers.ModelSerializer):
 location_name=serializers.CharField(source="location.name",read_only=True)
 class Meta: model=Alert; fields="__all__"
