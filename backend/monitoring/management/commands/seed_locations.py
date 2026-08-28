from django.core.management.base import BaseCommand
from monitoring.views import ensure_locations

class Command(BaseCommand):
    help = "Create the fixed NER monitoring locations without simulated sensor/weather data."

    def handle(self, *args, **kwargs):
        ensure_locations()
        self.stdout.write(self.style.SUCCESS("NER monitoring locations are ready. No simulated sensor data was created."))
