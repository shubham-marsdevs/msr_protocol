from django.db import models
from django.contrib.auth.models import User

class UserRole(models.Model):
    """Model to define user roles and their permissions"""
    ROLE_CHOICES = (
        ('operator', 'Operator'),
        ('calibrator', 'Calibrator'),
        ('admin', 'Admin'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='operator')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    @property
    def is_operator(self):
        return self.role == 'operator'

    @property
    def is_calibrator(self):
        return self.role == 'calibrator'

    @property
    def is_admin(self):
        return self.role == 'admin'

    class Meta:
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
