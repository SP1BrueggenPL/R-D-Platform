from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.hub, name='hub'),
    path('jezyk/<str:code>/', views.set_language, name='set_language'),
]
