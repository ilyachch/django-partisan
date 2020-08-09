from django_partisan.processor import BaseTaskProcessor
from django_partisan.registry import register

@register
class Task(BaseTaskProcessor):
    def run(self):
        from .models import Results
        Results.objects.create(result=f'{self.args} - {self.kwargs}')