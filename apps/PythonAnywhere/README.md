# PythonAnywhere Flask app

## Run and debug Flask app locally with VSCode

Launching and debuging parameters are located in the `.vscode/launch.json` file.

On any `*.py` file, use the VSCode menus :
   - Run > Start Debugging (F5)
   - Run > Start Without Debugging  (Ctrl-F5)

See https://code.visualstudio.com/docs/python/tutorial-flask for more information

### Run in a terminal

```
cd ./apps/PythonAnywhere/website
flask --app ./flask_app.py run
```

## Main site

Developped for historical reasons, includes some documentation and power calculations features.

http://127.0.0.1:5000/

https://syntrillo.pythonanywhere.com/

## iFrames displayed at Healthie

Need to ask Healthie support to set-up or rename these endpoints.

- http://127.0.0.1:5000/iframe_healthie_client_sidebar
   - https://syntrillo.pythonanywhere.com/iframe_healthie_client_sidebar
   - Considered to display care plans

- http://127.0.0.1:5000/iframe_healthie_provider_sidebar
    - https://syntrillo.pythonanywhere.com/iframe_healthie_provider_sidebar
    - Considered to display study wide information
    - Used to build Intake Forms and Charting Notes from repository

- http://127.0.0.1:5000/iframe_healthie_provider_tab
    - https://syntrillo.pythonanywhere.com/iframe_healthie_provider_tab
    - Provides patient specific information to the clinicians
    - Allows to pair Heathie, Tenovi and Syntrillo accounts
    - Restricted system menu to display and manage low level information and problems


## Endpoints

Incoming endpoint from Healthie webhooks : `/healthie_endpoint_post', methods=['POST']`


## Installation on PythonAnywhere

```txt
   - making use of python 3.9 everywhere : set-up in System Image
   - need to 'pip3.9 install statsmodels markdown2' in the console.
      :Make sure to use the right python version !!!
      : see : https://help.pythonanywhere.com/pages/InstallingNewModules/
```

`/var/www/syntrillo_pythonanywhere_com_wsgi.py`

```python
# This file contains the WSGI configuration required to serve up your
# web application at http://<your-username>.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.
#
# The below has been auto-generated for your Flask project

import sys

# add your project directory to the sys.path : where flask_app.py is
# project_home = '/home/syntrillo/15K_SyntrilloPythonAnywhere/website'
project_home = '/home/syntrillo/Syntrillo_Clinic/apps/PythonAnywhere/website/'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# add the sources (similar to PYTHONPATH for VSCode)
company_packages_home = '/home/syntrillo/Syntrillo_Clinic/sources/'
if company_packages_home not in sys.path:
    sys.path = [company_packages_home] + sys.path

# import flask app but need to call it "application" for WSGI to work
from flask_app import app as application  # noqa
```

## Additional packages installed manually

```bash
pip install aws-lambda-powertools aws-xray-sdk
```


