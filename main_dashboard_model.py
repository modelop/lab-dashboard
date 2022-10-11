import json
from datetime import datetime

import default_actual_roi_monitor as classification_roi_monitor
import regression_ROI_monitor as regression_roi_monitor
import modelop.monitors.bias as bias
import modelop.monitors.drift as drift
import modelop.monitors.performance as performance
import modelop.monitors.stability as stability
import modelop.monitors.volumetrics as volumetrics
import modelop.schema.infer as infer
import modelop.utils as utils
import modelop_sdk.apis.mlc_api as mlc
import modelop_sdk.restclient.moc_client as moc_client
import modelop_sdk.utils.logging as logger
from modelop_sdk.utils import dashboard_utils, dict_utils


LOG = logger.configure_logger()

JOB = {}
DEPLOYABLE_MODEL = {}
MODEL_METHODOLOGY = ""

# modelop.init
def init(job_json):
    global JOB
    global DEPLOYABLE_MODEL
    global MODEL_METHODOLOGY

    job = json.loads(job_json["rawJson"])
    DEPLOYABLE_MODEL = job.get("referenceModel", None)
    JOB = job_json
    MODEL_METHODOLOGY = (
        DEPLOYABLE_MODEL.get("storedModel", {})
        .get("modelMetaData", {})
        .get("modelMethodology", "")
    )

    infer.validate_schema(job_json)


# modelop.metrics
def metrics(baseline, comparator) -> dict:
    LOG.info("Building monitors")
    result = {}

    # some code for gr
    heat_map = {}
    flat_heatmap = {}
    execution_errors_array = []
    LOG.info("Executing monitors")

    result = utils.merge(
        extract_model_fields(execution_errors_array),
        calculate_roi(comparator, execution_errors_array),
        calculate_daily_inferences(comparator, execution_errors_array),
        calculate_data_drift(baseline, comparator, execution_errors_array),
        calculate_concept_drift(baseline, comparator, execution_errors_array),
        calculate_performance(comparator, execution_errors_array),
        calculate_stability(baseline, comparator, execution_errors_array),
        calculate_bias(comparator, execution_errors_array),
    )

    try:
        LOG.info("Performing DMN evaluation")
        client = moc_client.MOCClient()
        mlc_api = mlc.MLCApi(client)
        evaluated_results = mlc_api.evaluate_results(result, "dashboard_model.dmn")
        LOG.info("Generating heatMap")
        heat_map["heatMap"] = dashboard_utils.generate_heatmap(evaluated_results)
        flat_heatmap = dict_utils.flatten_data(heat_map)
    except Exception as eval_ex:
        heat_map = {"heatMap": {}}
        LOG.error(str(eval_ex))
        execution_errors_array.append(
            "Something went wrong during DMN evaluation or heatmap generation, please check logs"
        )

    dashboard_result = {"createdDate": datetime.now().strftime("%m/%d/%Y %H:%M:%S")}
    dashboard_result = utils.merge(
        dashboard_result,
        result,
        heat_map,
        flat_heatmap,
    )

    dashboard_result.update({"executionErrors": execution_errors_array})
    dashboard_result.update({"executionErrorsCount": len(execution_errors_array)})

    yield dashboard_result


def extract_model_fields(execution_errors_array):
    try:
        return {
            "modelUseCategory": DEPLOYABLE_MODEL.get("storedModel", {})
            .get("modelMetaData", {})
            .get("modelUseCategory", ""),
            "modelOrganization": DEPLOYABLE_MODEL.get("storedModel", {})
            .get("modelMetaData", {})
            .get("modelOrganization", ""),
            "modelRisk": DEPLOYABLE_MODEL.get("storedModel", {})
            .get("modelMetaData", {})
            .get("modelRisk", ""),
            "modelMethodology": MODEL_METHODOLOGY,
        }
    except Exception as ex:
        error_message = (
            f"Something went wrong when extracting modelop default fields: {str(ex)}"
        )
        execution_errors_array.append(error_message)
        LOG.error(error_message)
        return {}


def calculate_roi(comparator, execution_errors_array) -> dict:
    try:
        dashboard_utils.assert_df_not_none_and_not_empty(
            comparator, "Required comparator"
        )
        if "regression" in MODEL_METHODOLOGY.casefold():
            return {
                "actualROIAllTime": regression_roi_monitor.calculate_roi(comparator, JOB)
            }
        else:
            return {
                "actualROIAllTime": classification_roi_monitor.calculate_roi(comparator, JOB)
            }
    except Exception as err:
        error_message = f"Something went wrong with the ROI monitor: {str(err)}"
        LOG.error(error_message)
        execution_errors_array.append(error_message)
        return {"actualROIAllTime": "N/A"}


def calculate_daily_inferences(comparator, execution_errors_array) -> dict:
    try:
        dashboard_utils.assert_df_not_none_and_not_empty(
            comparator, "Required comparator"
        )
        volumetric_monitor = volumetrics.VolumetricMonitor(comparator)
        # Initialize Volumetric monitor with 1st input DataFrame
        return {
            "allVolumetricMonitorRecordCount": volumetric_monitor.count()[
                "record_count"
            ]
        }
    except Exception as err:
        error_message = (
            f"Something went wrong with the Volumetrics count monitor: {str(err)}"
        )
        LOG.error(error_message)
        execution_errors_array.append(error_message)
        return {"allVolumetricMonitorRecordCount": "N/A"}


def calculate_data_drift(baseline, comparator, execution_errors_array) -> dict:
    """
    Evaluation Metrics Source:https://modelop.atlassian.net/wiki/spaces/~355140182/pages/2286944283/Dashboard+3.0+monitors:
        max( <feature_1>: <p-value>,...:...,<feature_n>: <p-value>)
        i.e. the max of all the p-values across all the features
    ---- Heatmap criteria
        max(p-value) > 2 → RED
        1 < max(p-value) < 2 → YELLOW
        max(p-value) < 1 → GREEN
        max(p-value) IS NULL or test fails → GRAY
    """
    try:
        dashboard_utils.assert_df_not_none_and_not_empty(baseline, "Required baseline")
        dashboard_utils.assert_df_not_none_and_not_empty(
            comparator, "Required comparator"
        )
        drift_monitor = drift.DriftDetector(
            df_baseline=baseline, df_sample=comparator, job_json=JOB
        )

        return drift_monitor.calculate_drift(pre_defined_test="Kolmogorov-Smirnov")
    except Exception as err:
        error_message = f"Something went wrong with Data Drift KS monitor: {str(err)}"
        LOG.error(error_message)
        execution_errors_array.append(error_message)
        return {"DataDrift_maxKolmogorov-SmirnovPValue": -99}


def calculate_concept_drift(baseline, comparator, execution_errors_array) -> dict:
    """
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
    try:
        dashboard_utils.assert_df_not_none_and_not_empty(baseline, "Required baseline")
        dashboard_utils.assert_df_not_none_and_not_empty(
            comparator, "Required comparator"
        )
        concept_drift_monitor = drift.ConceptDriftDetector(
            df_baseline=baseline, df_sample=comparator, job_json=JOB
        )
        return concept_drift_monitor.calculate_concept_drift(
            pre_defined_test="Kolmogorov-Smirnov"
        )
    except Exception as err:
        error_message = f"Something went wrong with Concept Drift monitor: {str(err)}"
        LOG.error(error_message)
        execution_errors_array.append(error_message)
        return {"ConceptDrift_maxKolmogorov-SmirnovPValueValue": -99}


def calculate_performance(comparator, execution_errors_array) -> dict:
    """
    Evaluation Metrics (Source:https://modelop.atlassian.net/wiki/spaces/~355140182/pages/2286944283/Dashboard+3.0+monitors):
        <auc>
    ---- Heatmap criteria
        <auc> > 0.7 → GREEN
        0.6 < <auc> < 0.7 → YELLOW
        <auc> < 0.6 → RED
        <auc> IS NULL or test fails → GRAY
    """
    try:
        dashboard_utils.assert_df_not_none_and_not_empty(
            comparator, "Required comparator"
        )
        performance_monitor = performance.ModelEvaluator(
            dataframe=comparator, job_json=JOB
        )
        if "regression" in MODEL_METHODOLOGY.casefold():
            return performance_monitor.evaluate_performance(
                pre_defined_metrics="regression_metrics"
            )
        else:
            return performance_monitor.evaluate_performance(
                pre_defined_metrics="classification_metrics"
            )
    except Exception as err:
        error_message = (
            f"Something went wrong with Statistical Performance monitor: {str(err)}"
        )
        LOG.error(error_message)
        execution_errors_array.append(error_message)
        return {"auc": -99}


def calculate_stability(baseline, comparator, execution_errors_array) -> dict:
    """
    Evaluation Metrics (Source:https://modelop.atlassian.net/wiki/spaces/~355140182/pages/2286944283/Dashboard+3.0+monitors):
        max( <predictive_feature.stability_index>:)
        i.e. the max of all the stability indexes across all features
    ---- Heatmap criteria
        max(stability_index) > 0.2 → RED
        0.1 < max(stability_index) < 0.2 → YELLOW
        max(stability_index) < 0.1 → GREEN
        max(stability_index) IS NULL or test fails → GRAY
    """
    try:
        if DEPLOYABLE_MODEL.get("modelMetaData",{}).get("custom",{}).get("Monitor_Stability",{}):
            dashboard_utils.assert_df_not_none_and_not_empty(baseline, "Required baseline")
            dashboard_utils.assert_df_not_none_and_not_empty(
                comparator, "Required comparator"
            )
            stability_monitor = stability.StabilityMonitor(
                baseline, comparator, job_json=JOB
            )
            return stability_monitor.compute_stability_indices()
        else:
            raise Exception('Skipping Stability Monitor due to model configuration')
    except Exception as err:
        error_message = (
            f"Something went wrong with Characteristic Stability monitor: {str(err)}"
        )
        LOG.error(error_message)
        execution_errors_array.append(error_message)
        return {"CSI_maxCSIValue": -99}


def calculate_bias(comparator, execution_errors_array) -> dict:
    """
    Evaluation Metrics (Source:https://modelop.atlassian.net/wiki/spaces/~355140182/pages/2286944283/Dashboard+3.0+monitors):
        max(ppr_disparity) and min(ppr_disparity) across all protected classes
    ---- Heatmap criteria
        max(ppr_disparity)>1.2 or min(ppr_disparity) <0.8  → RED
        max(ppr_disparity)<1.2 or min(ppr_disparity) >0.8  → GREEN
    """
    try:
        dashboard_utils.assert_df_not_none_and_not_empty(
            comparator, "Required comparator"
        )
        if "regression" in MODEL_METHODOLOGY.casefold():
            raise Exception("Bias monitor can not be run for regression models.")
        bias_monitor = bias.BiasMonitor(dataframe=comparator, job_json=JOB)
        return bias_monitor.compute_bias_metrics()
    except Exception as err:
        error_message = (
            f"Something went wrong with Ethical Fairness monitor: {str(err)}"
        )
        LOG.error(error_message)
        execution_errors_array.append(error_message)
        return {"Bias_maxPPRDisparityValue": -99, "Bias_minPPRDisparityValue": -99}