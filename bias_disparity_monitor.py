from modelop.ootb_monitors.bias_disparity import bias_disparity
import modelop_sdk.utils.logging as logger
from modelop_sdk.utils import dashboard_utils as dashboard_utils
from modelop_sdk.utils import dict_utils as dict_utils


def calculate_bias(comparator, init_param) -> dict:
    """
    Source: https://github.com/modelop/moc_monitors/tree/main/src/modelop/ootb_monitors/bias_disparity
    Sample Output:
            {
              "test_name": "Aequitas Bias",
              "test_category": "bias",
              "test_type": "bias",
              "protected_class": "gender",
              "test_id": "bias_bias_gender",
              "reference_group": "male",
              "thresholds": {
                "min": 0.8,
                "max": 1.25
              },
              "values": [
                {
                  "attribute_name": "gender",
                  "attribute_value": "female",
                  "ppr_disparity": 0.5,
                  "pprev_disparity": 0.8889,
                  "precision_disparity": 1.36,
                  "fdr_disparity": 0.7568,
                  "for_disparity": 1.6098,
                  "fpr_disparity": 0.7648,
                  "fnr_disparity": 1.32,
                  "tpr_disparity": 0.8976,
                  "tnr_disparity": 1.15,
                  "npv_disparity": 0.9159
                },
                {
                  "attribute_name": "gender",
                  "attribute_value": "male",
                  "ppr_disparity": 1,
                  "pprev_disparity": 1,
                  "precision_disparity": 1,
                  "fdr_disparity": 1,
                  "for_disparity": 1,
                  "fpr_disparity": 1,
                  "fnr_disparity": 1,
                  "tpr_disparity": 1,
                  "tnr_disparity": 1,
                  "npv_disparity": 1
                }
              ]
            }
    ---
    Evaluation Metrics (Source:https://modelop.atlassian.net/wiki/spaces/~355140182/pages/2286944283/Dashboard+3.0+monitors):
        max(ppr_disparity) and min(ppr_disparity) across all protected classes
    ---- Heatmap criteria
        max(ppr_disparity)>1.2 or min(ppr_disparity) <0.8  → RED
        max(ppr_disparity)<1.2 or min(ppr_disparity) >0.8  → GREEN
    """
    LOG = logger.configure_logger()

    dashboard_utils.assert_df_not_none_and_not_empty(comparator, "Required comparator")
    # monitor execution
    bias_disparity.init(init_param)
    monitor_results = bias_disparity.metrics(comparator)

    for result in monitor_results:
        bias_disparity_metrics = result

    try:
        bias_disparity_statistical_parity_values = dict_utils.get_entries_with_suffix_and_numeric_values(
            bias_disparity_metrics, "_statistical_parity")
    except Exception as ex:
        raise ValueError(f"Error while extracting '_statistical_parity' : {str(ex)} ")

    statistical_parity_array = dict_utils.extract_numeric_values_to_array(bias_disparity_statistical_parity_values)

    if len(statistical_parity_array) == 0:
        raise ValueError(
            f" No numerics _statistical_parity values found at bias_disparity_metrics")

    ethical_fairness_max_ppr_disparity_result = {"ethical_fairness_max_ppr_disparity": max(statistical_parity_array),
                                                 "ethical_fairness_min_ppr_disparity": min(statistical_parity_array)}
    LOG.info(f" ethical_fairness_max_ppr_disparity_result {str(ethical_fairness_max_ppr_disparity_result)}")
    bias_disparity_metrics.update(ethical_fairness_max_ppr_disparity_result)

    LOG.debug(f"bias_disparity {bias_disparity_metrics}")

    return bias_disparity_metrics
