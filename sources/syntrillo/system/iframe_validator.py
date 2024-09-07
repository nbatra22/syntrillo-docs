# Path: ./sources/syntrillo/system/iframe_validator.py
import os

from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets

class IframeValidator:
    """

    Class to handle iframe request validation.

    """

    # must include trailing slash to avoid subdomains
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

        Returns a tupple:
        - True if the request is allowed, False otherwise.
        - A dictionary containing logs of the referer and origin headers.

        Args:
            request (Flask request object): The Flask request object.

        Returns:
            bool,dict : True if allowed, False otherwise. The dict contains the referer and origin headers.

        """
        referer = request.headers.get('Referer')
        origin = request.headers.get('Origin')

        secrets = LocalEnvironmentAndSecrets(load_healthie_secrets=True)
        org = secrets.get_healthie_organization()

        referer_is_valid = False
        origin_is_valid = False
        request_is_valid = False

        if org == 'staging':
            request_is_valid = True

        else:

            if referer:
                referer += '/' if not referer.endswith('/') else ''
                referer_is_valid = any(referer.startswith(domain) for domain in self.ALLOWED_DOMAINS_PRODUCTION)

            if origin:
                origin += '/' if not origin.endswith('/') else ''
                origin_is_valid = any(origin.startswith(domain) for domain in self.ALLOWED_DOMAINS_PRODUCTION)

            request_is_valid = referer_is_valid or origin_is_valid


        log = {
            'referer': referer,
            'origin': origin,
            'organization': org,
            'referer_is_valid': referer_is_valid,
            'origin_is_valid': origin_is_valid,
            'request_is_valid': request_is_valid,
        }

        self.request_is_valid = request_is_valid
        self.log = log

        return request_is_valid, log
