import re
from typing import Optional, Dict
from bs4 import BeautifulSoup

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

        # If no med match, try matching classification/supercategory directly
        all_classifications = {info["classification"] for info in self.medication_lookup.values()}
        all_supercategories = {info["supercategory"] for info in self.medication_lookup.values()}

        for classification in all_classifications:
            if classification and classification in cleaned:
                return {"classification": classification, "supercategory": None}

        for supercategory in all_supercategories:
            if supercategory and supercategory in cleaned:
                return {"classification": None, "supercategory": supercategory}

        return {"classification": None, "supercategory": None}

    def _parse_prescriptions(self):
        blocks = self.prescription_str.split('\\\\')

        for block in blocks:
            parts = block.split('\r|\r|')

            if len(parts) >= 2:
                raw_name = parts[0].strip().lower()
                instructions = parts[1].split('\r|')[1].strip().lower() if len(parts[1].split('\r|')) > 1 else None
                info = self._match_medication_classification_and_supercategory(raw_name)

                if raw_name:
                    self.medications[raw_name] = {
                        "classification": info["classification"],
                        "supercategory": info["supercategory"],
                        "instructions": instructions,
                        "compliance": None
                    }

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
