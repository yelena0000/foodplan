from django.contrib import admin
from django.urls import path

from planner import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('auth/', views.auth, name='auth'),
    path('lk/', views.lk, name='lk'),
    path('order/', views.order, name='order'),
    path('card/', views.card, name='card'),
    path('registration/', views.register_view, name='registration'),
    path('logout/', views.logout_view, name='logout'),
    path('order/', views.order_view, name='order'),
    path('lk/', views.lk_view, name='lk'),
]
