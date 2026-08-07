from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('chip_number', 'display_name', 'user', 'role', 'is_active_chip')
    list_filter = ('role', 'is_active_chip')
    search_fields = ('chip_number', 'display_name', 'user__username')
