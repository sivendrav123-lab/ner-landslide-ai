import random
from django.core.management.base import BaseCommand
from monitoring.models import *
from monitoring.risk_engine import calculate_risk
DATA=[("Agartala","Tripura","West Tripura",23.8315,91.2868,50,18,.55),("Guwahati","Assam","Kamrup",26.1445,91.7362,55,22,.7),("Itanagar","Arunachal Pradesh","Papum Pare",27.0844,93.6053,350,28,.8),("Gangtok","Sikkim","East Sikkim",27.3389,88.6065,1650,38,.9),("Imphal","Manipur","Imphal West",24.817,93.9368,790,24,.55),("Kohima","Nagaland","Kohima",25.6751,94.1086,1444,35,.8),("Aizawl","Mizoram","Aizawl",23.7271,92.7176,1132,40,.85),("Shillong","Meghalaya","East Khasi Hills",25.5788,91.8933,1496,30,.7),("Cherrapunji","Meghalaya","East Khasi Hills",25.284,91.722,1484,42,.9)]
class Command(BaseCommand):
 def handle(self,*a,**k):
  for i,d in enumerate(DATA,1):
   l,_=Location.objects.update_or_create(name=d[0],defaults=dict(state=d[1],district=d[2],latitude=d[3],longitude=d[4],elevation=d[5],slope_angle=d[6],geological_risk=d[7]))
   for j,t in enumerate(["RAIN","SOIL","TILT","GROUND","VIBRATION"]):
    for n in range(1,8):
     sid=f"{t}-{i:02d}-{n:02d}"; unit={"RAIN":"mm","SOIL":"%","TILT":"deg","GROUND":"mm","VIBRATION":"mm/s"}[t]
     v={"RAIN":random.uniform(5,30),"SOIL":random.uniform(40,90),"TILT":random.uniform(.2,5),"GROUND":random.uniform(.2,12),"VIBRATION":random.uniform(.2,7)}[t]
     Sensor.objects.get_or_create(sensor_id=sid,defaults={"sensor_type":t,"location":l,"value":v,"unit":unit,"status":"ONLINE","battery_level":random.uniform(70,100)})
   WeatherData.objects.create(location=l,temperature=random.uniform(16,31),humidity=random.uniform(60,95),rainfall_1h=random.uniform(2,25),rainfall_24h=random.uniform(40,145),rainfall_7d=random.uniform(100,450),rainfall_intensity=random.uniform(5,25),wind_speed=random.uniform(2,18))
   vals={t:random.uniform(1,15) for t in ["GROUND","TILT","VIBRATION"]}; w=l.weather.order_by("-timestamp").first()
   r=calculate_risk(rainfall_intensity=w.rainfall_intensity,rainfall_24h=w.rainfall_24h,rainfall_7d=w.rainfall_7d,soil_moisture=vals["GROUND"]*4,slope_angle=l.slope_angle,ground_movement=vals["GROUND"],tilt=vals["TILT"],vibration=vals["VIBRATION"],geological_risk=l.geological_risk,elevation=l.elevation)
   obj=RiskAssessment.objects.create(location=l,**r)
   if r["risk_level"] in ("HIGH","CRITICAL"): Alert.objects.get_or_create(alert_id=f"DEMO-{i}",defaults={"location":l,"risk_assessment":obj,"alert_level":r["risk_level"],"title":f"{r['risk_level']} landslide risk at {l.name}","message":f"Demo warning: {r['risk_score']}/100","reason":r["explanation"],"recommended_action":"Increase monitoring and field verification."})
  self.stdout.write("Demo data created. Data is simulated/demo data.")
