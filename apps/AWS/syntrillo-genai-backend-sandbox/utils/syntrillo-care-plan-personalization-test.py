
# HTTP
import json
import requests
response = requests.post('http://10.0.190.145/query', headers= {'Content-Type': 'application/json'} , data = json.dumps({
    "query": "Robert Johnson is a 64 yo M w/ a history of diabetes, obesity, hypertension, and hyperlipidemia who presents following recent admission for ischemic stroke involving the left internal capsule. Stroke mechanism is small vessel disease. LDL is 86. Hemoglobin A1c is 6.3. Patient is on ASA 81 mg daily and Atorvastatin 20 mg daily. Patient does not smoke but drinks two alcoholic drinks per day. Patient has moderate depression and severe fatigue. What American Heart Association recommendations apply to this patient? Please only include recommendations associated with level A and level B evidence.",
    "model": "claude-3-5-sonnet"}))
print(response.text)

## HTTPS
import json
import requests
response = requests.post('https://10.0.190.145/query', verify=False, headers= {'Content-Type': 'application/json'} , data = json.dumps({
    "query": "Robert Johnson is a 64 yo M w/ a history of diabetes, obesity, hypertension, and hyperlipidemia who presents following recent admission for ischemic stroke involving the left internal capsule. Stroke mechanism is small vessel disease. LDL is 86. Hemoglobin A1c is 6.3. Patient is on ASA 81 mg daily and Atorvastatin 20 mg daily. Patient does not smoke but drinks two alcoholic drinks per day. Patient has moderate depression and severe fatigue. What American Heart Association recommendations apply to this patient? Please only include recommendations associated with level A and level B evidence.",
    "model": "claude-3-5-sonnet"}))
print(response.text)
print('AAAAAAAAAAAAAAAAAA')