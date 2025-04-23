from django.db import models
from django.contrib.auth.models import User


class Allergy(models.Model):
    name = models.CharField(max_length=150, verbose_name='Аллергия')

    def __str__(self):
        return self.name


class DietType(models.Model):
    name = models.CharField(max_length=150, verbose_name='Тип диеты')

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    allergies = models.ManyToManyField(
        Allergy,
        blank=True,
        verbose_name='Аллергии'
    )    
    diet_type = models.ForeignKey(
        DietType,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Тип диеты'
    )
    budget_limit = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Ограничение по стоимости'
    )

    count_of_persons = models.IntegerField(
        default=1,
        verbose_name='Количество персон'
    )
    breakfast = models.BooleanField(verbose_name='Завтрак')
    lunch = models.BooleanField(verbose_name='Обед')
    dinner = models.BooleanField(verbose_name='Ужин')
    dessert = models.BooleanField(verbose_name='Десерт')
    subscription_end_date = models.DateField(
        verbose_name='Дата окончания подписки'
    )  # при подсчёте тарифа прибавляем дни к конечной дате

    def __str__(self):
        return self.user.username


class Dish(models.Model):
    name = models.CharField(max_length=150, verbose_name='Название блюда')
    description = models.TextField(verbose_name='Описание блюда')
    photo = models.ImageField(verbose_name='Фото блюда')
    diet_type = models.ForeignKey(
        DietType,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Тип диеты'
    )
    # dish_type = models. выбор из 4 вариантов

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=150, verbose_name='Название блюда')
    allergens = models.ManyToManyField(
        Allergy,
        blank=True,
        verbose_name='Аллергены'
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Стоимость'
    )
    callories = models.IntegerField(verbose_name='Калорийность')