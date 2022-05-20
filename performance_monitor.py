from modelop.ootb_monitors.performance_classification import performance_classification
from modelop_sdk.utils import dashboard_utils as dashboard_utils


def calculate_performance(comparator, init_param) -> dict:
    """
    Source - https://github.com/modelop/moc_monitors/tree/main/src/modelop/ootb_monitors/performance_classification
    Monitor result
    {
      "test_name": "Classification Metrics",
      "test_category": "performance",
      "test_type": "classification_metrics",
      "test_id": "performance_classification_metrics",
      "values": {
        "accuracy": 0.665,
        "precision": 0.4516,
        "recall": 0.7241,
        "f1_score": 0.5563,
        "auc": 0.6825,  <--- value used for evaluation
        "confusion_matrix": [
          {
            "0": 0.455,
            "1": 0.255
          },
          {
            "0": 0.08,
            "1": 0.21
          }
        ]
      }
    }

    Evaluation Metrics (Source:https://modelop.atlassian.net/wiki/spaces/~355140182/pages/2286944283/Dashboard+3.0+monitors):
        <auc>
    ---- Heatmap criteria
        <auc> > 0.7 → GREEN
        0.6 < <auc> < 0.7 → YELLOW
        <auc> < 0.6 → RED
        <auc> IS NULL or test fails → GRAY
    """

    dashboard_utils.assert_df_not_none_and_not_empty(comparator, "Required comparator")
    performance_classification.init(init_param)
    monitor_results = performance_classification.metrics(comparator)

    for result in monitor_results:
        performance_results = result

    # Generating one output for evaluation
    raw_values_for_evaluation = {"statistical_performance_auc": performance_results["auc"]}
    performance_results.update(raw_values_for_evaluation)
    return raw_values_for_evaluation
