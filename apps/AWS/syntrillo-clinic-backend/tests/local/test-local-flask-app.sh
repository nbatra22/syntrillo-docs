# cd ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/lambda-functions/servers/iframe-generator-function
# python3 handler.py

cd /home/olivier/SyntrilloClinic/apps/PythonAnywhere/website
ln -s ../../../sources/syntrillo/ syntrillo
export FLASK_APP=flask_app 
flask run