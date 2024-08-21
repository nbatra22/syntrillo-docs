import os

from syntrillo.system.dot_env_loader import DotEnvFileLoader

class IframeValidator:
    """

    Class to handle iframe request validation.

    """

    ALLOWED_DOMAINS = [
    "https://securestaging.gethealthie.com/",
    "https://secure.gethealthie.com/",
    "https://patients.syntrillo.com/",
    "127.0.0.1",
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
        _ = DotEnvFileLoader()
        org = os.getenv('HEALTHIE_ORGANIZATION')

        log = { 'referer': referer, 'origin': origin, 'organization': org }

        if referer:
            return any(referer.startswith(domain) for domain in self.ALLOWED_DOMAINS), log
        elif origin:
            return any(origin.startswith(domain) for domain in self.ALLOWED_DOMAINS), log
        elif org == 'staging':
            return True, log

        return False, log

