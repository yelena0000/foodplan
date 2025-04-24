from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST

from .forms import LoginForm, RegisterForm, UserProfileForm
from .models import UserProfile, DietType, Dish


User = get_user_model()


def index(request):
    return render(request, 'index.html')


def auth(request):
    if request.user.is_authenticated:
        return redirect('lk')
    return render(request, 'auth.html')


def registration(request):
    if request.user.is_authenticated:
        return redirect('lk')
    return render(request, 'registration.html')


@login_required
def lk_view(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    form = UserProfileForm(instance=profile, user=user)

    my_dishes = Dish.objects.filter(diet_type=profile.diet_type)

    context = {
        'form': form,
        'profile': profile,
        'user': user,
        'my_dishes': my_dishes,
    }
    return render(request, 'lk.html', context)


@login_required
def order(request):
    return render(request, 'order.html')


def card(request):
    return render(request, 'card.html')


def auth_view(request):
    if request.user.is_authenticated:
        return redirect('lk')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

            if user is not None:
                login(request, user)
                next_url = request.POST.get('next', '')
                return redirect(next_url if next_url else 'lk')
            else:
                messages.error(request, 'Неверный email или пароль')
    else:
        form = LoginForm()

    next_url = request.GET.get('next', '')
    return render(request, 'auth.html', {
        'form': form,
        'next': next_url
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('lk')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Создаем профиль пользователя с данными по умолчанию
            UserProfile.objects.create(
                user=user,
                diet_type=form.cleaned_data.get('diet_type'),
                breakfast=True,
                lunch=True,
                dinner=True,
                dessert=False
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


@require_POST
@login_required
def update_profile(request):
    user = request.user
    profile = user.userprofile

    form = UserProfileForm(request.POST, instance=profile, user=user)
    if form.is_valid():
        form.save()
        messages.success(request, 'Профиль обновлён!')
    else:
        messages.error(request, 'Ошибка при обновлении профиля.')

    return redirect('lk')
