import os

from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets

class IframeValidator:
    """

    Class to handle iframe request validation.

    """

    ALLOWED_DOMAINS_PRODUCTION = [
    "https://secure.gethealthie.com/",
    "https://patients.syntrillo.com/",
    "https://api.prod.syntrillo-clinic-backend.com/",
    ]

    def __init__(self):
        pass

    def is_request_allowed(self, request):
        """
        Checks if the request comes from an allowed domain.

        Args:
            request (Flask request object): The Flask request object.

        Returns:
            bool,dict : True if allowed, False otherwise. The dict contains the referer and origin headers.

        """
        referer = request.headers.get('Referer')
        origin = request.headers.get('Origin')

        secrets = LocalEnvironmentAndSecrets(load_healthie_secrets=True)
        org = secrets.get_healthie_organization()

        log = { 'referer': referer, 'origin': origin, 'organization': org }

        if org == 'staging':
            return True, log

        else:

            referer_is_valid = False
            origin_is_valid = False

            if referer:
                referer += '/'
                referer_is_valid = any(referer.startswith(domain) for domain in self.ALLOWED_DOMAINS_PRODUCTION), log

            if origin:
                origin += '/'
                origin_is_valid = any(origin.startswith(domain) for domain in self.ALLOWED_DOMAINS_PRODUCTION), log

            return referer_is_valid or origin_is_valid, log


