from django.contrib import admin
from django.urls import path

from planner import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('auth/', views.auth, name='auth'),
    path('registration/', views.registration, name='registration'),
    path('lk/', views.lk, name='lk'),
    path('order/', views.order, name='order'),
    path('card/', views.card, name='card'),
]
