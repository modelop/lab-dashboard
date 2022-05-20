import modelop_sdk.utils.logging as logger
from modelop.ootb_monitors.volumetrics_count import volumetrics_count
from modelop_sdk.utils import dashboard_utils as dashboard_utils


def calculate_daily_inferences(comparator) -> dict:
    """
    MOCVolumetricsCountMonitor that performs Volumetrics counts
    Source: https://github.com/modelop/moc_monitors/tree/main/src/modelop/ootb_monitors/volumetrics_count
    """
    LOG = logger.configure_logger()

    dashboard_utils.assert_df_not_none_and_not_empty(comparator, "Required comparator")

    # Initialize Volumetric monitor with 1st input DataFrame
    volumetric_monitor = volumetrics_count.metrics(comparator)

    for result in volumetric_monitor:
        return result["record_count"]
