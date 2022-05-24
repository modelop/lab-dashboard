from modelop.ootb_monitors.performance_regression import performance_regression
from modelop_sdk.utils import dashboard_utils as dashboard_utils


def calculate_performance(comparator, init_param) -> dict:
    """
    Source - https://github.com/modelop/moc_monitors/blob/main/src/modelop/ootb_monitors/performance_regression/performance_regression.py
    Monitor result
    {
        "mae": <mae>,
        "rmse": <rmse>,
        "r2_score": <r2_score>,
        "performance": [
            {
                "test_category": "performance",
                "test_name": "Regression Metrics",
                "test_type": "regression_metrics",
                "test_id": "performance_regression_metrics",
                "values": {
                    "mae": <mae>,
                    "rmse": <rmse>,
                    "r2_score": <r2_score>
                }
            }
        ]
    }

    """

    dashboard_utils.assert_df_not_none_and_not_empty(comparator, "Required comparator")
    performance_regression.init(init_param)
    monitor_results = performance_regression.metrics(comparator)

    for result in monitor_results:
        performance_results = result

    # Generating one output for evaluation
    raw_values_for_evaluation = {"statistical_performance_val": performance_results["r2_score"]}
    performance_results.update(raw_values_for_evaluation)
    return raw_values_for_evaluation