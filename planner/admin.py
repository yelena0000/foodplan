from django.contrib import admin
from .models import Allergy, DietType, UserProfile, Ingredient, Dish, DishIngredient

admin.site.register(Allergy)
admin.site.register(DietType)
admin.site.register(UserProfile)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'unit', 'get_allergens')
    list_filter = ('unit',)
    search_fields = ('name',)

    def get_allergens(self, obj):
        return ", ".join([a.name for a in obj.allergens.all()])


class DishIngredientInline(admin.TabularInline):
    model = DishIngredient
    extra = 1


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'display_diet_type', 'total_price', 'total_calories')
    list_filter = ('category', 'diet_type')
    inlines = [DishIngredientInline]
    readonly_fields = ('total_price', 'total_calories')

    def display_diet_type(self, obj):
        return obj.diet_type.name if obj.diet_type else "-"
    display_diet_type.short_description = 'Тип диеты'

    def total_price(self, obj):
        return f"{obj.total_price:.2f} руб"
    total_price.short_description = 'Цена'

    def total_calories(self, obj):
        return f"{obj.total_calories} ккал"
    total_calories.short_description = 'Калорийность'
