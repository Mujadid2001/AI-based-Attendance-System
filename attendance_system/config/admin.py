"""
Custom Django Admin Site Configuration
"""
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _


class AttendanceAdminSite(AdminSite):
    """Custom admin site for AI-Based Attendance System."""
    
    # Site header, title and index title
    site_header = _('AI Attendance System Administration')
    site_title = _('AI Attendance Admin')
    index_title = _('Dashboard - Manage Your Attendance System')
    
    # Enable default admin CSS
    enable_nav_sidebar = True
    
    def each_context(self, request):
        """Add custom context to all admin pages."""
        context = super().each_context(request)
        context.update({
            'custom_site_name': 'AI-Based Attendance System',
            'support_email': 'mujadid2001@gmail.com',
        })
        return context


# Create custom admin site instance
admin_site = AttendanceAdminSite(name='custom_admin')
