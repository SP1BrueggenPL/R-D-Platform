from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.chip_login, name='login'),
    path('logout/', views.chip_logout, name='logout'),
]
