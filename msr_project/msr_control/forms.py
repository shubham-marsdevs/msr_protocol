from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserRole

class SignUpForm(UserCreationForm):
    """Form for user registration with role selection"""
    email = forms.EmailField(max_length=254, required=True, help_text='Required. Enter a valid email address.')
    
    ROLE_CHOICES = (
        ('operator', 'Operator'),
        ('calibrator', 'Calibrator'),
        ('admin', 'Admin'),
    )
    
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, help_text='Select your role in the system.')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')
