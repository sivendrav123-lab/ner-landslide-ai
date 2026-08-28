from django.contrib import admin
from .models import *
admin.site.register([Location,Sensor,SensorReading,WeatherData,RiskAssessment,Alert,PredictionHistory])
