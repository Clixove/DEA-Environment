from django.contrib import admin
from .models import *


@admin.register(DeaResults)
class DeaResultsAdmin(admin.ModelAdmin):
    list_display = ['task', 'evaluation']
