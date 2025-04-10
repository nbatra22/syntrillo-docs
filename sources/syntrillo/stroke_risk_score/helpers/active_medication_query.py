from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager


def get_patient_medications(db_connection):
    try:
        with db_connection.cursor() as cursor:
            query = f"""
                SELECT
                    med_name
                FROM
                    patient_medications
            """

            cursor.execute(query)
            result = cursor.fetchall()

        print(f"***** PATIENT MEDICATINOS *****: {result}")

        db_connection.close()

        return result[0][0]

    except Exception as e:
        print(f"Failed to fetch.")
        return None

if __name__ == "__main__":
    db_manager = SyntrilloDatabaseManager("99fddf03-9304-4e48-8711-0cc4d825eb94")
    db_connection = db_manager.conn
    get_patient_medications(db_connection)


# ('Aspirin (oral - tablet)',),
# ('Atenolol (oral - tablet)',),
# ('amLODIPine Besylate Oral Tablet',),
# ('Aspirin 81 Oral Tablet Chewable',),
# ('Atorvastatin Calcium Oral Tablet',),
# ('Escitalopram Oxalate Oral Tablet',),
# ('Flonase Allergy Relief Nasal Suspension',),
# ('Loratadine Oral Capsule',),
# ('Losartan Potassium Oral Tablet',),
# ('Metoprolol Tartrate Oral Tablet',),
# ('PriLOSEC OTC Oral Tablet Delayed Release',),
# ('Tadalafil Oral Tablet',),
# ('Xanax Oral Tablet',),
# ('Allopurinol Oral Tablet',),
# ('amLODIPine-Valsartan-HCTZ Oral Tablet',),
# ('Carvedilol Oral Tablet',),
# ('Colchicine Oral Capsule',),
# ('Docusate Sodium Oral Capsule',),
# ('Eliquis Oral Tablet',),
# ('Eplerenone Oral Tablet',),
# ('Ezetimibe Oral Tablet',),
# ('Flecainide Acetate Oral Tablet',),
# ('Fluticasone Propionate Nasal Suspension',),
# ('glyBURIDE Micronized Oral Tablet',),
# ('hydrALAZINE HCl Oral Tablet',),
# ('Hydroxychloroquine Sulfate Oral Tablet',),
# ('metFORMIN HCl Oral Tablet',),
# ('Senna Laxative Oral Tablet',),
# ('Sodium Bicarbonate Oral Tablet',),
# ('Tresiba FlexTouch Subcutaneous Solution Pen-injector',),
# ('Atorvastatin (oral - tablet)',),
# ('Plavix (oral - tablet)',)
