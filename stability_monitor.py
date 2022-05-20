from modelop.ootb_monitors.stability_analysis import stability_analysis
import modelop_sdk.utils.logging as logger
from modelop_sdk.utils import dashboard_utils as dashboard_utils
from modelop_sdk.utils import dict_utils as dict_utils

def calculate_stability(baseline, comparator, init_param) -> dict:
    """
    Source: https://github.com/modelop/moc_monitors/tree/main/src/modelop/ootb_monitors/stability_analysis

    Evaluation Metrics (Source:https://modelop.atlassian.net/wiki/spaces/~355140182/pages/2286944283/Dashboard+3.0+monitors):
        max( <predictive_feature.stability_index>:)
        i.e. the max of all the stability indexes across all features
    ---- Heatmap criteria
        max(stability_index) > 0.2 → RED
        0.1 < max(stability_index) < 0.2 → YELLOW
        max(stability_index) < 0.1 → GREEN
        max(stability_index) IS NULL or test fails → GRAY
    """
    LOG = logger.configure_logger()

    dashboard_utils.assert_df_not_none_and_not_empty(baseline, "Required baseline")
    dashboard_utils.assert_df_not_none_and_not_empty(comparator, "Required comparator")

    stability_analysis.init(init_param)
    monitor_results = stability_analysis.metrics(baseline, comparator)

    for result in monitor_results:
        stability_analysis_metrics = result

    LOG.debug(f"stability_analysis_metrics {stability_analysis_metrics}")

    try:
        csi_values = dict_utils.get_entries_with_suffix_and_numeric_values(stability_analysis_metrics, "_CSI")
    except Exception as ex:
        raise ValueError(f"Error while extracting Stability analysis '_CSI' values : {str(ex)} ")

    csi_array = dict_utils.extract_numeric_values_to_array(csi_values)

    if len(csi_array) == 0:
        raise ValueError(
            f" No numerics values found at the `csi_array` results field {str(stability_analysis_metrics)} ")

    characteristic_stability_max_csi_result = {"characteristic_stability_max_stability_index": max(csi_array)}
    LOG.info(f" characteristic_stability_max_csi_result {str(characteristic_stability_max_csi_result)}")
    stability_analysis_metrics.update(characteristic_stability_max_csi_result)

    return stability_analysis_metrics
