
from flask import request

from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement


class PostManager:
    """
    Retrieve the form data from the POST request
    : these are passed from the healthie_iframe_provider_tab index.html
    : healthie_user_id, is None, unless in panic mode
    """

    def __init__(self, request):
        """
        Initialize the PostManager object
        """
        self.request = request

        # get what's posted
        self.healthie_provider_id = request.form.get('healthie_provider_id')
        self.posted_healthie_user_id = request.form.get('healthie_user_id') # should be 'hidden|not transmitted|None' unless in panic mode
        self.temporary_lookup_code = request.form.get('temporary_lookup_code')
        patient_not_registered_at_syntrillo_str = request.form.get('patient_not_registered_at_syntrillo')
        self.patient_not_registered_at_syntrillo=(patient_not_registered_at_syntrillo_str == 'True')

        # look up for syntrillo_internal_key
        if self.temporary_lookup_code is not None:
            temporary_lookup_codes_manager = TemporaryLookUpCodesManagement()
            self.syntrillo_internal_key = temporary_lookup_codes_manager.retrieve_syntrillo_internal_key(
                self.temporary_lookup_code,
                purpose=TemporaryLookUpCodesManagement.PURPOSE_HEALTHIE_IFRAME
                )

            # get all pseudonyms
            lookup_manager = LookUpCodesManagement()
            self.pseudonyms = lookup_manager.retrieve_entry_by_internal_key(self.syntrillo_internal_key)

        else:
            self.syntrillo_internal_key = None
            self.pseudonyms = None



