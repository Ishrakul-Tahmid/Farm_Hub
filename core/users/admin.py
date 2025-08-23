from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'username', 'first_name', 'last_name', 'is_agent', 'is_farmer', 'is_staff', 'is_superuser']
    search_fields = ['email', 'username', 'first_name', 'last_name', 'is_agent', 'is_farmer']