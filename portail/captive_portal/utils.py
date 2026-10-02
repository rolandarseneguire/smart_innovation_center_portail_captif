from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('forfaits/', views.forfaits_view, name='liste_forfaits'),
    path('informations/<uuid:forfait_id>/', views.recuperation_informations_view, name='recuperation_informations'),
    path('paiement/<uuid:souscription_id>/', views.paiement_view, name='paiement'),
    path('recapitulatif/<uuid:souscription_id>/', views.recapitulatif_paiement_view, name='recapitulatif_paiement'),
    path('traiter-paiement/<uuid:souscription_id>/', views.traiter_paiement_view, name='traiter_paiement'),
    path('succes/<uuid:souscription_id>/', views.succes_connexion_view, name='succes_connexion'),
]