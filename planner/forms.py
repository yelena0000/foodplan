from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, DietType


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    diet_type = forms.ModelChoiceField(
        queryset=DietType.objects.all(),
        required=False,
        label="Тип диеты"
    )
    breakfast = forms.BooleanField(
        required=False,
        label="Завтрак"
    )
    lunch = forms.BooleanField(
        required=False,
        label="Обед"
    )
    dinner = forms.BooleanField(
        required=False,
        label="Ужин"
    )
    dessert = forms.BooleanField(
        required=False,
        label="Десерт"
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
