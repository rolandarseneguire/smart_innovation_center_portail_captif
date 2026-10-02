import uuid
import secrets
import string
from django.db import models
from django.utils import timezone


def generate_secure_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class Enterprise(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=150, verbose_name="Nom de l'entreprise")
    logo = models.ImageField(
        upload_to='enterprises/logos/', null=True, blank=True, verbose_name="Logo de l'entreprise"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        db_table = 'enterprise'
        verbose_name = 'Entreprise'
        verbose_name_plural = 'Entreprises'

    def __str__(self):
        return self.nom


class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.CharField(max_length=100, verbose_name="Nom du service")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        db_table = 'service'
        verbose_name = 'Service / Pôle'
        verbose_name_plural = 'Services / Pôles'

    def __str__(self):
        return self.service


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    numero = models.CharField(max_length=20, verbose_name="Numéro de téléphone", db_index=True)

    username = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Username RADIUS / MAC Cleaned",
        help_text="Format standardisé (ex: AA:BB:CC:DD:EE:FF)"
    )
    password = models.CharField(
        max_length=128,
        default=generate_secure_password,
        verbose_name="Password RADIUS"
    )

    mac_adresse = models.CharField(max_length=17, null=True, blank=True, verbose_name="Adresse MAC", db_index=True)
    ip_adresse = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dernière IP connue")

    pole_service = models.ForeignKey(
        'Service',
        on_delete=models.SET_NULL,
        related_name='pole_de_service_users',
        null=True,
        blank=True,
        verbose_name="Pôle de service"
    )
    enterprise = models.ForeignKey(
        'Enterprise',
        on_delete=models.SET_NULL,
        related_name='network_users',
        null=True,
        blank=True,
        verbose_name="Entreprise"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'enregistrement")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        db_table = 'network_users'
        verbose_name = 'Utilisateur Réseau'
        verbose_name_plural = 'Utilisateurs Réseau'

    def __str__(self):
        service_nom = self.pole_service.service if self.pole_service else "Sans service"
        return f"{self.prenom} {self.nom} - {service_nom} ({self.numero})"


class Operator(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=150, unique=True, verbose_name="Nom de l'opérateur")
    logo = models.ImageField(
        upload_to='operators/logos/', null=True, blank=True, verbose_name="Logo de l'opérateur"
    )
    code = models.CharField(max_length=20, null=True, blank=True, verbose_name="Code API Opérateur (ex: OM, WAVE)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        db_table = 'operator'
        verbose_name = 'Opérateur'
        verbose_name_plural = 'Opérateurs'

    def __str__(self):
        return self.nom


class Prise(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prise = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Prise / Port réseau",
        help_text="Ex: Prise RJ45-A101"
    )

    class Meta:
        db_table = 'prise'
        verbose_name = 'Prise'
        verbose_name_plural = 'Prises'

    def __str__(self):
        return self.prise


class Contenu(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    libelle = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Libellé du contenu",
        help_text="Ex: Accès Wi-Fi 5G, Support 24/7, Débit 10 Mbps"
    )

    class Meta:
        db_table = 'contenu'
        verbose_name = 'Contenu disponible'
        verbose_name_plural = 'Contenus disponibles'

    def __str__(self):
        return self.libelle


class Forfait(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(max_length=150, verbose_name="Titre du forfait")
    prix = models.IntegerField(default=0, verbose_name="Prix (FCFA)")
    duree_minutes = models.IntegerField(default=60, verbose_name="Durée de validité (en minutes)")
    simultaneous_use = models.IntegerField(default=1, verbose_name="Sessions simultanées max")

    prises = models.ManyToManyField(
        Prise,
        related_name='forfaits',
        verbose_name="Prises associées / autorisées",
        blank=True,
        help_text="Prises/ports réseau sur lesquels ce forfait est utilisable"
    )

    quota_octets = models.BigIntegerField(
        default=0,
        verbose_name="Quota Data (en Octets)",
        help_text="0 pour Illimité. Exemple: 1 Go = 1073741824 octets"
    )
    bandwidth_max_down = models.IntegerField(
        default=10485760,
        verbose_name="Débit Max Descendant (bps)",
        help_text="WISPr-Bandwidth-Max-Down. Exemple: 10 Mbps = 10485760"
    )
    bandwidth_max_up = models.IntegerField(
        default=5242880,
        verbose_name="Débit Max Montant (bps)",
        help_text="WISPr-Bandwidth-Max-Up. Exemple: 5 Mbps = 5242880"
    )
    actif = models.BooleanField(default=True, verbose_name="Forfait actif")

    contenus = models.ManyToManyField(
        Contenu,
        related_name='forfaits',
        verbose_name="Contenus inclus",
        blank=True
    )

    class Meta:
        db_table = 'forfait'
        verbose_name = 'Forfait'
        verbose_name_plural = 'Forfaits'

    def __str__(self):
        return f"{self.titre} - {self.prix} FCFA ({self.duree_minutes} min)"

    @property
    def duree_formatted(self):
        mins = self.duree_minutes or 0
        if mins < 60:
            return f"{mins} min"
        elif mins < 1440:
            heures = mins // 60
            reste = mins % 60
            return f"{heures}h{f'{reste:02d}' if reste else ''}"
        else:
            jours = mins // 1440
            return f"{jours} Jour{'s' if jours > 1 else ''}"

    @property
    def quota_formatted(self):
        bytes_val = self.quota_octets or 0
        if bytes_val <= 0:
            return "Illimité"
        gb = 1073741824
        mb = 1048576
        if bytes_val >= gb:
            return f"{round(bytes_val / gb, 1)} Go"
        elif bytes_val >= mb:
            return f"{round(bytes_val / mb)} Mo"
        else:
            return f"{round(bytes_val / 1024)} Ko"

    @property
    def bandwidth_down_formatted(self):
        bps = self.bandwidth_max_down or 0
        if bps >= 1000000:
            return f"{round(bps / 1000000)} Mbps"
        elif bps >= 1000:
            return f"{round(bps / 1000)} Kbps"
        return f"{bps} bps"

    @property
    def bandwidth_up_formatted(self):
        bps = self.bandwidth_max_up or 0
        if bps >= 1000000:
            return f"{round(bps / 1000000)} Mbps"
        elif bps >= 1000:
            return f"{round(bps / 1000)} Kbps"
        return f"{bps} bps"


class Souscription(models.Model):
    class StatutSouscription(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        ACTIF = 'ACTIF', 'Actif'
        EXPIRE = 'EXPIRE', 'Expiré'
        ECHEC = 'ECHEC', 'Échec / Annulé'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name='souscriptions', verbose_name="Utilisateur"
    )
    forfait = models.ForeignKey(
        'Forfait', on_delete=models.PROTECT, related_name='souscriptions', verbose_name="Forfait souscrit"
    )
    operateur = models.ForeignKey(
        'Operator', on_delete=models.PROTECT, related_name='souscriptions', verbose_name="Opérateur de paiement"
    )

    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="ID Transaction Paiement",
        help_text="Identifiant unique fourni par la passerelle de paiement (ex: CinetPay)"
    )
    payment_token = models.CharField(
        max_length=128, null=True, blank=True, db_index=True, verbose_name="Jeton de paiement API"
    )

    numero_paiement = models.CharField(
        max_length=20,
        verbose_name="Numéro de téléphone / Paiement"
    )
    montant_paye = models.IntegerField(default=0, verbose_name="Montant payé (FCFA)")
    statut = models.CharField(
        max_length=20,
        choices=StatutSouscription.choices,
        default=StatutSouscription.EN_ATTENTE,
        verbose_name="Statut de la souscription",
        db_index=True
    )
    date_heure_souscription = models.DateTimeField(
        auto_now_add=True, verbose_name="Date et heure de souscription"
    )
    date_expiration = models.DateTimeField(
        null=True, blank=True, verbose_name="Date et heure d'expiration"
    )

    class Meta:
        db_table = 'souscription'
        verbose_name = 'Souscription'
        verbose_name_plural = 'Souscriptions'
        ordering = ['-date_heure_souscription']

    def __str__(self):
        return f"{self.user} - {self.forfait.titre} ({self.get_statut_display()})"


class Connexion(models.Model):
    class StatutConnexion(models.TextChoices):
        ACTIF = 'ACTIF', 'En cours'
        TERMINE = 'TERMINE', 'Terminée'
        COUPE = 'COUPE', 'Coupée par CoA (Quota/Admin)'
        EXPIRE = 'EXPIRE', 'Expirée (Temps dépassé)'
        ECHEC = 'ECHEC', 'Échec de connexion'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name='connexions', verbose_name="Utilisateur"
    )
    souscription = models.ForeignKey(
        'Souscription', on_delete=models.CASCADE, related_name='connexions', verbose_name="Souscription utilisée"
    )
    prise = models.ForeignKey(
        'Prise', on_delete=models.SET_NULL, null=True, blank=True, related_name='connexions',
        verbose_name="Prise utilisée"
    )

    acct_session_id = models.CharField(
        max_length=64, null=True, blank=True, db_index=True, verbose_name="Session ID RADIUS (Acct-Session-Id)"
    )
    nas_ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="IP du NAS / pfSense"
    )

    status_connexion = models.CharField(
        max_length=20,
        choices=StatutConnexion.choices,
        default=StatutConnexion.ACTIF,
        verbose_name="Statut de la connexion",
        db_index=True
    )
    adresse_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="Adresse IP client")
    adresse_mac = models.CharField(max_length=17, null=True, blank=True, verbose_name="Adresse MAC", db_index=True)

    octets_entrants = models.BigIntegerField(default=0, verbose_name="Download (Octets)")
    octets_sortants = models.BigIntegerField(default=0, verbose_name="Upload (Octets)")

    debut_connexion = models.DateTimeField(auto_now_add=True, verbose_name="Début de connexion")
    derniere_mise_a_jour = models.DateTimeField(auto_now=True, verbose_name="Dernier paquet Accounting")
    fin_connexion = models.DateTimeField(null=True, blank=True, verbose_name="Fin de connexion")

    class Meta:
        db_table = 'connexion'
        verbose_name = 'Connexion Réseau'
        verbose_name_plural = 'Connexions Réseau'
        ordering = ['-debut_connexion']

    @property
    def total_octets(self):
        return self.octets_entrants + self.octets_sortants

    def quota_depasse(self):
        quota = self.souscription.forfait.quota_octets
        if quota > 0 and self.total_octets >= quota:
            return True
        return False

    def temps_expire(self):
        if self.souscription.date_expiration and timezone.now() >= self.souscription.date_expiration:
            return True
        return False

    def __str__(self):
        date_str = self.debut_connexion.strftime('%d/%m/%Y %H:%M') if self.debut_connexion else "Nouvelle"
        return f"{self.user} - {self.get_status_connexion_display()} ({date_str})"


class RadiusAcctLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    acct_session_id = models.CharField(max_length=64, db_index=True, verbose_name="Session ID RADIUS")
    username = models.CharField(max_length=64, db_index=True, verbose_name="MAC / Username")
    input_octets = models.BigIntegerField(default=0, verbose_name="Download (AcctInputOctets)")
    output_octets = models.BigIntegerField(default=0, verbose_name="Upload (AcctOutputOctets)")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Horodatage")

    class Meta:
        db_table = 'radius_acct_log'
        verbose_name = 'Journal Accounting RADIUS'
        verbose_name_plural = 'Journaux Accounting RADIUS'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Log {self.username} - {self.acct_session_id}"


class Nas(models.Model):
    id = models.BigAutoField(primary_key=True)
    nasname = models.CharField(max_length=128, db_column='nasname')
    shortname = models.CharField(max_length=32, db_column='shortname', blank=True, null=True)
    type = models.CharField(max_length=30, db_column='type', default='other')
    ports = models.IntegerField(db_column='ports', blank=True, null=True)
    secret = models.CharField(max_length=60, db_column='secret')
    server = models.CharField(max_length=64, db_column='server', blank=True, null=True)
    community = models.CharField(max_length=50, db_column='community', blank=True, null=True)
    description = models.CharField(max_length=200, db_column='description', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'nas'
        verbose_name = 'NAS / Pare-feu (pfSense)'
        verbose_name_plural = 'NAS / Pare-feux (pfSense)'

    def __str__(self):
        return f"{self.shortname or self.nasname} ({self.nasname})"


class RadCheck(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=64, db_column='username', default='')
    attribute = models.CharField(max_length=64, db_column='attribute', default='')
    op = models.CharField(max_length=2, db_column='op', default='==')
    value = models.CharField(max_length=253, db_column='value', default='')

    class Meta:
        managed = False
        db_table = 'radcheck'
        verbose_name = 'FreeRADIUS - Check'
        verbose_name_plural = 'FreeRADIUS - Checks'

    def __str__(self):
        return f"{self.username} - {self.attribute} {self.op} {self.value}"


class RadReply(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=64, db_column='username', default='')
    attribute = models.CharField(max_length=64, db_column='attribute', default='')
    op = models.CharField(max_length=2, db_column='op', default='=')
    value = models.CharField(max_length=253, db_column='value', default='')

    class Meta:
        managed = False
        db_table = 'radreply'
        verbose_name = 'FreeRADIUS - Reply'
        verbose_name_plural = 'FreeRADIUS - Replies'

    def __str__(self):
        return f"{self.username} - {self.attribute} {self.op} {self.value}"


class RadAcct(models.Model):
    radacctid = models.BigAutoField(primary_key=True, db_column='radacctid')
    acctsessionid = models.CharField(max_length=64, db_column='acctsessionid')
    acctuniqueid = models.CharField(max_length=32, db_column='acctuniqueid')
    username = models.CharField(max_length=64, db_column='username', blank=True, null=True)
    realm = models.CharField(max_length=64, db_column='realm', blank=True, null=True)
    nasipaddress = models.GenericIPAddressField(db_column='nasipaddress')
    nasportid = models.CharField(max_length=32, db_column='nasportid', blank=True, null=True)
    nasporttype = models.CharField(max_length=32, db_column='nasporttype', blank=True, null=True)
    acctstarttime = models.DateTimeField(db_column='acctstarttime', blank=True, null=True)
    acctupdatetime = models.DateTimeField(db_column='acctupdatetime', blank=True, null=True)
    acctstoptime = models.DateTimeField(db_column='acctstoptime', blank=True, null=True)
    acctinterval = models.IntegerField(db_column='acctinterval', blank=True, null=True)
    acctsessiontime = models.BigIntegerField(db_column='acctsessiontime', blank=True, null=True)
    acctauthentic = models.CharField(max_length=32, db_column='acctauthentic', blank=True, null=True)
    connectinfo_start = models.CharField(max_length=128, db_column='connectinfo_start', blank=True, null=True)
    connectinfo_stop = models.CharField(max_length=128, db_column='connectinfo_stop', blank=True, null=True)
    acctinputoctets = models.BigIntegerField(db_column='acctinputoctets', blank=True, null=True)
    acctoutputoctets = models.BigIntegerField(db_column='acctoutputoctets', blank=True, null=True)
    calledstationid = models.CharField(max_length=50, db_column='calledstationid', blank=True, null=True)
    callingstationid = models.CharField(max_length=50, db_column='callingstationid', blank=True, null=True)
    acctterminatecause = models.CharField(max_length=32, db_column='acctterminatecause', blank=True, null=True)
    servicetype = models.CharField(max_length=32, db_column='servicetype', blank=True, null=True)
    framedprotocol = models.CharField(max_length=32, db_column='framedprotocol', blank=True, null=True)
    framedipaddress = models.GenericIPAddressField(db_column='framedipaddress', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'radacct'
        verbose_name = 'FreeRADIUS - Session Accounting'
        verbose_name_plural = 'FreeRADIUS - Sessions Accounting'

    def __str__(self):
        return f"{self.username or 'Anonyme'} - Session {self.acctsessionid}"