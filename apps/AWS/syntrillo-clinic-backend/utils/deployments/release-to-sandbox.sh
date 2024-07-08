~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/tests/local/test-local-source-syntrillo.sh && \
~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/tests/local/test-local-flask-app.sh && \
./deploy-to-sandbox.sh && \
~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/tests/remote/test-remote-invokes-lambdas-and-apis.sh