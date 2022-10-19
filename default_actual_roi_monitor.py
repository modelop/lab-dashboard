import modelop.schema.infer as infer
import json
import modelop_sdk.utils.logging as logger
from modelop_sdk.utils import dashboard_utils as dashboard_utils

LOG = logger.configure_logger()


def calculate_roi(comparator, job_json) -> float:
    """
    Source: https://github.com/merhi-odg/actual_ROI_monitor ( This monitor has local improvements )
    Monitor required inputs:
        1 - Comparator type: dataframe
        2 - job_json type: dict

    Note: The original implementation of this monitor is modifying the input comparator dataframe, so instead this
    implementation is generating a copy of the comparator dataframe to avoid issues with other monitors during the
    rest of the Dashboard execution.
    """
    dashboard_utils.assert_df_not_none_and_not_empty(comparator, "Required comparator")

    ## Creating a copy because the current actual_roi implementation modifies the comparatator df
    comparator_copy = comparator.copy()

    try:
        job = json.loads(job_json["rawJson"])
        deployable_model = job.get("referenceModel", None)
    except Exception as ex:
        error_message = "referenceModel parameter not found on job_json"
        LOG.error(error_message)
        raise KeyError(error_message)

    if deployable_model is None or len(deployable_model) == 0:
        raise ValueError("deployed_model is None or empty")

    try:
        input_schema = infer.extract_input_schema(job_json)
    except Exception as ex:
        LOG.error(f"Error while extracting input_schema - {str(ex)}")
        input_schema = None

    if input_schema is None or len(input_schema) == 0:
        raise ValueError("input_schema is None or empty")

    try:
        ROI_parameters = deployable_model["storedModel"]["modelMetaData"]["roi"]
        LOG.info("ROI parameters: %s", ROI_parameters)
    except Exception as er1:
        error_message = "Required deployableModel.storedModel.modelMetadata.roi parameters not found, missing parameters "
        LOG.error(error_message)
        raise KeyError(error_message)

    try:
        positive_class_label = get_positive_class_label(input_schema)
        LOG.info("Label of Positive Class: %s", positive_class_label)
    except Exception as er2:
        raise KeyError(
            f"Error while extracting positive_class_label from input_extended_schema : {str(er2)}"
        )

    global amount_field, label_field, score_field
    global cost_multipliers

    amount_field = get_credit_amount_field_name(input_schema)
    score_field = "score"  # Assuming these values will be present all the time
    label_field = "label_value"  # Assuming these values will be present all the time

    # ROI cost multipliers for each classification case
    cost_multipliers = {
        "TP": ROI_parameters["costMultipliersTP"],
        "FP": ROI_parameters["costMultipliersFP"],
        "TN": ROI_parameters["costMultipliersTN"],
        "FN": ROI_parameters["costMultipliersFN"],
    }

    LOG.info(f"Using cost_multipliers {str(cost_multipliers)}")
    # Classify each record in dataframe
    for idx in range(len(comparator_copy)):
        if (
            comparator_copy.iloc[idx][label_field]
            == comparator_copy.iloc[idx][score_field]
        ):
            comparator_copy["record_class"] = (
                "TP"
                if comparator_copy.iloc[idx][label_field] == positive_class_label
                else "TN"
            )
        elif (
            comparator_copy.iloc[idx][label_field]
            < comparator_copy.iloc[idx][score_field]
        ):
            comparator_copy["record_class"] = "FP"
        else:
            comparator_copy["record_class"] = "FN"

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
        actual_roi += (
            data.iloc[idx][amount_field]
            * cost_multipliers[data.iloc[idx]["record_class"]]
        )

    return round(actual_roi, 2)


def get_credit_amount_field_name(input_schema: dict = None) -> str:
    """
    Method that extracts the credit_amount field name marked with `isAmountField`:true from the input_schema.

        input:
            input_schema : dict - external input_schema
        output:
            str: `name` value of field marked as `isAmountField`
        exceptions thrown:
            - If none fields were defined with `isAmountField`:true, then it raises ValueException.
            - If more than one field were marked with `isAmountField`: true, then it raises ValueException.

    """
    if input_schema is None or not input_schema:
        raise ValueError("input_schema is None or empty")

    if input_schema.get("fields") is None:
        raise KeyError("fields field not found at the input extended_schema")

    fields_array = input_schema["fields"]

    if not isinstance(fields_array, list):
        raise ValueError(
            f"fields_array is not an instance of array , instead {type(fields_array)}"
        )

    amount_field_value = None

    for field in fields_array:
        if field.get("isAmountField") is not None:
            # Making sure isAmountField true
            if isinstance(field.get("isAmountField"), bool) and field.get(
                "isAmountField"
            ):
                if amount_field_value is not None:
                    raise ValueError(
                        f"Error: More than one fields marked as `isAmountField` found, existing one {amount_field_value}"
                    )
                amount_field_value = field.get("name")

    if amount_field_value is None:
        raise ValueError("None fields found as `isAmountField`:true ")

    return amount_field_value


def get_positive_class_label(input_schema: dict = None) -> any:
    """
    Method that extracts the value for `positiveClassLabel` for fields with 'role':'label',
    method throws exception if the number of `positiveClassLabel` fields != 1

       input:
           input_schema : dict - external input_schema
       output:
           any: `value` value for field marked as `positiveClassLabel`
       exceptions thrown:
           - If none fields were defined with `positiveClassLabel` then it raises ValueException.
           - If more than one field were marked with `positiveClassLabel`, then it raises ValueException.

    """
    if input_schema is None or not input_schema:
        raise ValueError("input_schema is None or empty")

    if input_schema.get("fields") is None:
        raise KeyError("fields field not found at the input extended_schema")

    fields_array = input_schema["fields"]

    if not isinstance(fields_array, list):
        raise ValueError(
            f"fields_array is not an instance of array , instead {type(fields_array)}"
        )

    positive_class_label = any

    for field in fields_array:
        if field.get("role") is not None and field.get("role") == "label":

            if field.get("positiveClassLabel") is not None:
                if positive_class_label is not any:
                    raise ValueError(
                        f"Error: More than one fields marked as `positiveClassLabel` found, only one is allowed"
                    )
                positive_class_label = field.get("positiveClassLabel")

    if positive_class_label is any:
        raise ValueError("None fields found marked as `positiveClassLabel` ")

    return positive_class_label
