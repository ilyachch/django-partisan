from django_partisan.processor import BaseTaskProcessor
from django_partisan.registry import register
from test_partisan.test_app.models import Results

@register
class Task(BaseTaskProcessor):
    def run(self):
        Results.objects.create(result=f'{self.args} - {self.kwargs}')