import re
from typing import Optional, Dict
from bs4 import BeautifulSoup

class MedicationParser:
    def __init__(
        self,
        prescription_str: Optional[str] = None,
        adherence_html: Optional[str] = None,
        db_conn=None  # Pass your database connection here
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

    def _load_medication_classifications(self) -> Dict[str, str]:
        """
        Load medication names and their classification into a dict.
        Keys are lowercased medication names for matching.
        """
        query = "SELECT medication_name, classification FROM medication_classifications;"
        cursor = self.db_conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()

        return {med.lower(): classification for med, classification in rows}


    def _clean_name(self, name: str) -> str:
        keywords_to_remove = ["oral", "tablet", "support", "miscellaneous"]
        cleaned = name.lower()
        for keyword in keywords_to_remove:
            cleaned = cleaned.replace(keyword, "")
        return cleaned.strip()


    def _match_medication_classification(self, raw_name: str) -> Optional[str]:
        cleaned = self._clean_name(raw_name)

        # Try to match substrings with known medications
        for med_name, classification in self.medication_lookup.items():
            if med_name in cleaned:
                return classification

        # If no med match, try matching against classification labels
        for classification in set(self.medication_lookup.values()):
            if classification in cleaned:
                return classification

        return None


    def _parse_prescriptions(self):
        blocks = self.prescription_str.split('\\\\')

        for block in blocks:
            parts = re.split(r'\r\|\r\|', block.strip())

            if len(parts) >= 4:
                raw_name = parts[0].strip().lower()
                instructions = parts[3].strip().lower()
                classification = self._match_medication_classification(raw_name)

                if raw_name:
                    self.medications[raw_name] = {
                        "classification": classification,
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
                    classification = self.medication_lookup.get(med)
                    self.medications[med] = {
                        "classification": classification,
                        "instructions": None,
                        "compliance": compliance
                    }

    def get_medications(self) -> Dict[str, Dict[str, Optional[str]]]:
        return self.medications
