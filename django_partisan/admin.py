from django.contrib import admin
from django_partisan import models


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    pass
