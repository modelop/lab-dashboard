from modelop_sdk.utils import dashboard_utils
import modelop_sdk.utils.logging as logger
import pandas as pd

LOG = logger.configure_logger()


# modelop.init
def calculate_roi(comparator, deployable_model, input_schema):
    """
    A function to set model-specific global variables used in ROI computations.
    """
    global label_field, baseline_field, action_field
    global cost_multipliers

    # with open("modelop_parameters.json", "r") as parameters_file:
    #     modelop_parameters = json.load(parameters_file)
    # ROI_parameters = modelop_parameters["monitoring"]["business_value"]["ROI"]
    # logger.info("ROI parameters: %s", ROI_parameters)

    # JOB = json.loads(init_param["rawJson"])
    # DEPLOYABLE_MODEL = JOB.get('referenceModel')
    # try:
    #     INPUT_SCHEMA = infer.extract_input_schema(init_param)
    # except Exception as e:
    #     LOG.error(f"Error while extracting input_schema - {str(e)}")
    #     INPUT_SCHEMA = None

    dashboard_utils.assert_df_not_none_and_not_empty(comparator, "Required comparator")

    ## Creating a copy because the current actual_roi implementation modifies the comparatator df
    comparator_copy = comparator.copy()

    if deployable_model is None or len(deployable_model) == 0:
        raise ValueError("deployed_model is None or empty")

    if input_schema is None or len(input_schema) == 0:
        raise ValueError("input_schema is None or empty")

    try:
        ROI_parameters = deployable_model["storedModel"]["modelMetaData"]["roi"]
        LOG.info("ROI paramaters: %s", ROI_parameters)
    except Exception as e:
        error_message = "required deployableModel.storedModel.modelMetadata.roi parameters not found, missing parameters."
        LOG.eror(error_message)
        raise KeyError(error_message)

    try:
        fields = get_fields(input_schema)
        LOG.info(f"Fields for regression ROI: %s", fields)
    except Exception as e:
        raise KeyError(
            f"Error while extracting fields from input_extended_schema: {str(e)}"
        )

    label_field = fields["label_field"]
    baseline_field = fields["baseline_field"]
    action_field = fields["action_field"]

    print("--------Field readout----------")
    print(label_field)
    print(baseline_field)
    print(action_field)
    print("--------Field readout----------")
    # ROI cost multipliers for cases that are determined in function
    cost_multipliers = {
        "TP": ROI_parameters["costMultipliersTP"],
        "FP": ROI_parameters["costMultipliersFP"],
        "TN": ROI_parameters["costMultipliersTN"],
        "FN": ROI_parameters["costMultipliersFN"]
    }

# # modelop.metrics
# def metrics(data) -> dict:
#     """
#     A Function to classify records & compute actual ROI given a labeled & scored DataFrame.

#     Args:
#         dataframe (pd.DataFrame): Slice of Production data

#     Yields:
#         dict: Test Result containing actual roi metrics
#     """

    # Classify each record in dataframe
    for idx in range(len(comparator_copy)):
        amount = comparator_copy.iloc[idx][label_field] - comparator_copy.iloc[idx][baseline_field]
        if comparator_copy.iloc[idx][action_field]:
            comparator_copy["record_class"] = (
                "TP" if amount > 0 else "TN"
            )
        else:
            comparator_copy["record_class"] = (
                "FN" if amount < 0 else "FN"
            )


    # Compute actual ROI
    actual_roi = compute_actual_roi(comparator_copy)
    LOG.info(f"compute_actual_roi: {actual_roi}")
    return actual_roi


def compute_actual_roi(data) -> float:
    """
    Helper function to compute actual ROI.

    Args:
        data (pd.DataFrame): Input DataFrame containing record_class

    Returns:
        float: actual ROI
    """

    actual_roi = 0
    for idx in range(len(data)):
        amount = data.iloc[idx][label_field] - data.iloc[idx][baseline_field]
        actual_roi += (
            amount * cost_multipliers[data.iloc[idx]["record_class"]]
        )

    return round(actual_roi, 2)


def get_fields(input_schema: dict = None) -> dict:
    """
     Method that extracts the names of the fields with 'role': 'label', 'actionTaken': true, 'baselineValue': true
     method throws exception if the number of `positiveClassLabel` fields != 1

        input:
            input_schema : dict - external input_schema
        output:
            dict: dictionary of field names 
        exceptions thrown:
            - If none fields were defined then it raises ValueException.
            - If more than one field were marked, then it raises ValueException.

    """
    if input_schema is None or not input_schema:
        raise ValueError("input_schema is None or empty")

    if input_schema.get("fields") is None:
        raise KeyError("fields field not found at the input extended_schema")

    fields_array = input_schema["fields"]

    if not isinstance(fields_array, list):
        raise ValueError(f"fields_array is not an instance of an array, instead {type(fields_array)}")

    fields_array = input_schema["fields"]
    label_field = any
    action_field = any
    baseline_field = any

    for field in fields_array:
        if field.get("role") is not None and field.get("role") == "label":
            if label_field is not any:
                raise ValueError(
                    f"Error: More than one fields marked as 'label_field' found, only one is allowed."
                )
            label_field = field.get("name")
        elif field.get("actionTaken") is not None and field.get("actionTaken") == True:
            if action_field is not any:
                raise ValueError(
                    f"Error: More than one fields marked as 'action_field' found, only one is allowed."
                )
            action_field = field.get("name")
        elif field.get("baselineValue") is not None and field.get("baselineValue") == True:
            if baseline_field is not any:
                raise ValueError(
                        f"Error: More than one fields marked as 'baseline_field' found, only one is allowed."
                    )
            baseline_field = field.get("name")

    return {
        "label_field": label_field, # Column containing ground_truth
        "baseline_field": baseline_field, # Column containing baseline predictions
        "action_field": action_field  # Column containing action field, ie. buy vs no buy
    }