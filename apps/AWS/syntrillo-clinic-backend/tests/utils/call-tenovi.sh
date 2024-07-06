API_KEY_NON_HWI="AiXWgI5O.q6jRFRbi1RMsNW5r7OwXEHKXII8r6SXn"
API_KEY_HWI="j8cByYRW.yYXwrxD1gXdryy41AIbz4QTsLcRDYfNt"

CLIENT_DOMAIN_NON_HWI=syntrillo
CLIENT_DOMAIN_HWI=syntrillo-hwi

API_KEY=$API_KEY_NON_HWI
CLIENT_DOMAIN=$CLIENT_DOMAIN_NON_HWI

curl -X GET \
     -H "Authorization: Api-Key $API_KEY" \
     -H "Content-Type: application/json" \
     "https://api2.tenovi.com/clients/$CLIENT_DOMAIN///hwi/hwi-devices/" \
     |jq '.[] | select(.id == "8f6b64e2-01f2-4528-a8c4-4ce1763d9193")'

curl -X GET \
     -H "Authorization: Api-Key $API_KEY" \
     -H "Content-Type: application/json" \
     "https://api2.tenovi.com/clients/$CLIENT_DOMAIN///hwi/hwi-devices/?pseudo_code_for_tenovi_phi_access=564c8031-da06-4f7e-9057-44c4b790547d"
