


class SectionOneCalculator:

    def __init__(self, data):
        self.data = data
        self.medications = {}
        self._set_medications()

    def _set_medications(self):
        categories = [
            'blood_thinner',
            'aspirin',
            'plavix',
            'statin',
            'antiplatelet',
            'hypoglycemic',
            'antihypertensive',
        ]

        result = {category: (False, False) for category in categories}
        meds = self.data.get('medications', {})

        for med_name, info in meds.items():
            classification = info.get('classification')
            instructions = info.get('instructions', '')
            compliance_str = info.get('compliance')

            prescribed = True

            compliant = False
            if isinstance(compliance_str, str):
                compliant = 'yes' in compliance_str.lower() or 'compliant' in compliance_str.lower()

            # Handle aspirin based on name
            if isinstance(med_name, str) and 'aspirin' in med_name.lower():
                result['aspirin'] = (prescribed, compliant)

            # Match classification categories
            if isinstance(classification, str):
                classification = classification.lower()
                for category in categories:
                    if category == 'aspirin':
                        continue
                    if category in classification:
                        result[category] = (prescribed, compliant)

        self.medications = result


    def score_cardioembolic(self):
        meds = self.medications
        history = self.data.get('history', {})
        ldl = self.data.get('lab_values', {}).get('ldl')
        smoker = history.get('smoker')

        if not meds['blood_thinner'][0]:
            return 6.3
        if meds['blood_thinner'][0] and not meds['blood_thinner'][1]:
            return 6.3
        if ldl is not None and ldl > 71:
            return 2.6
        if smoker:
            return 1.6
        return 0

    def score_large_vessel(self):
        meds = self.medications
        history = self.data.get('history', {})
        ldl = self.data.get('lab_values', {}).get('ldl')
        afib = history.get('afib')

        if not meds['aspirin'][0] and not meds['plavix'][0]:
            if history.get('carotid_stenosis') and not history.get('carotid_imaging_6mo', False):
                return 5.7
            return 6.3
        if not any(meds[med][1] for med in ['aspirin', 'statin', 'plavix']):
            return 6.3
        if not meds['statin'][0] and ldl is not None and ldl > 71:
            return 6.3
        if afib:
            return 4.2
        return 0

    def score_small_vessel(self):
        meds = self.medications
        history = self.data.get('history', {})
        ldl = self.data.get('lab_values', {}).get('ldl')
        ha1c = self.data.get('lab_values', {}).get('ha1c')
        smoker = history.get('smoker')
        afib = history.get('afib')

        if not any(meds[med][0] for med in ['blood_thinner', 'aspirin', 'plavix', 'antiplatelet']):
            return 6.3
        if not any(meds[med][1] for med in ['aspirin', 'plavix', 'statin', 'antiplatelet']):
            return 6.3
        if not any(meds[med][1] for med in ['hypoglycemic', 'antihypertensive']):
            if ha1c is not None and ha1c > 6.5:
                return 5.2
            return 6.3
        if not meds['statin'][0] and ldl is not None and ldl > 71:
            return 6.3
        if smoker:
            return 6.4
        if afib:
            return 4.2
        return 0

    def score_other(self):
        history = self.data.get('history', {})
        smoker = history.get('smoker')
        intracranial_atherosclerosis = history.get('intracranial_atherosclerosis')

        if intracranial_atherosclerosis is False:
            return 2.6 if smoker else 1.6
        if intracranial_atherosclerosis is True:
            return 6.3
        return 0

    def score_cryptogenic(self):
        meds = self.medications
        history = self.data.get('history', {})
        ha1c = self.data.get('lab_values', {}).get('ha1c')
        ldl = self.data.get('lab_values', {}).get('ldl')
        smoker = history.get('smoker')
        cpap_rx = history.get('cpap_prescription')
        cpap_use = history.get('cpap_usage')
        osa = history.get('osa')

        if not any(meds[med][0] for med in ['blood_thinner', 'aspirin', 'plavix', 'antiplatelet']):
            return 6.3
        if not any(meds[med][1] for med in ['aspirin', 'plavix', 'antiplatelet']):
            return 6.3
        if meds['statin'][0] and ldl is not None and ldl > 71:
            return 2.6
        if smoker and all(val[1] for val in meds.values()):
            return 1.6
        if osa and cpap_rx and not cpap_use:
            return 1.7
        if not meds['hypoglycemic'][0] and ha1c is not None and ha1c > 7:
            return 1.1
        if not meds['hypoglycemic'][1] and ha1c is not None and ha1c > 6.5:
            return 1.1
        return 0

    def score_na(self):
        meds = self.medications
        history = self.data.get('history', {})
        ha1c = self.data.get('lab_values', {}).get('ha1c')
        osa = history.get('osa')
        cpap_rx = history.get('cpap_prescription')
        cpap_use = history.get('cpap_usage')

        if osa and cpap_rx and not cpap_use:
            return 1.7
        if not meds['hypoglycemic'][0] and ha1c is not None and ha1c > 7:
            return 1.1
        if not meds['hypoglycemic'][1] and ha1c is not None and ha1c > 6.5:
            return 1.1
        return 0
