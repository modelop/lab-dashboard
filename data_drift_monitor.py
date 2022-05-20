import modelop_sdk.utils.logging as logger
from modelop.ootb_monitors.data_drift_kolmogorov_smirnov import data_drift_kolmogorov_smirnov
from modelop_sdk.utils import dashboard_utils as dashboard_utils
from modelop_sdk.utils import dict_utils as dict_utils

def calculate_data_drift(baseline, comparator, init_param) -> dict:
    """
    Source: https://github.com/modelop/moc_monitors/tree/main/src/modelop/ootb_monitors/data_drift_kolmogorov_smirnov

    Evaluation Metrics Source:https://modelop.atlassian.net/wiki/spaces/~355140182/pages/2286944283/Dashboard+3.0+monitors:
        max( <feature_1>: <p-value>,...:...,<feature_n>: <p-value>)
        i.e. the max of all the p-values across all the features
    ---- Heatmap criteria
        max(p-value) > 2 → RED
        1 < max(p-value) < 2 → YELLOW
        max(p-value) < 1 → GREEN
        max(p-value) IS NULL or test fails → GRAY
    """
    LOG = logger.configure_logger()

    dashboard_utils.assert_df_not_none_and_not_empty(baseline, "Required baseline")
    dashboard_utils.assert_df_not_none_and_not_empty(comparator, "Required comparator")

    data_drift_kolmogorov_smirnov.init(init_param)
    monitor_results = data_drift_kolmogorov_smirnov.metrics(baseline, comparator)

    for result in monitor_results:
        drift_metrics = result

    LOG.debug(f"drift_metrics {drift_metrics}")

    try:
        data_drift_values = dict_utils.get_entries_with_suffix_and_numeric_values(drift_metrics, "_pvalue")
    except Exception as ex:
        raise ValueError(f"Error while extracting Data Drift KS '_pvalue' : {str(ex)} ")

    p_value_array = dict_utils.extract_numeric_values_to_array(data_drift_values)

    if len(p_value_array) == 0:
        raise ValueError(
            f" No numerics values found at the 'values' data drift generated results field {str(drift_metrics)} ")

    data_drift_kr_result = {"data_drift_max_p_value": max(p_value_array)}
    LOG.info(f" data_drift_ks_result {str(data_drift_kr_result)}")
    drift_metrics.update(data_drift_kr_result)
    return drift_metrics
