# Path: ./sources/syntrillo/api_healthie/feature_toggle.py

from syntrillo_lib.api_healthie.auth import HealthieAuth
import datetime
import random

class HealthieFeatureToggle():
    """
    A utility class for specific Healthie API interactions.


    """
    def __init__(self):
        """
        Initializes the HealthieFeatureToggle instance.

        https://docs.gethealthie.com/schema/featuretoggle.doc

        https://securestaging.gethealthie.com/settings/journal_entries

        https://docs.gethealthie.com/schema/custommetric.doc

        'These settings apply to all clients assigned to you (i.e., they are “global settings”). You can change settings on this page at any time.
        Settings for a client group override global settings. To change settings for a group, select "Edit Settings" in "Actions" in the groups list.
        Settings for a client override group and global settings. To change settings for a client, go to their profile and select "Settings" in "Actions.'

        'Feature toggles are inherited from the organization owner when a new user is created. So going forward, assuming the settings are how you like, the feature toggle will be essentially duplicated. However, if you have feature toggles that are not in sync, you'll need to update those accordingly.'

        => decision not to use this. Instead the owner of the organization will have to set the feature toggles with the GUI, including the custom metrics.


        """
        self.auth = HealthieAuth()

    def create_feature_toggle(
        self,
        user_id : str,
    ):
        """

        """
        mutation = '''
            mutation createFeatureToggle (
                $name: String,
                $show: Boolean,
                $show_client: Boolean,
                $user_id: ID
            ) {
                createFeatureToggle (input:{
                    user_id: $user_id,
                    custom_metrics: [{
                            name : $name,
                            show : $show,
                            show_client : $show_client,
                    }]
                })
                {
                    feature_toggle {
                      id
                    }
                    messages
                    {
                        field
                        message
                    }
                }
            }
        '''

        # Set up the variables for the GraphQL mutation
        variables = {
            'name' : "test Larry metrics",
            'show': True,
            'show_client': True,
            'user_id': user_id
        }

        # Make the GraphQL mutation request using the send_query method inherited from HealthieAPI
        response, log = self.auth.send_query(mutation, variables)

        return response, log

    def update_feature_toggle(
        self,
        feature_toggle_id: str,
        toggle_dict: dict = None,
    ):
        """
        Update a feature toggle

        https://docs.gethealthie.com/schema/updatefeaturetoggleinput.doc
        """
        mutation = '''
            mutation UpdateFeatureToggle(
                $id: ID!,
                $allow_apple_health_sync: Boolean,
                $allow_clearstep_sync: Boolean,
                $allow_community_chat: Boolean,
                $allow_direct_chat: Boolean,
                $allow_fitbit_sync: Boolean,
                $allow_google_fit_sync: Boolean,
                $allow_shapa_sync: Boolean,
                $allow_withings_sync: Boolean,
                $apply_eating_disorder_default: Boolean,
                $can_schedule_appointments: Boolean,
                $can_track_poop: Boolean,
                $can_track_symptoms: Boolean,
                $can_track_water_intake: Boolean,
                $can_view_care_plan: Boolean,
                $can_view_documents: Boolean,
                $can_view_forms: Boolean,
                $can_view_goals: Boolean,
                $can_view_journal_entries: Boolean,
                $can_view_packages: Boolean,
                $can_view_payments: Boolean,
                $can_view_programs: Boolean,
                $custom_metric_overrides: [CustomMetricOverridesInput],
                $custom_metrics: [CustomMetricInput],
                $date_range_preference: String,
                $default_water_intake: String,
                $do_not_auto_submit_cms1500: Boolean,
                $email_notification_frequency: String,
                $last_journal_from_date: String,
                $last_journal_to_date: String,
                $push_notification_frequency: String,
                $send_unpaid_invoice_reminder: Boolean,
                $seperate_provider_metric_from_client: Boolean,
                $show_a1c_metric: Boolean,
                $show_bf_percent_metric: Boolean,
                $show_blood_pressure_metric: Boolean,
                $show_blood_sugar_metric: Boolean,
                $show_bmi_graph: Boolean,
                $show_bmi_growth_chart: Boolean,
                $show_bmr_metric: Boolean,
                $show_body_temperature_metric: Boolean,
                $show_client_a1c_metric: Boolean,
                $show_client_bf_percent_metric: Boolean,
                $show_client_blood_pressure_metric: Boolean,
                $show_client_blood_sugar_metric: Boolean,
                $show_client_bmi_graph: Boolean,
                $show_client_bmi_growth_chart: Boolean,
                $show_client_bmr_metric: Boolean,
                $show_client_body_temperature_metric: Boolean,
                $show_client_harris_benedict: Boolean,
                $show_client_height_growth_chart: Boolean,
                $show_client_ox_sat_metric: Boolean,
                $show_client_waist_circumference_metric: Boolean,
                $show_client_weight_growth_chart: Boolean,
                $show_client_weight_metric: Boolean,
                $show_ed_posthunger: Boolean,
                $show_ed_prehunger: Boolean,
                $show_food: Boolean,
                $show_food_category: Boolean,
                $show_food_emotion: Boolean,
                $show_food_reflection: Boolean,
                $show_harris_benedict: Boolean,
                $show_healthiness: Boolean,
                $show_height_graph: Boolean,
                $show_height_growth_chart: Boolean,
                $show_metric: Boolean,
                $show_mirror: Boolean,
                $show_normal_hunger: Boolean,
                $show_note: Boolean,
                $show_note_emotion: Boolean,
                $show_nutrients_tracking: Boolean,
                $show_ox_sat_metric: Boolean,
                $show_waist_circumference_metric: Boolean,
                $show_weight_growth_chart: Boolean,
                $show_weight_metric: Boolean,
                $show_workout: Boolean,
                $use_metric_system: Boolean,
                $user_id: ID,
                $view_not_track: Boolean
            ) {
                updateFeatureToggle(
                    id: $id,
                    allow_apple_health_sync: $allow_apple_health_sync,
                    allow_clearstep_sync: $allow_clearstep_sync,
                    allow_community_chat: $allow_community_chat,
                    allow_direct_chat: $allow_direct_chat,
                    allow_fitbit_sync: $allow_fitbit_sync,
                    allow_google_fit_sync: $allow_google_fit_sync,
                    allow_shapa_sync: $allow_shapa_sync,
                    allow_withings_sync: $allow_withings_sync,
                    apply_eating_disorder_default: $apply_eating_disorder_default,
                    can_schedule_appointments: $can_schedule_appointments,
                    can_track_poop: $can_track_poop,
                    can_track_symptoms: $can_track_symptoms,
                    can_track_water_intake: $can_track_water_intake,
                    can_view_care_plan: $can_view_care_plan,
                    can_view_documents: $can_view_documents,
                    can_view_forms: $can_view_forms,
                    can_view_goals: $can_view_goals,
                    can_view_journal_entries: $can_view_journal_entries,
                    can_view_packages: $can_view_packages,
                    can_view_payments: $can_view_payments,
                    can_view_programs: $can_view_programs,
                    custom_metric_overrides: $custom_metric_overrides,
                    custom_metrics: $custom_metrics,
                    date_range_preference: $date_range_preference,
                    default_water_intake: $default_water_intake,
                    do_not_auto_submit_cms1500: $do_not_auto_submit_cms1500,
                    email_notification_frequency: $email_notification_frequency,
                    last_journal_from_date: $last_journal_from_date,
                    last_journal_to_date: $last_journal_to_date,
                    push_notification_frequency: $push_notification_frequency,
                    send_unpaid_invoice_reminder: $send_unpaid_invoice_reminder,
                    seperate_provider_metric_from_client: $seperate_provider_metric_from_client,
                    show_a1c_metric: $show_a1c_metric,
                    show_bf_percent_metric: $show_bf_percent_metric,
                    show_blood_pressure_metric: $show_blood_pressure_metric,
                    show_blood_sugar_metric: $show_blood_sugar_metric,
                    show_bmi_graph: $show_bmi_graph,
                    show_bmi_growth_chart: $show_bmi_growth_chart,
                    show_bmr_metric: $show_bmr_metric,
                    show_body_temperature_metric: $show_body_temperature_metric,
                    show_client_a1c_metric: $show_client_a1c_metric,
                    show_client_bf_percent_metric: $show_client_bf_percent_metric,
                    show_client_blood_pressure_metric: $show_client_blood_pressure_metric,
                    show_client_blood_sugar_metric: $show_client_blood_sugar_metric,
                    show_client_bmi_graph: $show_client_bmi_graph,
                    show_client_bmi_growth_chart: $show_client_bmi_growth_chart,
                    show_client_bmr_metric: $show_client_bmr_metric,
                    show_client_body_temperature_metric: $show_client_body_temperature_metric,
                    show_client_harris_benedict: $show_client_harris_benedict,
                    show_client_height_growth_chart: $show_client_height_growth_chart,
                    show_client_ox_sat_metric: $show_client_ox_sat_metric,
                    show_client_waist_circumference_metric: $show_client_waist_circumference_metric,
                    show_client_weight_growth_chart: $show_client_weight_growth_chart,
                    show_client_weight_metric: $show_client_weight_metric,
                    show_ed_posthunger: $show_ed_posthunger,
                    show_ed_prehunger: $show_ed_prehunger,
                    show_food: $show_food,
                    show_food_category: $show_food_category,
                    show_food_emotion: $show_food_emotion,
                    show_food_reflection: $show_food_reflection,
                    show_harris_benedict: $show_harris_benedict,
                    show_healthiness: $show_healthiness,
                    show_height_graph: $show_height_graph,
                    show_height_growth_chart: $show_height_growth_chart,
                    show_metric: $show_metric,
                    show_mirror: $show_mirror,
                    show_normal_hunger: $show_normal_hunger,
                    show_note: $show_note,
                    show_note_emotion: $show_note_emotion,
                    show_nutrients_tracking: $show_nutrients_tracking,
                    show_ox_sat_metric: $show_ox_sat_metric,
                    show_waist_circumference_metric: $show_waist_circumference_metric,
                    show_weight_growth_chart: $show_weight_growth_chart,
                    show_weight_metric: $show_weight_metric,
                    show_workout: $show_workout,
                    use_metric_system: $use_metric_system,
                    view_not_track: $view_not_track
                ) {
                    feature_toggle {
                        id
                    }
                    messages {
                        field
                        message
                    }
                }
            }
        '''

        # Set up the variables for the GraphQL mutation
        variables = {
            'id': feature_toggle_id,
        }
        if toggle_dict:
            variables.update(toggle_dict)  # Merge toggle_dict into variables

        # Make the GraphQL mutation request using the send_query method inherited from HealthieAPI
        response, log = self.auth.send_query(mutation, variables)

        return response, log


    def get_feature_toggles(
        self,
        user_id : str = None,
        ):
        """
        Get all feature toggles
        """
        query = '''
            query FeatureToggle(
                    $id: ID,
                    $user_id: ID
                ) {
                featureToggle(
                    id: $id,
                    user_id: $user_id
                ) {
                    id
                    created_at
                    show_blood_pressure_metric
                    custom_metrics {
                        feature_toggle_id
                        high_warning_threshold
                        id
                        low_warning_threshold
                        name
                        should_show
                        should_show_client
                        show
                        show_client
                        track
                        user_id
                    },
                }
            }
        '''

        variables = {
            'user_id': user_id
        }

        # Make the GraphQL query request using the send_query method inherited from HealthieAPI
        response, log = self.auth.send_query(query, variables)

        return response, log

if __name__ == "__main__":
    feature_toggle = HealthieFeatureToggle()

    if False:
        response, log = feature_toggle.create_feature_toggle("1035117")
        HealthieAuth.print_pretty_json(response)
        HealthieAuth.print_pretty_json(log)

    if True:
        response, log = feature_toggle.get_feature_toggles("1035117")
        HealthieAuth.print_pretty_json(response)
        HealthieAuth.print_pretty_json(log)