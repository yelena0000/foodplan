from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .forms import LoginForm, RegisterForm
from .models import UserProfile


def index(request):
    return render(request, 'index.html')


def auth(request):
    return render(request, 'auth.html')


def registration(request):
    return render(request, 'registration.html')


def lk(request):
    return render(request, 'lk.html')


def order(request):
    return render(request, 'order.html')


def card(request):
    return render(request, 'card.html')


def auth_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                # Проверяем, откуда пришел пользователь
                next_url = request.POST.get('next', None)
                if next_url:
                    return redirect(next_url)  # Редирект на исходную страницу
                return redirect('lk')  # По умолчанию — в личный кабинет
    else:
        form = LoginForm()

    # Сохраняем URL, с которого пришли (для редиректа после входа)
    next_url = request.GET.get('next', '')
    return render(request, 'auth.html', {
        'form': form,
        'next': next_url  # Передаем в шаблон
    })


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            UserProfile.objects.create(
                user=user,
                diet_type=form.cleaned_data.get('diet_type')
            )
            login(request, user)
            return redirect('order')
    else:
        form = RegisterForm()
    return render(request, 'registration.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('index')


@login_required
def order_view(request):
    return render(request, 'order.html')


def lk_view(request):
    user_profile = request.user.userprofile
    return render(request, 'lk.html', {
        'user_profile': user_profile
    })
