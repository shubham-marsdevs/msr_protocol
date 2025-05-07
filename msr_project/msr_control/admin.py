from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserRole

class UserRoleInline(admin.StackedInline):
    model = UserRole
    can_delete = False
    verbose_name_plural = 'User Roles'

class UserAdmin(BaseUserAdmin):
    inlines = (UserRoleInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')

    def get_role(self, obj):
        try:
            return obj.role.get_role_display()
        except UserRole.DoesNotExist:
            return '-'

    get_role.short_description = 'Role'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserRole)
