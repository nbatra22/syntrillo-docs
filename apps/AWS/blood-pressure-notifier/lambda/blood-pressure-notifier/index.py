import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    # trigger event is either
    # - sent on a schedule, for example daily at 10:00 AM    
    # - sent in real-time using Tenovi webhooks (we are investigating this)
    logger.info(f"Received event: {event}")

    # Steps when triggered by schedule
    # 1. Get list of all patients with blood pressure device
    from tenovi_measurements import get_patients, get_measurements
    patients: list[str] = get_patients()

    # 2. Get list of all measurements for each of these patients from 12:00 AM to 11:59 PM for that day
    measurements: list[dict] = get_measurements(patients)
    n_measurements = len(measurements)

    # 3. Push these measurements to MySQL database
    from mysql_db import push_measurements
    push_measurements(measurements)
    
    # 4. Send notifications to clinicians when high blood pressure is detected
    n_alerts = 0
    for measurement in measurements:
        if measurement.is_dangerous():
            # Generate alert for this measurement, including message and destination sink config
            # for example, send to Slack, email, etc.
            alert = measurement.to_alert()
            # Send alert
            alert.send()
            n_alerts += 1
    

    # Steps when triggered by Tenovi webhooks
    # 1. Extract patient_id and measurement data from event
    # 2. Push these measurements to MySQL database
    # 3. Send notifications to clinicians when high blood pressure is detected

    return {
        'statusCode': 200,
        'body': f'{n_measurements} measurements pushed to MySQL database, {n_alerts} alerts sent to clinicians'
    }
