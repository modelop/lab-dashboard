from modelop.ootb_monitors.concept_drift_kolmogorov_smirnov import concept_drift_kolmogorov_smirnov
import modelop_sdk.utils.logging as logger
from modelop_sdk.utils import dashboard_utils as dashboard_utils
from modelop_sdk.utils import dict_utils as dict_utils

def calculate_concept_drift(baseline, comparator, init_param) -> dict:
    """
    Source:  https://github.com/modelop/moc_monitors/tree/main/src/modelop/ootb_monitors/concept_drift_kolmogorov_smirnov

    Evaluation Metrics (Source:https://modelop.atlassian.net/wiki/spaces/~355140182/pages/2286944283/Dashboard+3.0+monitors):
        max( <score_column>: <p-value>)
        i.e. the max of all the p-values across the score columns (usually there is only one but there could
        be multiple)
    ---- Heatmap criteria
        max(p-value) > 2 → RED
        1 < max(p-value) < 2 → YELLOW
        max(p-value) < 1 → GREEN
        max(p-value) IS NULL or test fails → GRAY

    """
    LOG = logger.configure_logger()

    dashboard_utils.assert_df_not_none_and_not_empty(baseline, "Required baseline")
    dashboard_utils.assert_df_not_none_and_not_empty(comparator, "Required comparator")

    concept_drift_kolmogorov_smirnov.init(init_param)
    monitor_results = concept_drift_kolmogorov_smirnov.metrics(baseline, comparator)

    for result in monitor_results:
        concept_drift = result

    try:
        concept_drift_pvalues = dict_utils.get_entries_with_suffix_and_numeric_values(concept_drift, "_pvalue")
    except Exception as ex:
        raise ValueError(f"Error while extracting Concept Drift KS '_pvalue' : {str(ex)} ")

    p_value_array = dict_utils.extract_numeric_values_to_array(concept_drift_pvalues)
    if len(p_value_array) == 0:
        raise ValueError(
            f" No numerics values found at the 'values' concept drift generated results field {str(concept_drift)} ")

    concept_drift_max_p_value = {"concept_drift_max_p_value": max(p_value_array)}
    LOG.debug(f"Adding generated : {concept_drift_max_p_value}")
    concept_drift.update(concept_drift_max_p_value)
    return concept_drift
