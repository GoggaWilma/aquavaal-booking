from django.contrib import admin
from .models import Stand


@admin.register(Stand)
class StandAdmin(admin.ModelAdmin):
    list_display = ('number', 'section', 'approval_flow', 'is_active')
    list_filter = ('section', 'approval_flow', 'is_active')
    ordering = ('number',)

