import re
from typing import Dict, Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TestsOrdersResponse:
    def __init__(self, cta_performed: Optional[str] = None, cardiac_monitoring_30day: Optional[str] = None, ha1c_6mo: Optional[str] = None):
        self.cta_performed = cta_performed
        self.cardiac_monitoring_30day = cardiac_monitoring_30day
        self.ha1c_6mo = ha1c_6mo

        self.tests_orders = {
            'cta_performed': None, # boolean
            'cardiac_monitoring_30day': None,
            'ha1c_6mo': None
        }

    def get_tests_orders(self):
        if self.cta_performed:
            self._parse_cta_performed()

        if self.cardiac_monitoring_30day:
            self._parse_cardiac_monitoring_30day()

        if self.ha1c_6mo:
            self._parse_ha1c_6mo()

        return self.tests_orders

    def _parse_cta_performed(self):
        blocks = self.cta_performed.split('|')

        for block in blocks:
            if 'cta' in block.lower():
                self.tests_orders['cta_performed'] = True
                break  # optional: stops after first match
            else:
                self.tests_orders['cta_performed'] = False


    def _parse_cardiac_monitoring_30day(self):

        if self.cardiac_monitoring_30day == 'Yes':
            self.tests_orders['cardiac_monitoring_30day'] = True
        elif self.cardiac_monitoring_30day == 'No':
            self.tests_orders['cardiac_monitoring_30day'] = False

    def _parse_ha1c_6mo(self):
        if self.ha1c_6mo is None:
            return

        ha1c_date = datetime.strptime(self.ha1c_6mo, "%Y-%m-%d")
        six_months_ago = datetime.today() - relativedelta(months=6)

        if ha1c_date < six_months_ago:
            self.tests_orders['ha1c_6mo'] = True
        else:
            self.tests_orders['ha1c_6mo'] = False
