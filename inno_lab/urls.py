from django.urls import path

from . import views

app_name = 'inno_lab'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('skaner/', views.product_create, name='scan'),
    path('baza/', views.base_list, name='base'),
    path('baza/eksport.csv', views.export_csv, name='export_csv'),
    path('baza/eksport.json', views.export_json, name='export_json'),
    path('baza/import.json', views.import_json, name='import_json'),

    path('produkt/<int:pk>/', views.product_edit, name='product_edit'),
    path('produkt/<int:pk>/usun/', views.product_delete, name='product_delete'),
    path('produkt/<int:pk>/zdjecia/dodaj/', views.photo_add, name='photo_add'),
    path('produkt/<int:pk>/ai-etykieta/', views.ai_read_label, name='ai_read_label'),
    path('zdjecie/<int:pk>/typ/', views.photo_set_type, name='photo_set_type'),
    path('zdjecie/<int:pk>/usun/', views.photo_delete, name='photo_delete'),

    path('produkt/<int:pk>/plan/', views.plan_detail, name='plan'),
    path('plan/<int:pk>/edytuj/', views.plan_edit, name='plan_edit'),
    path('plan/<int:pk>/przelicz/', views.plan_recalc_progress, name='plan_recalc'),
    path('plan/<int:pk>/usun/', views.plan_delete, name='plan_delete'),
    path('plan/<int:pk>/ai/', views.ai_enrich_plan, name='ai_enrich_plan'),
    path('plan/<int:pk>/krok/dodaj/', views.step_add, name='step_add'),

    path('krok/<int:pk>/edytuj/', views.step_edit, name='step_edit'),
    path('krok/<int:pk>/usun/', views.step_delete, name='step_delete'),
    path('krok/<int:pk>/przesun/<str:direction>/', views.step_move, name='step_move'),
]
