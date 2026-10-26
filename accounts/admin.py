from django.contrib import admin, messages

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('chip_number', 'display_name', 'user', 'role', 'is_active_chip', 'has_code')
    list_filter = ('role', 'is_active_chip')
    search_fields = ('chip_number', 'display_name', 'user__username')
    actions = ['reset_auth_codes']

    @admin.display(boolean=True, description='Kod autoryzacyjny ustawiony')
    def has_code(self, obj):
        return obj.has_auth_code

    @admin.action(description='Resetuj kod autoryzacyjny (użytkownik ustawi nowy przy logowaniu)')
    def reset_auth_codes(self, request, queryset):
        for profile in queryset:
            profile.reset_auth_code()
        self.message_user(request, f'Zresetowano kody: {queryset.count()}.', messages.SUCCESS)
