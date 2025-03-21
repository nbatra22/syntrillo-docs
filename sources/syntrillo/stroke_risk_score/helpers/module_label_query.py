from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager


def get_question_variables(db_connection):
    try:
        with db_connection.cursor() as cursor:
            query = f"""
                SELECT
                    label
                FROM
                    module_label_look_up
            """

            cursor.execute(query)
            result = cursor.fetchall()

        print(f"***** MODULE LABELS *****: {result}")

        db_connection.close()

        return result[0][0]

    except Exception as e:
        print(f"Failed to fetch.")
        return None

if __name__ == "__main__":
    db_manager = SyntrilloDatabaseManager("99fddf03-9304-4e48-8711-0cc4d825eb94")
    db_connection = db_manager.conn
    get_question_variables(db_connection)


# (
#   ('weight', '2131157', '29020443', '1373914', '18516155'),
#   ('systolic_bp_initial', '2131053', '28021730', '1765843', '15159774'),
#   ('diastolic_bp_initial', '2131053', '28021731', '1765843', '15159775'),
#   ('resting_hr_initial', '2131053', '28021734', '1765843', '15159780'),
#   ('vigorous_exercise', '2174066', '29945718', '2155903', '18516167'),
#   ('moderate_exercise', '2174066', '29945729', '2155903', '18516168'),
#   ('stroke_type_bleeding_or_clotting', '2131157', '28594467', '1373914', '18516160'),
#   ('ldl', '2131053', '28021735', '1765843', '15159782'),
#   ('ha1c', '2131053', '28021743', '1765843', '15159786'),
#   ('cpap_prescribed', '2131055', '28559402', '2155936', '18519138'),
#   ('cpap_regular_usage', '2131055', '28559403', '2155936', '18519139'),
#   ('current_smoker', '2131055', '28559465', '2155936', '18519144'),
#   ('cigarettes_per_day_avg', '2131055', '28559511', '2155936', '18519145'),
#   ('stroke_cause_vessel_dissection', '2181298', '28665257', '2156089', '18519164'),
#   ('stroke_cause_procedure_complication', '2181298', '28665258', '2156089', '18519165'),
#   ('cardiac_monitoring_30day', '2131055', '28020687', '2155936', '18518423'),
#   ('trouble_concentrating', '2134701', '28077467', '1743130', '14968032'),
#   ('trouble_remembering_things', '2134701', '28077468', '1743130', '14968034'),
#   ('memory_requires_notes', '2134701', '29317791', '1743130', '14968036'),
#   ('fatigue_bothered', '2131186', '28022050', '1743132', '14968078'),
#   ('fatigue_quick_tiredness', '2131186', '28022051', '1743132', '14968079'),
#   ('fatigue_daily_inactivity', '2131186', '28022052', '1743132', '14968080'),
#   ('fatigue_sufficient_energy', '2131186', '28022053', '1743132', '14968081'),
#   ('fatigue_physical_exhaustion', '2131186', '28022054', '1743132', '14968082'),
#   ('fatigue_task_initiation', '2131186', '28022057', '1743132', '14968083'),
#   ('fatigue_clear_thinking', '2131186', '28022056', '1743132', '14968084'),
#   ('fatigue_motivation_lack', '2131186', '28022055', '1743132', '14968085'),
#   ('fatigue_mental_exhaustion', '2131186', '28022066', '1743132', '14968086'),
#   ('fatigue_concentration_ability', '2131186', '28022065', '1743132', '14968087'),
#   ('phq9_lack_of_interest', '2131187', '28022085', '1765846', '15159808'),
#   ('phq9_depressed_mood', '2131187', '28022086', '1765846', '15159809'),
#   ('phq9_sleep_disturbance', '2131187', '28022087', '1765846', '15159810'),
#   ('phq9_fatigue', '2131187', '28022088', '1765846', '15159811'),
#   ('phq9_appetite_changes', '2131187', '28022093', '1765846', '15159812'),
#   ('phq9_negative_self_perception', '2131187', '28022092', '1765846', '15159813'),
#   ('phq9_concentration_difficulty', '2131187', '28022091', '1765846', '15159814'),
#   ('phq9_psychomotor_changes', '2131187', '28022090', '1765846', '15159815'),
#   ('phq9_suicidal_thoughts', '2131187', '28022089', '1765846', '15159816'),
#   ('height_combined', '2131157', '29020445', '1373914', '18516154'),
#   ('medical_history_afib_carotid', '2131055', '28559387', '2155936', '18518428'),
#   ('meds_statin_plavix_aspirin_anticoagulants', '2131055', '28551137', '2155936', '18520987'),
#   ('medication_adherence_combined', '2131055', '28560828', '2155936', '18516245')
# )
