"""
Admin configuration for authentication models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.authentication.models import User, LoginLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    
    list_display = (
        'email', 'get_full_name', 'role', 'is_active', 'is_verified',
        'created_at'
    )
    list_filter = ('role', 'is_active', 'is_verified', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'phone', 'profile_picture'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'role',
                'is_verified'
            )
        }),
        ('Important Dates', {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login')


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    """Admin interface for LoginLog model."""
    
    list_display = (
        'user', 'ip_address', 'success', 'failure_reason', 'timestamp'
    )
    list_filter = ('success', 'timestamp')
    search_fields = ('user__email', 'ip_address')
    readonly_fields = ('user', 'ip_address', 'user_agent', 'success',
                      'failure_reason', 'timestamp')
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        """Prevent manual addition of logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of logs."""
        return False
