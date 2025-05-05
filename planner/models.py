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


class SubscriptionOrder(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма заказа'
    )
    description = models.CharField(
        max_length=255,
        verbose_name='Описание подписки'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидает оплаты'),
            ('paid', 'Оплачен'),
            ('failed', 'Не удался')
        ],
        default='pending',
        verbose_name='Статус'
    )
    payment_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='ID платежа'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    subscription_params = models.JSONField(
        default=dict,
        verbose_name='Параметры подписки'
    )
    payment_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Данные платежа'
    )

    @property
    def is_active(self):
        return self.status == 'paid' and (
            self.user.userprofile.subscription_end_date >= timezone.now().date()
            if hasattr(self.user, 'userprofile') and self.user.userprofile.subscription_end_date
            else False
        )

    def __str__(self):
        return f"Заказ #{self.id} - {self.get_status_display()}"


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
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
        blank=True,
        verbose_name='Тип диеты'
    )
    budget_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Ограничение по стоимости'
    )
    count_of_persons = models.IntegerField(
        default=1,
        verbose_name='Количество персон'
    )
    breakfast = models.BooleanField(
        default=True,
        verbose_name='Завтрак'
    )
    lunch = models.BooleanField(
        default=True,
        verbose_name='Обед'
    )
    dinner = models.BooleanField(
        default=True,
        verbose_name='Ужин'
    )
    dessert = models.BooleanField(
        default=False,
        verbose_name='Десерт'
    )
    subscription_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата окончания подписки'
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='avatars/',
        null=True, blank=True
    )

    active_subscription = models.ForeignKey(
        SubscriptionOrder,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Активная подписка'
    )

    def __str__(self):
        return self.user.username


class Ingredient(models.Model):
    UNIT_CHOICES = [
        ('g', 'Граммы'),
        ('ml', 'Миллилитры'),
        ('pcs', 'Штуки'),
        ('tbsp', 'Столовые ложки'),
        ('tsp', 'Чайные ложки'),
    ]
    name = models.CharField(
        max_length=150,
        verbose_name='Название ингредиента'
    )
    allergens = models.ManyToManyField(
        Allergy,
        blank=True,
        verbose_name='Аллергены'
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Стоимость за единицу'
    )
    callories = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name='Калорийность'
    )
    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default='g',
        verbose_name='Единица измерения'
    )

    def __str__(self):
        return f'{self.name} ({self.get_unit_display()})'


class Dish(models.Model):
    DISH_CATEGORY_CHOICES = [
        ('breakfast', 'Завтрак'),
        ('lunch', 'Обед'),
        ('dinner', 'Ужин'),
        ('dessert', 'Десерт')
    ]
    name = models.CharField(
        max_length=150,
        verbose_name='Название блюда'
    )
    description = models.TextField(
        verbose_name='Описание блюда'
    )
    recipe = models.TextField(
        verbose_name='Рецепт приготовления',
        blank=True,
        default=''
    )
    photo = models.ImageField(
        verbose_name='Фото блюда',
        blank=True,
        null=True,
        upload_to='dishes/'
    )
    diet_type = models.ForeignKey(
        DietType,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Тип меню'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='DishIngredient',
        verbose_name='Ингредиенты'
    )
    category = models.CharField(
        max_length=50,
        choices=DISH_CATEGORY_CHOICES,
        verbose_name='Категория блюда',
        default='lunch'
    )

    @property
    def total_price(self):
        return sum(
            di.quantity * di.ingredient.price
            for di in self.dishingredient_set.all()
        )

    @property
    def total_calories(self):
        return sum(
            di.quantity * di.ingredient.callories
            for di in self.dishingredient_set.all()
        )

    def __str__(self):
        return self.name


class DishIngredient(models.Model):
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Количество'
    )

    def __str__(self):
        return f'{self.ingredient} - {self.quantity}'
