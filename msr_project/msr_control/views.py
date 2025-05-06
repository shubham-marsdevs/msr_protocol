from django.shortcuts import render

def dashboard(request):
    return render(request, 'msr_control/dashboard.html')
