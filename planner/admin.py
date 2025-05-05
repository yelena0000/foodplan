from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Allergy,
    DietType,
    UserProfile,
    Ingredient,
    Dish,
    DishIngredient,
    SubscriptionOrder
)


@admin.register(Allergy)
class AllergyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(DietType)
class DietTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'diet_type', 'subscription_status', 'count_of_persons')
    list_filter = ('diet_type', 'breakfast', 'lunch', 'dinner', 'dessert')
    search_fields = ('user__username',)
    filter_horizontal = ('allergies',)

    fieldsets = (
        ('Основное', {
            'fields': ('user', 'avatar', 'diet_type', 'allergies')
        }),
        ('Настройки питания', {
            'fields': ('breakfast', 'lunch', 'dinner', 'dessert', 'count_of_persons', 'budget_limit')
        }),
        ('Подписка', {
            'fields': ('subscription_end_date', 'active_subscription')
        }),
    )

    def subscription_status(self, obj):
        if obj.subscription_end_date:
            if obj.subscription_end_date >= timezone.now().date():
                return f"Активна до {obj.subscription_end_date.strftime('%d.%m.%Y')}"
            return f"Истекла {obj.subscription_end_date.strftime('%d.%m.%Y')}"
        return "Нет подписки"
    subscription_status.short_description = 'Статус подписки'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'callories', 'unit')
    list_filter = ('unit',)
    search_fields = ('name',)
    filter_horizontal = ('allergens',)


class DishIngredientInline(admin.TabularInline):
    model = DishIngredient
    extra = 1
    fields = ('ingredient', 'quantity')


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'diet_type', 'total_price', 'total_calories')
    list_filter = ('category', 'diet_type')
    search_fields = ('name', 'description')
    inlines = [DishIngredientInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'diet_type', 'category', 'photo')
        }),
        ('Описание', {
            'fields': ('description', 'recipe')
        }),
    )

    def total_price(self, obj):
        return f"{obj.total_price:.2f} руб"
    total_price.short_description = 'Стоимость'

    def total_calories(self, obj):
        return f"{obj.total_calories:.0f} ккал"
    total_calories.short_description = 'Калории'


@admin.register(SubscriptionOrder)
class SubscriptionOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'description')
    readonly_fields = ('created_at', 'payment_details')

    fieldsets = (
        ('Основное', {
            'fields': ('user', 'status', 'amount', 'description')
        }),
        ('Платеж', {
            'fields': ('payment_id', 'payment_details', 'created_at')
        }),
        ('Параметры', {
            'fields': ('subscription_params',)
        }),
    )

    def payment_details(self, obj):
        if obj.payment_data:
            return format_html(
                '<pre>{}</pre>',
                str(obj.payment_data))
        return "Нет данных"
    payment_details.short_description = 'Детали платежа'
