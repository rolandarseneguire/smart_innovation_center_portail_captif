import math
from django.contrib import admin, messages
from django.utils.html import format_html
from .models import (
    Enterprise,
    Service,
    User,
    Operator,
    Prise,
    Contenu,
    Forfait,
    Souscription,
    Connexion,
    RadiusAcctLog,
    Nas,
    RadCheck,
    RadReply,
    RadAcct,
)


def format_bytes(bytes_val):
    if bytes_val is None or bytes_val == 0:
        return "0 Octet"
    k = 1024
    sizes = ['Octets', 'Ko', 'Mo', 'Go', 'To']
    i = int(math.floor(math.log(bytes_val, k)))
    p = math.pow(k, i)
    s = round(bytes_val / p, 2)
    return f"{s} {sizes[i]}"


def format_bps(bps_val):
    if bps_val is None or bps_val == 0:
        return "0 bps"
    if bps_val >= 1000000:
        return f"{round(bps_val / 1000000, 2)} Mbps"
    elif bps_val >= 1000:
        return f"{round(bps_val / 1000, 2)} Kbps"
    return f"{bps_val} bps"


@admin.register(Enterprise)
class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'created_at', 'updated_at')
    search_fields = ('nom',)
    ordering = ('nom',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service', 'created_at')
    search_fields = ('service',)
    ordering = ('service',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'numero',
        'username',
        'mac_adresse',
        'ip_adresse',
        'pole_service',
        'enterprise',
        'created_at',
    )
    list_filter = ('pole_service', 'enterprise', 'created_at')
    search_fields = ('nom', 'prenom', 'numero', 'username', 'mac_adresse', 'ip_adresse')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description="Nom complet")
    def full_name(self, obj):
        return f"{obj.prenom} {obj.nom}"


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'created_at', 'updated_at')
    search_fields = ('nom', 'code')


@admin.register(Prise)
class PriseAdmin(admin.ModelAdmin):
    list_display = ('prise',)
    search_fields = ('prise',)


@admin.register(Contenu)
class ContenuAdmin(admin.ModelAdmin):
    list_display = ('libelle',)
    search_fields = ('libelle',)


@admin.register(Forfait)
class ForfaitAdmin(admin.ModelAdmin):
    list_display = (
        'titre',
        'prix_display',
        'duree_display',
        'quota_display',
        'down_display',
        'up_display',
        'actif',
    )
    list_filter = ('actif', 'prises')
    search_fields = ('titre',)
    filter_horizontal = ('prises', 'contenus')
    ordering = ('prix', 'duree_minutes')

    @admin.display(description="Prix")
    def prix_display(self, obj):
        return f"{obj.prix:,} FCFA".replace(',', ' ')

    @admin.display(description="Durée")
    def duree_display(self, obj):
        return obj.duree_formatted

    @admin.display(description="Quota Data")
    def quota_display(self, obj):
        return obj.quota_formatted

    @admin.display(description="Débit Max Down")
    def down_display(self, obj):
        return obj.bandwidth_down_formatted

    @admin.display(description="Débit Max Up")
    def up_display(self, obj):
        return obj.bandwidth_up_formatted


@admin.register(Souscription)
class SouscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'forfait',
        'operateur',
        'transaction_id',
        'numero_paiement',
        'montant_paye_display',
        'statut_badge',
        'date_heure_souscription',
        'date_expiration',
    )
    list_filter = ('statut', 'operateur', 'date_heure_souscription')
    search_fields = (
        'transaction_id',
        'numero_paiement',
        'user__nom',
        'user__prenom',
        'user__username',
        'user__numero',
    )
    date_hierarchy = 'date_heure_souscription'
    readonly_fields = ('date_heure_souscription',)

    @admin.display(description="Montant Payé")
    def montant_paye_display(self, obj):
        return f"{obj.montant_paye:,} FCFA".replace(',', ' ')

    @admin.display(description="Statut")
    def statut_badge(self, obj):
        colors = {
            'EN_ATTENTE': '#ffc107',
            'ACTIF': '#28a745',
            'EXPIRE': '#6c757d',
            'ECHEC': '#dc3545',
        }
        color = colors.get(obj.statut, '#000000')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_statut_display(),
        )


@admin.register(Connexion)
class ConnexionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'status_badge',
        'adresse_ip',
        'adresse_mac',
        'download_display',
        'upload_display',
        'total_display',
        'debut_connexion',
        'derniere_mise_a_jour',
        'actions_reseau',
    )
    list_filter = ('status_connexion', 'debut_connexion')
    search_fields = (
        'acct_session_id',
        'adresse_ip',
        'adresse_mac',
        'user__nom',
        'user__prenom',
        'user__username',
    )
    date_hierarchy = 'debut_connexion'
    readonly_fields = (
        'debut_connexion',
        'derniere_mise_a_jour',
        'fin_connexion',
        'octets_entrants',
        'octets_sortants',
    )
    actions = ['forcer_deconnexion_utilisateurs']

    @admin.display(description="Statut")
    def status_badge(self, obj):
        colors = {
            'ACTIF': '#28a745',
            'TERMINE': '#6c757d',
            'COUPE': '#dc3545',
            'EXPIRE': '#fd7e14',
            'ECHEC': '#bd2130',
        }
        color = colors.get(obj.status_connexion, '#000000')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_connexion_display(),
        )

    @admin.display(description="Download")
    def download_display(self, obj):
        return format_bytes(obj.octets_entrants)

    @admin.display(description="Upload")
    def upload_display(self, obj):
        return format_bytes(obj.octets_sortants)

    @admin.display(description="Total Consommé")
    def total_display(self, obj):
        return format_bytes(obj.total_octets)

    @admin.display(description="Action Réseau")
    def actions_reseau(self, obj):
        if obj.status_connexion == 'ACTIF':
            return format_html(
                '<a class="button" style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 4px;" '
                'href="javascript:void(0);" onclick="alert(\'Demande de déconnexion CoA émise pour la MAC: {}\');">Couper Accès</a>',
                obj.adresse_mac
            )
        return "-"

    @admin.action(description="Couper immédiatement l'accès réseau (PoD RADIUS)")
    def forcer_deconnexion_utilisateurs(self, request, queryset):
        count = 0
        for connexion in queryset.filter(status_connexion='ACTIF'):
            from .views import couper_acces_utilisateur
            if connexion.adresse_mac and couper_acces_utilisateur(connexion.adresse_mac):
                connexion.status_connexion = 'COUPE'
                connexion.save()
                count += 1

        if count > 0:
            self.message_user(request, f"{count} session(s) ont été coupées avec succès.", messages.SUCCESS)
        else:
            self.message_user(request, "Aucune session active à couper dans la sélection.", messages.WARNING)


@admin.register(RadiusAcctLog)
class RadiusAcctLogAdmin(admin.ModelAdmin):
    list_display = (
        'acct_session_id',
        'username',
        'download_display',
        'upload_display',
        'timestamp',
    )
    search_fields = ('acct_session_id', 'username')
    list_filter = ('timestamp',)
    readonly_fields = ('acct_session_id', 'username', 'input_octets', 'output_octets', 'timestamp')

    @admin.display(description="Download")
    def download_display(self, obj):
        return format_bytes(obj.input_octets)

    @admin.display(description="Upload")
    def upload_display(self, obj):
        return format_bytes(obj.output_octets)


@admin.register(Nas)
class NasAdmin(admin.ModelAdmin):
    list_display = ('nasname', 'shortname', 'type', 'ports', 'secret', 'server', 'description')
    search_fields = ('nasname', 'shortname', 'description')


@admin.register(RadCheck)
class RadCheckAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'attribute', 'op', 'value')
    search_fields = ('username', 'attribute', 'value')
    list_filter = ('attribute', 'op')


@admin.register(RadReply)
class RadReplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'attribute', 'op', 'value')
    search_fields = ('username', 'attribute', 'value')
    list_filter = ('attribute', 'op')


@admin.register(RadAcct)
class RadAcctAdmin(admin.ModelAdmin):
    list_display = (
        'radacctid',
        'username',
        'acctsessionid',
        'nasipaddress',
        'framedipaddress',
        'acctstarttime',
        'acctstoptime',
        'acctsessiontime',
        'download_display',
        'upload_display',
        'acctterminatecause',
    )
    search_fields = ('username', 'acctsessionid', 'framedipaddress', 'callingstationid')
    list_filter = ('acctstarttime', 'acctterminatecause', 'nasipaddress')
    readonly_fields = [f.name for f in RadAcct._meta.fields]

    @admin.display(description="Download")
    def download_display(self, obj):
        return format_bytes(obj.acctinputoctets)

    @admin.display(description="Upload")
    def upload_display(self, obj):
        return format_bytes(obj.acctoutputoctets)