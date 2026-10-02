import time
import threading
import subprocess
import os
from django.db.models import Sum

NAS_IP = os.environ.get("NAS_IP", "192.168.1.40")  # IP de pfSense
NAS_PORT = int(os.environ.get("NAS_PORT", 3799))  # Port CoA
RADIUS_SECRET = os.environ.get("RADIUS_SECRET", "testing123")  # Secret partagé RADIUS


def couper_session_nas(username):
    """Émet un paquet Disconnect-Request (CoA) à pfSense."""
    cmd = ["radclient", "-x", f"{NAS_IP}:{NAS_PORT}", "disconnect", RADIUS_SECRET]
    input_data = f"User-Name={username}\n".encode('utf-8')
    try:
        res = subprocess.run(cmd, input=input_data, capture_output=True, timeout=5)
        return res.returncode == 0
    except FileNotFoundError:
        print(f"[ERREUR CoA] L'outil 'radclient' n'est pas installé sur le système.")
        return False
    except Exception as e:
        print(f"[EXCEPT CoA] Erreur pour {username}: {e}")
        return False


def verifier_et_couper_quotas():
    """Vérifie les quotas et déconnecte les utilisateurs ayant dépassé leur limite."""
    from .models import RadAcct, RadCheck, Souscription, Connexion

    sessions_actives = RadAcct.objects.filter(acctstoptime__isnull=True)
    usernames_actifs = sessions_actives.values_list('username', flat=True).distinct()

    for username in usernames_actifs:
        stats = RadAcct.objects.filter(username=username).aggregate(
            total_in=Sum('acctinputoctets'),
            total_out=Sum('acctoutputoctets')
        )
        total_consomme = (stats['total_in'] or 0) + (stats['total_out'] or 0)

        quota_check = RadCheck.objects.filter(username=username, attribute='Max-Data-Quota').first()

        if quota_check:
            try:
                quota_max = int(quota_check.value)
            except ValueError:
                continue

            if total_consomme >= quota_max:
                print(f"[ALERT QUOTA] {username} a dépassé son quota. Coupure en cours...")
                if couper_session_nas(username):
                    Souscription.objects.filter(
                        user__username=username,
                        statut=Souscription.StatutSouscription.ACTIF
                    ).update(statut=Souscription.StatutSouscription.EXPIRE)

                    Connexion.objects.filter(
                        adresse_mac=username,
                        status_connexion=Connexion.StatutConnexion.ACTIF
                    ).update(status_connexion=Connexion.StatutConnexion.INACTIF)


def lanser_boucle_verification(intervalle_secondes=30):
    """Boucle infinie exécutée dans un Thread séparé."""
    while True:
        try:
            verifier_et_couper_quotas()
        except Exception as e:
            print(f"[ERROR CHECK QUOTAS] {e}")
        time.sleep(intervalle_secondes)


def demarrer_background_checker():
    """Démarre le thread d'arrière-plan."""
    thread = threading.Thread(target=lanser_boucle_verification, daemon=True)
    thread.start()
    print("=== Worker d'arrière-plan check_quotas démarré ===")
