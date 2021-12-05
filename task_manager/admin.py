from django.contrib import admin
from .models import *


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_time', 'busy', 'current_step']
    list_filter = ['created_time', 'busy', 'current_step']
    autocomplete_fields = ['user']
    search_fields = ['name']


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ['task', 'name', 'is_datetime', 'is_dmu', 'is_input', 'is_output']
    autocomplete_fields = ['task']
    search_fields = ['name']


@admin.register(AsyncErrorMessage)
class AsyncErrorMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'happened_time', 'current_step', 'error_message']
    autocomplete_fields = ['user', 'task']
    list_filter = ['happened_time', 'current_step']
    search_fields = ['error_message']
