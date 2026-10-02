from django.apps import AppConfig
import os
class CaptivePortalConfig(AppConfig):
    name = 'captive_portal'

    def ready(self):
        # RUN_MAIN permet d'éviter que le thread se lance 2 fois à cause du reloader de runserver
        if os.environ.get('RUN_MAIN') == 'true':
            from .check_quotas import demarrer_background_checker
            demarrer_background_checker()
