import unittest


class MainDashboardTests(unittest.TestCase):
    def test_placeholder(self):
        assert True

    # def test_main_test(self):
    #     baseline_scored = pd.read_json('./sampleData/df_baseline_scored.json', lines=True)
    #     comparator_scored = pd.read_json('./sampleData/df_sample_scored.json', lines=True)
    #
    #     # Updated job, because input schema was all in UPPER CAPS
    #     # jobAsString = open('./sampleData/jsonJobWithInputSchema_germanCredit_updated.json', 'r').read()
    #     # jobAsString = open('./sampleData/jsonJobWithInputSchema_germanCredit_additional_ext_sc_fields.json', 'r').read()
    #     jobAsString = open('./sampleData/jsonJobWithInputSchema_germanCredit_additional_ext_sc_fields_no_def.json', 'r').read()
    #     # jobAsString = open('./sampleData/jsonJobWithInputSchema_germanCredit_updated_bad_input_schema.json', 'r').read()
    #     # jobAsString = open('sampleData/jsonJobGermanCredit_withInputSchema_error.json', 'r').read()
    #     json_job_dict = {"rawJson": jobAsString}
    #
    #     main_dashboard_model.init(json_job_dict)
    #     metrics_result = main_dashboard_model.metrics(baseline_scored, comparator_scored)
    #     # metrics_result = metrics(baseline=None, comparator=None)
    #     for result in metrics_result:
    #         try:
    #             jsonObj = json.loads(
    #                 str(result).replace("'", "\"").replace("False", "false").replace("True", "true").replace("None",
    #                                                                                                          "null"))
    #             print(json.dumps(jsonObj, indent=2))
    #         except Exception as ex:
    #             print(str(ex))
    #             print(str(result).replace("'", "\""))

    #
    # def test_main_additiona_extended_schema_fields_test(self):
    #     baseline_scored = pd.read_json('./sampleData/df_baseline_scored.json', lines=True)
    #     comparator_scored = pd.read_json('./sampleData/df_sample_scored.json', lines=True)
    #
    #     # Updated job, because input schema was all in UPPER CAPS
    #     jobAsString = open('./sampleData/jsonJobWithInputSchema_germanCredit_additional_ext_sc_fields.json', 'r').read()
    #     # jobAsString = open('./sampleData/jsonJobWithInputSchema_germanCredit_updated_bad_input_schema.json', 'r').read()
    #     # jobAsString = open('sampleData/jsonJobGermanCredit_withInputSchema_error.json', 'r').read()
    #     json_job_dict = {"rawJson": jobAsString}
    #
    #     main_dashboard_model.init(json_job_dict)
    #     metrics_result = main_dashboard_model.metrics(baseline_scored, comparator_scored)
    #     # metrics_result = metrics(baseline=None, comparator=None)
    #     for result in metrics_result:
    #         try:
    #             jsonObj = json.loads(str(result).replace("'", "\"").replace("False", "false").replace("True", "true"))
    #             print(json.dumps(jsonObj, indent=2))
    #         except Exception as ex:
    #             print(str(ex))
    #             print(str(result).replace("'", "\""))

    #
    # def test_no_input_schema(self):
    #     baseline_scored = pd.read_json('./sampleData/df_baseline_scored.json', lines=True)
    #     comparator_scored = pd.read_json('./sampleData/df_sample_scored.json', lines=True)
    #
    #     # Updated job, because input schema was all in UPPER CAPS
    #     jobAsString = open('./sampleData/jsonJobGermanCredit_without_input_schema_error.json', 'r').read()
    #     # jobAsString = open('./sampleData/jsonJobWithInputSchema_germanCredit_updated_bad_input_schema.json', 'r').read()
    #     # jobAsString = open('sampleData/jsonJobGermanCredit_withInputSchema_error.json', 'r').read()
    #     json_job_dict = {"rawJson": jobAsString}
    #
    #     main_dashboard_model.init(json_job_dict)
    #     metrics_result = main_dashboard_model.metrics(baseline_scored, comparator_scored)
    #     # metrics_result = metrics(baseline=None, comparator=None)
    #     for result in metrics_result:
    #         try:
    #             jsonObj = json.loads(str(result).replace("'", "\"").replace("False", "false").replace("True", "true"))
    #             print(json.dumps(jsonObj, indent=2))
    #         except Exception as ex:
    #             print(str(ex))
    #             print(str(result).replace("'", "\""))


# if __name__ == "__main__":
#     input_schema_example = {
#         "name": "input_schema.avsc",
#         "type": "record",
#         "fields": [
#             {
#                 "name": "id",
#                 "type": "int",
#                 "dataClass": "numerical",
#                 "role": "identifier",
#                 "protectedClass": False,
#                 "driftCandidate": False,
#                 "specialValues": [],
#                 "scoringOptional": False
#             },
#             {
#                 "name": "credit_amount",
#                 "type": "float",
#                 "dataClass": "numerical",
#                 "role": "predictor",
#                 "protectedClass": False,
#                 "driftCandidate": True,
#                 "specialValues": [],
#                 "scoringOptional": False,
#                 "isAmountField": True
#             },
#             {
#                 "name": "label_value",
#                 "type": "int",
#                 "dataClass": "categorical",
#                 "role": "label",
#                 "protectedClass": False,
#                 "driftCandidate": True,
#                 "specialValues": [],
#                 "scoringOptional": True,
#                 "positiveClassLabel": 1
#             },
#             {
#                 "name": "score",
#                 "type": "int",
#                 "dataClass": "categorical",
#                 "role": "label",
#                 "protectedClass": False,
#                 "driftCandidate": True,
#                 "specialValues": [],
#                 "scoringOptional": True
#             }
#         ]
#     }
#
#     input_schema_example_with_error = {
#         "name": "input_schema.avsc",
#         "type": "record",
#         "fields": {"foo": "bar"}
#     }
#     input_schema_example_without_field = {
#         "name": "input_schema.avsc",
#         "type": "record"
#     }
#     credit_amount = get_credit_amount_field_name(input_schema_example)
#     print(f"Credit_amount_found {credit_amount}")
#     # credit_amount = get_credit_amount_field_name(input_schema_example_without_field)
#
#     positive_class_field = get_positive_class_label(input_schema_example)
#     print(f" positive_class_field {positive_class_field}")


if __name__ == "__main__":
    unittest.main()
