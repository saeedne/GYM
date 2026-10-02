from django.contrib import admin
from .models import ClubApiKey
@admin.register(ClubApiKey)
class ClubApiKeyAdmin(admin.ModelAdmin):
    list_display=("name","club","prefix","created_at","last_used_at","expires_at","revoked_at")
    readonly_fields=("prefix","secret_hash","created_at","last_used_at")
