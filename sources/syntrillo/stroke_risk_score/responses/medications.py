import re
from typing import Optional, Dict
from bs4 import BeautifulSoup

from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

class MedicationParser:
    def __init__(
        self,
        prescription_str: Optional[str] = None,
        adherence_html: Optional[str] = None,
        db_conn=None
    ):
        self.prescription_str = prescription_str
        self.adherence_html = adherence_html
        self.medications = {}
        self.grouped_meds = {
            'blood_thinner': [],
            'cholesterol_medication': [],
            'diabetes_medication': [],
            'blood_pressure_medication': [],
            'other': []
        }
        self.db_conn = db_conn
        self.medication_lookup = self._load_medication_classifications()

        if self.prescription_str:
            self._parse_prescriptions()

        if self.adherence_html:
            self._parse_adherence()

    def _load_medication_classifications(self) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Load medication names and their classification/supercategory into a dict.
        Keys are lowercased medication names.
        Values are dicts with `classification` and `supercategory`.
        """
        query = "SELECT medication_name, classification, supercategory FROM medication_classifications;"
        cursor = self.db_conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()

        return {
            med.lower(): {
                "classification": classification,
                "supercategory": supercategory
            }
            for med, classification, supercategory in rows
        }

    def _clean_name(self, name: str) -> str:
        keywords_to_remove = ["oral", "tablet", "support", "miscellaneous"]
        cleaned = name.lower()
        for keyword in keywords_to_remove:
            cleaned = cleaned.replace(keyword, "")
        return cleaned.strip()

    def _match_medication_classification_and_supercategory(self, raw_name: str) -> Dict[str, Optional[str]]:
        cleaned = self._clean_name(raw_name)

        for med_name, info in self.medication_lookup.items():
            if med_name in cleaned:
                return {
                    "classification": info["classification"],
                    "supercategory": info["supercategory"]
                }

        # Build classification → supercategory map
        classification_to_supercategory = {
            info["classification"]: info["supercategory"]
            for info in self.medication_lookup.values()
            if info["classification"]
        }

        all_classifications = classification_to_supercategory.keys()
        all_supercategories = {info["supercategory"] for info in self.medication_lookup.values()}

        # Match by classification
        for classification in all_classifications:
            if classification in cleaned:
                return {
                    "classification": classification,
                    "supercategory": classification_to_supercategory.get(classification)
                }

        # Match by supercategory
        for supercategory in all_supercategories:
            if supercategory and supercategory in cleaned:
                return {
                    "classification": None,
                    "supercategory": supercategory
                }

        return {
            "classification": None,
            "supercategory": None
        }


    # def _parse_prescriptions(self):
    #     blocks = self.prescription_str.split('\\\\')

    #     for block in blocks:
    #         parts = block.split('\r|\r|')

    #         if len(parts) >= 2:
    #             raw_name = parts[0].strip().lower()
    #             instructions = parts[1].split('\r|')[1].strip().lower() if len(parts[1].split('\r|')) > 1 else None
    #             info = self._match_medication_classification_and_supercategory(raw_name)

    #             if raw_name:
    #                 self.medications[raw_name] = {
    #                     "classification": info["classification"],
    #                     "supercategory": info["supercategory"],
    #                     "instructions": instructions,
    #                     "compliance": None
    #                 }

    def _parse_prescriptions(self):
        blocks = self.prescription_str.split('\\\\')

        for block in blocks:
            fields = [field.strip().lower() for field in block.split('\r|') if field.strip()]
            if not fields:
                continue

            raw_name = fields[0]

            # Match instruction line
            instructions = next((f for f in fields if re.match(r'^(take|chew|spray|apply)', f)), None)

            # Match dosage (e.g., "500 mg", "50 mcg", "5 ml")
            dosage = next((f for f in fields if re.search(r'\d+\s*(mg|mcg|ml|units|tablet|capsule)', f)), None)

            # Extract route from instruction, fallback to searching fields
            route_match = re.search(r'by ([a-z ]+)', instructions) if instructions else None
            route = route_match.group(1).strip() if route_match else None

            # Extract frequency (e.g., "daily", "every 9 hours", "once a week")
            frequency_match = re.search(r'(daily|weekly|monthly|every \d+ (hours|days)|once a (day|week))', instructions) if instructions else None
            frequency = frequency_match.group(0) if frequency_match else None

            info = self._match_medication_classification_and_supercategory(raw_name)

            if raw_name:
                # self.medications[raw_name] = {
                #     "classification": info.get("classification"),
                #     "supercategory": info.get("supercategory"),
                #     "instructions": instructions,
                #     "dosage": dosage,
                #     "route": route,
                #     "frequency": frequency,
                #     "compliance": None  # Will be filled later
                # }
                med_obj = {
                    "name": raw_name,
                    "classification": info.get("classification"),
                    "supercategory": info.get("supercategory"),
                    "instructions": instructions,
                    "dosage": dosage,
                    "route": route,
                    "frequency": frequency,
                    "compliance": None  # Will be filled later
                }

                self.medications[raw_name] = med_obj

                supercat = info.get("supercategory") or "other"
                if supercat not in self.grouped_meds:
                    self.grouped_meds[supercat] = []  # fallback for unknown supercats

                self.grouped_meds[supercat].append(med_obj)



    def _parse_adherence(self):
        soup = BeautifulSoup(self.adherence_html, "html.parser")
        lines = soup.get_text(separator="\n").strip().split("\n")

        for line in lines:
            if "-" in line:
                med, compliance = map(str.strip, line.split("-", 1))
                med = med.lower()
                compliance = compliance.lower()

                if med == '[medication]':
                    continue

                matched_key = None
                for key in self.medications.keys():
                    if med in key:
                        matched_key = key
                        break

                if matched_key:
                    self.medications[matched_key]["compliance"] = compliance
                else:
                    info = self.medication_lookup.get(med)
                    self.medications[med] = {
                        "classification": info["classification"] if info else None,
                        "supercategory": info["supercategory"] if info else None,
                        "instructions": None,
                        "compliance": compliance
                    }

    def get_medications(self) -> Dict[str, Dict[str, Optional[str]]]:
        return self.medications

    def get_grouped_medications(self) -> Dict[str, list]:
        return self.grouped_meds



if __name__ == "__main__":
    # healthie_user_id = "1525423" # Patient AWS Test
    # healthie_user_id = "2062877" # Patient AWS Test 6 (no data)
    healthie_user_id = "2315391" # Bob Barker

    look_up_codes_management = LookUpCodesManagement()
    entry = look_up_codes_management.retrieve_entry_by_healthie_user_id(healthie_user_id)
    internal_key = entry['syntrillo_internal_key']

    medications = MedicationParser(syntrillo_internal_key=internal_key)
    print(f"Medications: {medications}")
