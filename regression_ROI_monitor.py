import json
import modelop.utils as utils

logger = utils.configure_logger()


# modelop.init
def begin() -> None:
    """
    A function to set model-specific global variables used in ROI computations.
    """
    
    with open("modelop_parameters.json", "r") as parameters_file:
        modelop_parameters = json.load(parameters_file)
    
    ROI_parameters = modelop_parameters["monitoring"]["business_value"]["ROI"]
    logger.info("ROI parameters: %s", ROI_parameters)

    global label_field, baseline_field, action_field
    global cost_multipliers

    label_field = ROI_parameters["label_field"] # Column containing ground_truth
    baseline_field = ROI_parameters["baseline_field"] # Column containing baseline predictions
    action_field = ROI_parameters["action_field"] # Column containing action field, ie. buy vs no buy

    # ROI cost multipliers for cases that are determined in function
    cost_multipliers = ROI_parameters["cost_multipliers"]

# modelop.metrics
def metrics(data) -> dict:
    """
    A Function to classify records & compute actual ROI given a labeled & scored DataFrame.

    Args:
        dataframe (pd.DataFrame): Slice of Production data

    Yields:
        dict: Test Result containing actual roi metrics
    """

    # Classify each record in dataframe
    for idx in range(len(data)):
        amount = data.iloc[idx][label_field] - data.iloc[idx][baseline_field]
        if data.iloc[idx][action_field]:
            data["record_class"] = (
                "TP" if amount > 0 else "TN"
            )
        else:
            data["record_class"] = (
                "FN" if amount < 0 else "FN"
            )

    # Compute actual ROI
    actual_roi = compute_actual_roi(data)

    yield {
        "actual_roi": actual_roi,
        "label_field": label_field,
        "baseline_field": baseline_field,
        "business_value": [
            {
                "test_name": "Regression ROI",
                "test_category": "business_value",
                "test_type": "regression_roi",
                "test_id": "business_value_regression_roi",
                "values": {
                    "actual_roi": actual_roi,
                    "cost_multipliers": cost_multipliers,
                },
            }
        ],
    }


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
