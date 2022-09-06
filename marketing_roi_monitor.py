import random

import modelop_sdk.utils.logging as logger
from modelop_sdk.utils import dashboard_utils as dashboard_utils

LOG = logger.configure_logger()


def calculate_mkt_roi(comparator, deployable_model, input_schema) -> float:
    """
    Method that simulates a ROI custom calculation for models with MODEL_USE_CATEGORY == 'MARKETING'.
    This monitor should first validate that all required inputs exists are not None and not empty.
    If no issues with the input were found, monitor should proceed with ROI calculation.

    For this Dummy model, the ROI calculation is going to be performed by calculating a random float value between
    500 K and 1 MM.
    """

    # Step 1 - validating input comparator Dataframe is not None nor empty
    dashboard_utils.assert_df_not_none_and_not_empty(comparator, "Required comparator")

    # Step 2 -validating input deployable_model is not None or empty
    if deployable_model is None or len(deployable_model) == 0:
        raise ValueError("deployed_model is None or empty")

    # Step 2 -validating input input_schema is not None or empty
    if input_schema is None or len(input_schema) == 0:
        raise ValueError("input_schema is None or empty")

    # Step 3 - Monitor performs dummy calculation, by default rounds result to max. 2 decimals
    return round(random.uniform(500000, 1000000), 2)
