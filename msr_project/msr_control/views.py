from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserRole
from django.http import HttpResponseForbidden
from .forms import SignUpForm

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'msr_control/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Save the user
            user = form.save()

            # Create the user role
            role = form.cleaned_data.get('role')
            UserRole.objects.create(user=user, role=role)

            # Log the user in
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)

            messages.success(request, f'Account created successfully! Welcome, {username}!')
            return redirect('dashboard')
    else:
        form = SignUpForm()

    return render(request, 'msr_control/signup.html', {'form': form})

@login_required
def dashboard(request):
    # Get the user's role
    try:
        user_role = request.user.role.role
    except UserRole.DoesNotExist:
        # If no role is assigned, default to operator
        user_role = 'operator'
        UserRole.objects.create(user=request.user, role=user_role)

    context = {
        'user_role': user_role,
    }

    return render(request, 'msr_control/dashboard.html', context)

@login_required
def operator_view(request):
    # Check if user has operator role or higher
    try:
        user_role = request.user.role
        if not (user_role.is_operator or user_role.is_calibrator or user_role.is_admin):
            return HttpResponseForbidden("You don't have permission to access this page")
    except UserRole.DoesNotExist:
        return HttpResponseForbidden("Role not assigned")

    return render(request, 'msr_control/operator.html')

@login_required
def calibrator_view(request):
    # Check if user has calibrator role or higher
    try:
        user_role = request.user.role
        if not (user_role.is_calibrator or user_role.is_admin):
            return HttpResponseForbidden("You don't have permission to access this page")
    except UserRole.DoesNotExist:
        return HttpResponseForbidden("Role not assigned")

    return render(request, 'msr_control/calibrator.html')

@login_required
def admin_view(request):
    # Check if user has admin role
    try:
        user_role = request.user.role
        if not user_role.is_admin:
            return HttpResponseForbidden("You don't have permission to access this page")
    except UserRole.DoesNotExist:
        return HttpResponseForbidden("Role not assigned")

    return render(request, 'msr_control/admin.html')
