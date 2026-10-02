import uuid
import subprocess
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from .models import (
    Forfait, Operator, Enterprise, User,
    Souscription, Connexion, RadCheck, RadReply, RadAcct
)
from .forms import RegistrationForm

NAS_IP = os.environ.get("NAS_IP", "127.0.0.1")
NAS_PORT = int(os.environ.get("NAS_PORT", 3799))
RADIUS_SECRET = os.environ.get("RADIUS_SECRET", "testing123")


def get_client_ip(request):
    """Extrait l'adresse IP réelle du client (Proxy / pfSense / Direct)"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def home_view(request):
    """Portail d'accueil avec logo d'entreprise et récupération des paramètres NAS"""
    enterprise = Enterprise.objects.first()

    mac = request.GET.get('mac') or request.GET.get('client_mac', '')
    ip = request.GET.get('ip') or get_client_ip(request)
    redirurl = request.GET.get('redirurl', 'http://google.com')

    if mac:
        request.session['client_mac'] = mac
    if ip:
        request.session['client_ip'] = ip
    if redirurl:
        request.session['redirurl'] = redirurl

    context = {
        'enterprise': enterprise,
        'query_params': request.GET.urlencode(),
    }
    return render(request, 'index.html', context)


def forfaits_view(request):
    """Affichage du catalogue des forfaits disponibles"""
    forfaits = Forfait.objects.filter(actif=True).prefetch_related('contenus', 'prises')
    enterprise = Enterprise.objects.first()
    query_params = request.GET.urlencode()

    context = {
        'forfaits': forfaits,
        'enterprise': enterprise,
        'query_params': query_params,
    }
    return render(request, 'forfaits.html', context)


def recuperation_informations_view(request, forfait_id):
    """Collecte des informations signalétiques de l'utilisateur"""
    forfait = get_object_or_404(Forfait, id=forfait_id, actif=True)
    query_params = request.GET.urlencode()

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            client_mac = request.GET.get('mac') or request.session.get('client_mac')
            if not client_mac:
                client_mac = f"AA:BB:CC:{uuid.uuid4().hex[:6].upper()}"

            clean_mac = client_mac.upper().replace('-', ':')
            client_ip = request.GET.get('ip') or request.session.get('client_ip') or get_client_ip(request)

            service = data.get('pole_service')
            enterprise = data.get('enterprise')

            with transaction.atomic():
                user, _ = User.objects.update_or_create(
                    username=clean_mac,
                    defaults={
                        'nom': data['nom'],
                        'prenom': data['prenom'],
                        'numero': data['numero'],
                        'mac_adresse': clean_mac,
                        'ip_adresse': client_ip,
                        'pole_service': service,
                        'enterprise': enterprise,
                    }
                )

                souscription = Souscription.objects.create(
                    user=user,
                    forfait=forfait,
                    operateur=Operator.objects.first(),
                    numero_paiement=data['numero'],
                    montant_paye=forfait.prix,
                    statut=Souscription.StatutSouscription.EN_ATTENTE
                )

            target_url = reverse('paiement', kwargs={'souscription_id': souscription.id})
            if query_params:
                target_url += f"?{query_params}"
            return redirect(target_url)
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = RegistrationForm()

    context = {
        'forfait': forfait,
        'form': form,
        'query_params': query_params,
    }
    return render(request, 'registration.html', context)


def paiement_view(request, souscription_id):
    """Sélection de l'opérateur et du numéro de paiement"""
    souscription = get_object_or_404(
        Souscription, id=souscription_id, statut=Souscription.StatutSouscription.EN_ATTENTE
    )
    operateurs = Operator.objects.all()
    query_params = request.GET.urlencode()

    if request.method == 'POST':
        operator_id = request.POST.get('operator_id')
        numero_paiement = request.POST.get('numero_paiement', '').strip()

        if not operator_id or not numero_paiement:
            messages.error(request, "Veuillez sélectionner un opérateur et indiquer le numéro de paiement.")
        else:
            operateur = get_object_or_404(Operator, id=operator_id)
            souscription.operateur = operateur
            souscription.numero_paiement = numero_paiement
            souscription.save()

            target_url = reverse('recapitulatif_paiement', kwargs={'souscription_id': souscription.id})
            if query_params:
                target_url += f"?{query_params}"
            return redirect(target_url)

    context = {
        'souscription': souscription,
        'forfait': souscription.forfait,
        'operateurs': operateurs,
        'query_params': query_params,
    }
    return render(request, 'payement.html', context)


def recapitulatif_paiement_view(request, souscription_id):
    """Récapitulatif avant la validation finale"""
    souscription = get_object_or_404(
        Souscription, id=souscription_id, statut=Souscription.StatutSouscription.EN_ATTENTE
    )
    query_params = request.GET.urlencode()

    if request.method == 'POST':
        target_url = reverse('traiter_paiement', kwargs={'souscription_id': souscription.id})
        if query_params:
            target_url += f"?{query_params}"
        return redirect(target_url)

    context = {
        'souscription': souscription,
        'forfait': souscription.forfait,
        'operateur': souscription.operateur,
        'user': souscription.user,
        'query_params': query_params,
    }
    return render(request, 'recap.html', context)


def traiter_paiement_view(request, souscription_id):
    """Validation instantanée (cas d'école) et provisionnement FreeRADIUS"""
    souscription = get_object_or_404(Souscription, id=souscription_id)
    forfait = souscription.forfait
    user = souscription.user

    if souscription.statut == Souscription.StatutSouscription.EN_ATTENTE:
        with transaction.atomic():
            souscription.statut = Souscription.StatutSouscription.ACTIF
            souscription.transaction_id = f"SIMULATED-TRX-{uuid.uuid4().hex[:10].upper()}"
            souscription.date_expiration = timezone.now() + timezone.timedelta(minutes=forfait.duree_minutes)
            souscription.save()

            mac_user = user.username

            # Nettoyage des anciennes règles RADIUS associées à cette MAC
            RadCheck.objects.filter(username=mac_user).delete()
            RadReply.objects.filter(username=mac_user).delete()

            # Attributs d'authentification FreeRADIUS
            RadCheck.objects.create(
                username=mac_user, attribute='Cleartext-Password', op=':=', value=mac_user
            )
            RadCheck.objects.create(
                username=mac_user, attribute='Simultaneous-Use', op=':=', value=str(forfait.simultaneous_use)
            )

            # Session-Timeout (durée de validité convertie en secondes)
            timeout_seconds = forfait.duree_minutes * 60
            if timeout_seconds > 0:
                RadReply.objects.create(
                    username=mac_user, attribute='Session-Timeout', op='=', value=str(timeout_seconds)
                )

            # Quota de données
            if forfait.quota_octets and forfait.quota_octets > 0:
                RadCheck.objects.create(
                    username=mac_user, attribute='Max-Data-Quota', op=':=', value=str(forfait.quota_octets)
                )

            # QoS / Bande passante WISPr
            if forfait.bandwidth_max_down and forfait.bandwidth_max_down > 0:
                RadReply.objects.create(
                    username=mac_user, attribute='WISPr-Bandwidth-Max-Down', op='=', value=str(forfait.bandwidth_max_down)
                )
            if forfait.bandwidth_max_up and forfait.bandwidth_max_up > 0:
                RadReply.objects.create(
                    username=mac_user, attribute='WISPr-Bandwidth-Max-Up', op='=', value=str(forfait.bandwidth_max_up)
                )

            Connexion.objects.create(
                user=user,
                souscription=souscription,
                adresse_ip=user.ip_adresse,
                adresse_mac=user.mac_adresse,
                status_connexion=Connexion.StatutConnexion.ACTIF
            )

    return redirect('succes_connexion', souscription_id=souscription.id)


def succes_connexion_view(request, souscription_id):
    """Dashboard de suivi de consommation pour l'utilisateur connecté"""
    souscription = get_object_or_404(Souscription, id=souscription_id)
    connexion = Connexion.objects.filter(souscription=souscription).first()

    # Récupération de la consommation active via FreeRADIUS Accounting
    rad_acct = RadAcct.objects.filter(username=souscription.user.username, acctstoptime__isnull=True).first()

    bytes_in = rad_acct.acctinputoctets if rad_acct and rad_acct.acctinputoctets else 0
    bytes_out = rad_acct.acctoutputoctets if rad_acct and rad_acct.acctoutputoctets else 0
    total_consomme = bytes_in + bytes_out

    if connexion and total_consomme > 0:
        connexion.octets_entrants = bytes_in
        connexion.octets_sortants = bytes_out
        connexion.save(update_fields=['octets_entrants', 'octets_sortants'])

    quota_total = souscription.forfait.quota_octets
    if quota_total > 0:
        quota_restant_octets = max(0, quota_total - total_consomme)
        quota_restant = f"{round(quota_restant_octets / (1024 ** 2), 2)} Mo"
    else:
        quota_restant = "Illimité"

    context = {
        'souscription': souscription,
        'user': souscription.user,
        'forfait': souscription.forfait,
        'connexion': connexion,
        'total_consomme': f"{round(total_consomme / (1024 ** 2), 2)} Mo",
        'quota_restant': quota_restant,
        'redirurl': request.session.get('redirurl', 'http://google.com'),
    }
    return render(request, 'success.html', context)


def couper_acces_utilisateur(mac_adresse, nas_ip=NAS_IP, secret=RADIUS_SECRET, nas_port=NAS_PORT):
    """Permet de couper manuellement la session d'un utilisateur (CoA Disconnect)"""
    cmd = ["radclient", "-x", f"{nas_ip}:{nas_port}", "disconnect", secret]
    input_data = f"User-Name={mac_adresse}\n".encode('utf-8')
    try:
        res = subprocess.run(cmd, input=input_data, capture_output=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False
