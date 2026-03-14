from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def landing(request):
    if request.user.is_authenticated:
        if request.user.role == 'owner':
            return redirect('owner_dashboard')
        return redirect('attendant_dashboard')
    return render(request, 'accounts/landing.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session['role'] = user.role
            request.session.modified = True
            if user.role == 'owner':
                return redirect('owner_dashboard')
            else:
                return redirect('attendant_dashboard')
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid username or password'})
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')