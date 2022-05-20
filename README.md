# Regression ROI Monitor
This ModelOp Center monitor computes **Return-on-Investment projections** given a slice of scored production data (containing model outputs) for regression problems.

## Input Assets

| Type | Number | Description |
| ------ | ------ | ------ |
| Baseline Data | **0** | |
| Sample Data | **1** |  A dataset corresponding to a slice of production data |

## Assumptions & Requirements
 - Underlying `BUSINESS_MODEL` being monitored is a **regression** model.
 - `BUSINESS_MODEL` has 
     - a **modelop parameters** file (`.json`) defining monitoring parameters, such as
     ```json
     {
         "monitoring": {
             "performance": {
                 "model_type": "regression",
             },
             "business_value": {
                 "ROI": {
                     "label_field": <name_of_ground_truth_feature>,
                     "baseline_field": <name_of_baseline_to_compare_model_output_against>,
                     "action_field": <name_of_action_take_field>,
                     "cost_multipliers": {
                         "TP": <true_positive_cost_multiplier>,
                         "FP": <false_positive_cost_multiplier>,
                         "TN": <true_negative_cost_multiplier>,
                         "FN": <false_negative_cost_multiplier>
                     }
                 }
             }
         }
     }
     ```

## Execution
1. `init` function loads the `modelop_parameters.json` file and sets global monitoring variables.
2. `metrics` function computes actual ROI by classifying input records and then calling the `compute_actual_roi` function.
3. Test results are appended to the list of `business_value` tests to be returned by the model.

## Monitor Output

```JSON
{
    "actual_roi": <actual_roi_amount>,
    "label_field": <name_of_ground_truth_feature>,
    "baseline_field": <name_of_baseline_to_compare_model_output_against>,
    "business_value": [
        {
            "test_name": "Regression ROI",
            "test_category": "business_value",
            "test_type": "regression_roi",
            "test_id": "business_value_regression_roi",
            "values": {
                "actual_roi": <actual_roi_amount>,
                "cost_multipliers": {
                    "TP": <true_positive_cost_multiplier>,
                    "FP": <false_positive_cost_multiplier>,
                    "TN": <true_negative_cost_multiplier>,
                    "FN": <false_negative_cost_multiplier>
                }
            }
        }
    ]
}
```