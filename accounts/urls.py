from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.chip_login, name='login'),
    path('logout/', views.chip_logout, name='logout'),

    path('uzytkownicy/', views.user_list, name='user_list'),
    path('uzytkownicy/dodaj/', views.user_create, name='user_create'),
    path('uzytkownicy/<int:pk>/edytuj/', views.user_edit, name='user_edit'),
    path('uzytkownicy/<int:pk>/status/', views.user_toggle_active, name='user_toggle_active'),
    path('uzytkownicy/<int:pk>/usun/', views.user_delete, name='user_delete'),
]
