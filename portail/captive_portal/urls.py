from django.urls import path
from . import views

urlpatterns = [
    # 1. Accueil
    path('', views.home_view, name='home'),

    # 2. Catalogue Forfaits
    path('forfaits/', views.forfaits_view, name='liste_forfaits'),

    # 3. Étape 1 : Piège / Infos Utilisateur
    path('informations/<uuid:forfait_id>/', views.recuperation_informations_view, name='recuperation_informations'),

    # 4. Étape 2 : Paiement / Opérateur (Mis à jour avec UUID)
    path('paiement/<uuid:souscription_id>/', views.paiement_view, name='paiement'),

    # 5. Étape 3 : Récapitulatif et Confirmation (Mis à jour avec UUID)
    path('recapitulatif/<uuid:souscription_id>/', views.recapitulatif_paiement_view, name='recapitulatif_paiement'),

    # 6. Traitement & Génération RADIUS
    path('traiter-paiement/<uuid:souscription_id>/', views.traiter_paiement_view, name='traiter_paiement'),

    # 7. Dashboard Client
    path('succes/<uuid:souscription_id>/', views.succes_connexion_view, name='succes_connexion'),
]