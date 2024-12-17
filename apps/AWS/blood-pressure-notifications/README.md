# Blood pressure notification service

## The problem
We want to get early notifications when patients blood pressure levels are dangerous.

## The solution
Steps

1. Get blood pressure data in real time from Tenovi API, using AWS Lambda + AWS Gateway + Tenovi webhooks.

2. Compute thresholds, moving averages and trends.

3. If metric outside safe zone, send notification to care takers on Healthie.

4. Plot all the data in real-time in a Kibana dashboard, that we can link on our Healthie frontend app for clinicians.

## Next steps
- [ ] Simulate stream of measurment events using production data
- [ ] Compute alarms for historical data
- [ ] Build real-time visualizations in Kibana.


