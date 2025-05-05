import json
import logging
import random
import uuid
from datetime import timedelta

from yookassa import Configuration, Payment

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.http import HttpResponse
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .forms import LoginForm, RegisterForm, UserProfileForm
from .models import (
    Allergy,
    DietType,
    Dish,
    UserProfile,
    SubscriptionOrder,
)


logger = logging.getLogger(__name__)


User = get_user_model()

Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

duration_mapping = {
    '0': '30',
    '1': '90',
    '2': '180',
    '3': '365',
}


@csrf_exempt
@login_required
def create_payment(request):
    if request.method != 'POST':
        messages.error(request, "Неверный метод запроса")
        return redirect('order')

    required_fields = [
        'foodtype',
        'select1',
        'select2',
        'select3',
        'select4',
        'select5',
        'duration',
    ]
    if not all(field in request.POST for field in required_fields):
        messages.error(request, "Не все необходимые данные получены")
        return redirect('order')

    try:
        duration = request.POST.get('duration', '0')
        meal_count = sum(
            1 for select in ['select1', 'select2', 'select3', 'select4']
            if request.POST.get(select) == '0'
        )

        price_per_month = {'0': 1200, '1': 1000, '2': 700, '3': 500}.get(
            duration, 1200
        )
        total_amount = price_per_month * meal_count
        duration_days = int(duration_mapping.get(duration, '30'))

        diet_type_name = {
            'classic': 'Классическое',
            'low': 'Низкоуглеводное',
            'veg': 'Вегетарианское',
            'keto': 'Кето',
        }.get(request.POST.get('foodtype'), 'Неизвестный')

        description = (
            f"Подписка FoodPlan: {diet_type_name} меню, "
            f"{duration_days} дней, {meal_count} приемов пищи"
        )

        order = SubscriptionOrder.objects.create(
            user=request.user,
            amount=total_amount,
            description=description,
            status='pending',
            subscription_params={
                'duration': duration,
                'duration_days': duration_days,
                'meal_count': meal_count,
                'foodtype': request.POST.get('foodtype'),
                'select1': request.POST.get('select1'),
                'select2': request.POST.get('select2'),
                'select3': request.POST.get('select3'),
                'select4': request.POST.get('select4'),
                'select5': request.POST.get('select5'),
                **{
                    f'allergy{i}': request.POST.get(f'allergy{i}', '0')
                    for i in range(1, 7)
                },
            },
        )

        payment = Payment.create(
            {
                "amount": {
                    "value": f"{total_amount:.2f}",
                    "currency": "RUB",
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": request.build_absolute_uri(
                        reverse('payment_success') + f"?order_id={order.id}"
                    ),
                },
                "capture": True,
                "description": description,
                "metadata": {
                    "order_id": order.id,
                    "user_id": request.user.id,
                    "subscription_type": "foodplan",
                },
            },
            str(uuid.uuid4()),
        )

        order.payment_id = payment.id
        order.save()

        logger.info(
            f"Created payment for order #{order.id}. "
            f"Amount: {total_amount}, user: {request.user.username}"
        )

        return redirect(payment.confirmation.confirmation_url)

    except Exception as e:
        logger.error(f"Error creating payment: {str(e)}", exc_info=True)
        messages.error(
            request,
            "Произошла ошибка при создании платежа. Пожалуйста, попробуйте позже.",
        )
        return redirect('order')


@csrf_exempt
@login_required
def payment_success(request):
    order_id = request.GET.get('order_id')
    if not order_id:
        messages.error(request, "Не получен ID заказа")
        return redirect('order')

    try:
        order = SubscriptionOrder.objects.get(id=order_id)

        if order.status == 'paid':
            messages.success(request, "Подписка уже активирована!")
            return redirect('lk')

        payment = Payment.find_one(order.payment_id)

        if payment.status == 'succeeded':
            if activate_subscription(order, payment):
                messages.success(request, "Подписка успешно оформлена!")
            else:
                messages.error(request, "Ошибка активации подписки")
            return redirect('lk')
        elif payment.status == 'waiting_for_capture':
            messages.info(request, "Платеж ожидает подтверждения")
            return redirect('lk')
        else:
            messages.error(
                request, f"Платеж не прошел. Статус: {payment.status}"
            )
            return redirect('order')

    except Exception as e:
        logger.error(f"Payment success error: {str(e)}", exc_info=True)
        messages.error(request, "Ошибка при обработке платежа")
        return redirect('order')


@csrf_exempt
def yookassa_webhook(request):
    if request.method == 'POST':
        event_json = json.loads(request.body)
        payment_id = event_json['object']['id']

        try:
            payment = Payment.find_one(payment_id)
            order = SubscriptionOrder.objects.get(payment_id=payment_id)

            if payment.status == 'succeeded' and order.status != 'paid':
                activate_subscription(order.user, order)
                order.status = 'paid'
                order.save()

        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")

    return HttpResponse(status=200)


def activate_subscription(order, payment):
    try:
        profile = order.user.userprofile
        sub_params = order.subscription_params

        profile.breakfast = sub_params.get('select1') == '0'
        profile.lunch = sub_params.get('select2') == '0'
        profile.dinner = sub_params.get('select3') == '0'
        profile.dessert = sub_params.get('select4') == '0'

        persons_mapping = {'0': 1, '1': 2, '2': 3, '3': 4, '4': 5, '5': 6}
        profile.count_of_persons = persons_mapping.get(
            sub_params.get('select5', '0'), 1
        )

        diet_type_name = {
            'classic': 'Классическое',
            'low': 'Низкоуглеводное',
            'veg': 'Вегетарианское',
            'keto': 'Кето',
        }.get(sub_params.get('foodtype'))

        if diet_type_name:
            diet_type, _ = DietType.objects.get_or_create(name=diet_type_name)
            profile.diet_type = diet_type

        allergy_map = {
            'allergy1': 'Рыба и морепродукты',
            'allergy2': 'Мясо',
            'allergy3': 'Зерновые',
            'allergy4': 'Продукты пчеловодства',
            'allergy5': 'Орехи и бобовые',
            'allergy6': 'Молочные продукты',
        }

        profile.allergies.clear()
        for key, name in allergy_map.items():
            if sub_params.get(key) == '1':
                allergy, _ = Allergy.objects.get_or_create(name=name)
                profile.allergies.add(allergy)

        duration_days = int(sub_params.get('duration_days', 30))
        profile.subscription_end_date = timezone.now().date() + timedelta(
            days=duration_days
        )

        profile.active_subscription = order
        profile.save()

        order.status = 'paid'
        order.payment_data = {
            'id': payment.id,
            'status': payment.status,
            'paid': payment.paid,
            'amount': payment.amount.value,
            'currency': payment.amount.currency,
            'created_at': payment.created_at,
        }
        order.save()

        logger.info(
            f"Subscription activated for user {order.user.username}, "
            f"order #{order.id}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Subscription activation failed for order #{order.id}: {str(e)}",
            exc_info=True,
        )
        return False


def index(request):
    context = {
        'current_date': timezone.now().date(),
    }
    return render(request, 'index.html', context)


def auth(request):
    if request.user.is_authenticated:
        return redirect('lk')
    return render(request, 'auth.html')


def registration(request):
    if request.user.is_authenticated:
        return redirect('lk')
    return render(request, 'registration.html')


def dish_card(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)
    ingredients = dish.dishingredient_set.all()
    profile = request.user.userprofile

    adjusted_ingredients = []
    for ingredient in ingredients:
        adjusted_quantity = float(ingredient.quantity) * profile.count_of_persons
        adjusted_ingredients.append({
            'ingredient': ingredient.ingredient,
            'quantity': adjusted_quantity,
            'unit': ingredient.ingredient.get_unit_display(),
        })

    context = {
        'dish': dish,
        'ingredients': adjusted_ingredients,
        'profile': profile,
    }
    return render(request, 'card.html', context)


@login_required
def lk_view(request):
    user = request.user
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        messages.error(request, "Профиль пользователя не найден")
        return redirect('index')

    # Проверка активности подписки
    subscription_active = (
        profile.subscription_end_date
        and profile.subscription_end_date >= timezone.now().date()
    )
    dishes_by_category = {}

    if subscription_active and profile.diet_type:
        # Логика фильтрации блюд только если подписка активна и выбран тип диеты
        categories = []
        if profile.breakfast:
            categories.append('breakfast')
        if profile.lunch:
            categories.append('lunch')
        if profile.dinner:
            categories.append('dinner')
        if profile.dessert:
            categories.append('dessert')

        if categories:
            dishes = Dish.objects.filter(
                diet_type=profile.diet_type,
                category__in=categories,
            ).distinct()

            if profile.allergies.exists():
                dishes = dishes.exclude(
                    ingredients__allergens__in=profile.allergies.all()
                ).distinct()

            adjusted_dishes = []
            for dish in dishes:
                dish.adjusted_price = dish.total_price * profile.count_of_persons
                dish.adjusted_calories = dish.total_calories * profile.count_of_persons
                adjusted_dishes.append(dish)

            if profile.budget_limit:
                adjusted_dishes = [
                    dish
                    for dish in adjusted_dishes
                    if dish.adjusted_price <= profile.budget_limit
                ]

            for category in categories:
                category_dishes = [
                    d for d in adjusted_dishes if d.category == category
                ]
                dishes_by_category[f"{category}_dishes"] = category_dishes

    form = UserProfileForm(instance=profile, user=user)

    context = {
        'form': form,
        'profile': profile,
        'user': user,
        'subscription_active': subscription_active,
        **dishes_by_category,
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
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                next_url = request.POST.get('next', '')
                return redirect(next_url if next_url else 'lk')
            else:
                messages.error(request, 'Неверный логин или пароль')
    else:
        form = LoginForm()

    next_url = request.GET.get('next', '')
    return render(
        request,
        'auth.html',
        {
            'form': form,
            'next': next_url,
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect('lk')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()

            UserProfile.objects.create(
                user=user,
                diet_type=form.cleaned_data.get('diet_type'),
                breakfast=True,
                lunch=True,
                dinner=True,
                dessert=False,
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

    form = UserProfileForm(
        request.POST, request.FILES, instance=profile, user=user
    )
    if form.is_valid():
        form.save()
        messages.success(request, 'Профиль обновлён!')
    else:
        messages.error(request, 'Ошибка при обновлении профиля.')

    return redirect('lk')


@login_required
@require_POST
def update_avatar(request):
    profile = request.user.userprofile
    if 'avatar' in request.FILES:
        profile.avatar = request.FILES['avatar']
        profile.save()
        messages.success(request, 'Аватар успешно обновлен!')
    else:
        messages.error(request, 'Не удалось загрузить аватар')
    return redirect('lk')
