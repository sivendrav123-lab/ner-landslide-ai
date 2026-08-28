from django.db import models
class Location(models.Model):
 name=models.CharField(max_length=120); state=models.CharField(max_length=80); district=models.CharField(max_length=120); latitude=models.FloatField(); longitude=models.FloatField(); elevation=models.FloatField(default=0); slope_angle=models.FloatField(default=0); geological_risk=models.FloatField(default=.5); population=models.IntegerField(default=0); created_at=models.DateTimeField(auto_now_add=True)
class Sensor(models.Model):
 sensor_id=models.CharField(max_length=80,unique=True); sensor_type=models.CharField(max_length=20); location=models.ForeignKey(Location,on_delete=models.CASCADE,related_name="sensors"); value=models.FloatField(default=0); unit=models.CharField(max_length=20); status=models.CharField(max_length=20,default="ONLINE"); battery_level=models.FloatField(default=100); last_updated=models.DateTimeField(auto_now=True)
class SensorReading(models.Model):
 sensor=models.ForeignKey(Sensor,on_delete=models.CASCADE,related_name="readings"); value=models.FloatField(); timestamp=models.DateTimeField(auto_now_add=True)
class WeatherData(models.Model):
 location=models.ForeignKey(Location,on_delete=models.CASCADE,related_name="weather"); temperature=models.FloatField(); humidity=models.FloatField(); rainfall_1h=models.FloatField(); rainfall_24h=models.FloatField(); rainfall_7d=models.FloatField(); rainfall_intensity=models.FloatField(); wind_speed=models.FloatField(); timestamp=models.DateTimeField(auto_now_add=True)
class RiskAssessment(models.Model):
 location=models.ForeignKey(Location,on_delete=models.CASCADE,related_name="risks"); risk_score=models.FloatField(); risk_level=models.CharField(max_length=20); rainfall_factor=models.FloatField(); soil_moisture_factor=models.FloatField(); slope_factor=models.FloatField(); ground_movement_factor=models.FloatField(); geological_factor=models.FloatField(); ai_confidence=models.FloatField(); prediction_horizon=models.CharField(max_length=50); explanation=models.TextField(); created_at=models.DateTimeField(auto_now_add=True)
class Alert(models.Model):
 alert_id=models.CharField(max_length=80,unique=True); location=models.ForeignKey(Location,on_delete=models.CASCADE,related_name="alerts"); risk_assessment=models.ForeignKey(RiskAssessment,on_delete=models.CASCADE); alert_level=models.CharField(max_length=20); title=models.CharField(max_length=200); message=models.TextField(); reason=models.TextField(); recommended_action=models.TextField(); status=models.CharField(max_length=20,default="ACTIVE"); created_at=models.DateTimeField(auto_now_add=True); resolved_at=models.DateTimeField(null=True,blank=True)
class PredictionHistory(models.Model):
 location=models.ForeignKey(Location,on_delete=models.CASCADE); predicted_score=models.FloatField(); predicted_level=models.CharField(max_length=20); confidence=models.FloatField(); actual_outcome=models.BooleanField(null=True); created_at=models.DateTimeField(auto_now_add=True)
