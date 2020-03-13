
from django.urls import path, re_path
from . import views

urlpatterns = [
    path('',views.home),
    path('date/<int:jour>/<int:mois>/<int:annee>',views.view_date),
    path('date/<int:jour>/<int:mois>',views.view_date),
]
