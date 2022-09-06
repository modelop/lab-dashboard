import unittest

import default_actual_roi_monitor as default_actual_roi_monitor


class MyTestCase(unittest.TestCase):
    valid_input_ext_sc = {
        "name": "input_schema.avsc",
        "type": "record",
        "fields": [
            {
                "name": "id",
                "type": "int",
                "dataClass": "numerical",
                "role": "identifier",
                "protectedClass": False,
                "driftCandidate": False,
                "specialValues": [],
                "scoringOptional": False,
            },
            {
                "name": "credit_amount",
                "type": "float",
                "dataClass": "numerical",
                "role": "predictor",
                "protectedClass": False,
                "driftCandidate": True,
                "specialValues": [],
                "scoringOptional": False,
                "isAmountField": True,
            },
            {
                "name": "installment_rate",
                "type": "int",
                "dataClass": "numerical",
                "role": "predictor",
                "protectedClass": False,
                "driftCandidate": True,
                "specialValues": [],
                "scoringOptional": False,
            },
        ],
    }

    valid_input_ext_sc_multiple_isValueField_one_True = {
        "name": "input_schema.avsc",
        "type": "record",
        "fields": [
            {
                "name": "id",
                "type": "int",
                "dataClass": "numerical",
                "role": "identifier",
                "isAmountField": False,
                "protectedClass": False,
                "driftCandidate": False,
                "specialValues": [],
                "scoringOptional": False,
            },
            {
                "name": "credit_amount",
                "type": "float",
                "dataClass": "numerical",
                "role": "predictor",
                "protectedClass": False,
                "driftCandidate": True,
                "specialValues": [],
                "scoringOptional": False,
                "isAmountField": True,
            },
            {
                "isAmountField": False,
                "name": "installment_rate",
                "type": "int",
                "dataClass": "numerical",
                "role": "predictor",
                "protectedClass": False,
                "driftCandidate": True,
                "specialValues": [],
                "scoringOptional": False,
            },
        ],
    }

    invalid_input_ext_sc_multiple_isValueField_multiple_True = {
        "name": "input_schema.avsc",
        "type": "record",
        "fields": [
            {
                "name": "id",
                "type": "int",
                "dataClass": "numerical",
                "role": "identifier",
                "protectedClass": False,
                "driftCandidate": False,
                "specialValues": [],
                "scoringOptional": False,
                "isAmountField": True,
            },
            {
                "name": "credit_amount",
                "type": "float",
                "dataClass": "numerical",
                "role": "predictor",
                "protectedClass": False,
                "driftCandidate": True,
                "specialValues": [],
                "scoringOptional": False,
                "isAmountField": True,
            },
            {
                "isAmountField": False,
                "name": "installment_rate",
                "type": "int",
                "dataClass": "numerical",
                "role": "predictor",
                "protectedClass": False,
                "driftCandidate": True,
                "specialValues": [],
                "scoringOptional": False,
            },
        ],
    }

    invalid_input_ext_sc_no_isValueField = {
        "name": "input_schema.avsc",
        "type": "record",
        "fields": [
            {
                "name": "id",
                "type": "int",
                "dataClass": "numerical",
                "role": "identifier",
                "protectedClass": False,
                "driftCandidate": False,
                "specialValues": [],
                "scoringOptional": False,
            },
            {
                "name": "credit_amount",
                "type": "float",
                "dataClass": "numerical",
                "role": "predictor",
                "protectedClass": False,
                "driftCandidate": True,
                "specialValues": [],
                "scoringOptional": False,
            },
            {
                "name": "installment_rate",
                "type": "int",
                "dataClass": "numerical",
                "role": "predictor",
                "protectedClass": False,
                "driftCandidate": True,
                "specialValues": [],
                "scoringOptional": False,
            },
        ],
    }

    def test_get_credit_amount_field_happy_path_1_found(self):
        valid_credit_amount_one_field = (
            default_actual_roi_monitor.get_credit_amount_field_name(
                self.valid_input_ext_sc
            )
        )
        self.assertEqual(
            "credit_amount", valid_credit_amount_one_field
        )  # add assertion here

    def test_get_credit_amount_field_name_multiple_isAmountField_multiple_true(self):
        try:
            valid_credit_amount_one_field = (
                default_actual_roi_monitor.get_credit_amount_field_name(
                    self.invalid_input_ext_sc_multiple_isValueField_multiple_True
                )
            )
            self.assertFalse(
                "Method should have failed , because more than one isAmountField:true were found"
            )
        except Exception as ex:
            self.assertTrue("Multiple isAmountField:true found, so this is correct")

    def test_get_credit_amount_field_name_multiple_isAmountField_one_true(self):
        try:
            valid_credit_amount_field = (
                default_actual_roi_monitor.get_credit_amount_field_name(
                    self.valid_input_ext_sc_multiple_isValueField_one_True
                )
            )
            self.assertEqual(
                "credit_amount", valid_credit_amount_field
            )  # add assertion here

        except Exception as ex:
            self.assertFalse(
                "Method should have failed , multiple isAmountField found but only one marked as true found"
            )

    def test_invalid_get_credit_amount_field_no_isAmountField_found(self):
        try:
            valid_credit_amount_one_field = (
                default_actual_roi_monitor.get_credit_amount_field_name(
                    self.invalid_input_ext_sc_no_isValueField
                )
            )
            self.assertFalse(
                "None isAmountField:true found, so this is incorrect, exception should have happened"
            )
        except Exception as ex:
            self.assertTrue(
                "None isAmountField:true found, so this is correct, exception expected"
            )


if __name__ == "__main__":
    unittest.main()
