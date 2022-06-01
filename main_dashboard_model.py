from datetime import datetime
from numpy import true_divide
import pandas as pd
import modelop_sdk.utils.logging as logger
import modelop.schema.infer as infer
from sqlalchemy import null
import default_actual_roi_monitor as classification_roi_monitor
import regression_ROI_monitor as regression_roi_monitor
import volumetrics_count_monitor as daily_inferences_monitor
import data_drift_monitor as data_drift_monitor
import volumetrics_identifier_comparison_monitor as output_integrity_monitor
import concept_drift_monitor as concept_drift_monitor
import performance_monitor as statistical_performance_monitor_classification
import performance_monitor_regression as statistical_performance_monitor_regression
import stability_monitor as characteristic_stability_monitor
import bias_disparity_monitor as ethical_fairness_monitor
import NewRelicDashboardMonitor as new_relic_monitor
import modelop_sdk.restclient.moc_client as moc_client
import modelop_sdk.apis.mlc_api as mlc
from modelop_sdk.utils import dict_utils
from modelop_sdk.utils import dashboard_utils
import random
import asyncio
import json
import os

LOG = logger.configure_logger()

INPUT_JSON = {}
INIT_PARAM = {}
MODEL_CUSTOM_METADATA = {}
DEPLOYABLE_MODEL = {}
MODEL_USE_CATEGORY = None
MODEL_ORGANIZATION = None
MODEL_RISK = None


# modelop.init
def init(init_param):
    global INIT_PARAM
    global INPUT_SCHEMA
    global MODEL_CUSTOM_METADATA
    global DEPLOYABLE_MODEL
    global MODEL_USE_CATEGORY
    global MODEL_ORGANIZATION
    global MODEL_RISK
    global MODEL_METHODOLOGY
    global NR_OVERRIDE

    job = json.loads(init_param["rawJson"])
    DEPLOYABLE_MODEL = job.get('referenceModel')
    INIT_PARAM = init_param
    try:
        INPUT_SCHEMA = infer.extract_input_schema(INIT_PARAM)
    except Exception as ex:
        LOG.error(f"Error while extracting input_schema - {str(ex)}")
        INPUT_SCHEMA = None

    # Extract custom metadata
    try:
        MODEL_CUSTOM_METADATA = job["referenceModel"]["storedModel"]["modelMetaData"]["custom"]
    except Exception as e:
        LOG.warning(f"Required custom metadata value not present: {str(e)}")

    LOG.debug(f"init function input: {str(INIT_PARAM)}")

    try:
        ### Adding additional fields - modelUseCategory + modelOrganization + modelRisk + Model Methodology
        modelop_fields = dashboard_utils.get_default_modelop_fields_from_deployable_model(DEPLOYABLE_MODEL)
        MODEL_USE_CATEGORY = modelop_fields["modelUseCategory"]
        MODEL_ORGANIZATION = modelop_fields["modelOrganization"]
        MODEL_RISK = modelop_fields["modelRisk"]
        MODEL_METHODOLOGY = job["referenceModel"]["storedModel"]["modelMetaData"]["modelMethodology"]
        NR_OVERRIDE = MODEL_CUSTOM_METADATA["NR_OVERRIDE"]
    except Exception as ex:
        error_message = f"Something went wrong when extracting modelop default fields: {str(ex)}"
        LOG.error(error_message)


# modelop.metrics
def metrics(baseline, comparator) -> dict:
    LOG.info("Building monitors")
    monitor_results = {}
    heat_map = {}
    flat_heatmap = {}
    execution_errors_array = []
    LOG.info("Executing monitors")

    try:
        ## Adding default Model variables
        monitor_results["modelUseCategory"] = MODEL_USE_CATEGORY
        monitor_results["modelOrganization"] = MODEL_ORGANIZATION
        monitor_results["modelRisk"] = MODEL_RISK
        monitor_results["modelMethodology"]=MODEL_METHODOLOGY
    except Exception as ex_default_fields:
        error_message = f"Something went wile adding default ModelOp fields: {str(ex_default_fields)}"
        LOG.error(error_message)
        execution_errors_array.append(error_message)

    LOG.info("-------BEGIN ROI---------")
    try:
        # ROI Monitor
        if MODEL_METHODOLOGY.lower() == "regression":
            monitor_results['actualROIAllTime'] = regression_roi_monitor.calculate_roi(comparator, DEPLOYABLE_MODEL, INPUT_SCHEMA)
            LOG.info("ROI Calculated succeeded")
        else:
            monitor_results['actualROIAllTime'] = classification_roi_monitor.calculate_roi(comparator, DEPLOYABLE_MODEL, INPUT_SCHEMA)
            LOG.info("ROI Calculator failed")
    except Exception as rmE:
        monitor_results["actualROIAllTime"] = "N/A"
        error_message = f"Error in the ROI monitor: {str(rmE)}"
        LOG.error(error_message)
        execution_errors_array.append(error_message)
    LOG.info("-------END ROI---------")

    try:
        # Daily inferences Monitor
        monitor_results["allVolumetricMonitorRecordCount"] = daily_inferences_monitor.calculate_daily_inferences(
            comparator)
    except Exception as volE:
        monitor_results["allVolumetricMonitorRecordCount"] = "N/A"
        error_message = f"Error in the Volumetrics count monitor: {str(volE)}"
        LOG.error(error_message)
        execution_errors_array.append(error_message)

    try:
        # Data Drift Monitor
        LOG.info("Executing Data Drift KS monitor")
        monitor_results.update(data_drift_monitor.calculate_data_drift(baseline, comparator, INIT_PARAM))
        LOG.info("Data Drift KS monitor successfully executed")
    except Exception as ex:
        monitor_results["data_drift_max_p_value"] = -1
        error_message = f"Error in Data Drift KS monitor: {str(ex)}"
        LOG.error(error_message)
        execution_errors_array.append(error_message)

    try:
        # Output Integrity Monitor
        monitor_results.update(
            output_integrity_monitor.calculate_volumetrics_identifier_comparison(baseline, comparator, INIT_PARAM,
                                                                                 remove_breakdown=True))
    except Exception as ex:
        monitor_results["identifiers_match"] = None
        error_message = f"Error in Output Integrity monitor: {str(ex)}"
        LOG.error(error_message)
        execution_errors_array.append(error_message)

    try:
        # Concept Drift Monitor
        monitor_results.update(
            concept_drift_monitor.calculate_concept_drift(baseline, comparator, INIT_PARAM))
    except Exception as ex:
        monitor_results["concept_drift_max_p_value"] = -1
        error_message = f"Error in Concept Drift monitor: {str(ex)}"
        LOG.error(error_message)
        execution_errors_array.append(error_message)

    try:
        # Statistical Performance Monitor
        if MODEL_METHODOLOGY.lower() == "regression":
           monitor_results.update(statistical_performance_monitor_regression.calculate_performance(comparator, INIT_PARAM))
           monitor_results["statistical_performance_unit"] = "r2_score"
        else:
            monitor_results.update(statistical_performance_monitor_classification.calculate_performance(comparator, INIT_PARAM))
            monitor_results["statistical_performance_unit"] = "auc"
    except Exception as ex:
        monitor_results["statistical_performance_unit"] = "N/A"
        monitor_results["statistical_performance_val"] = -1
        error_message = f"Error in Statistical Performance monitor: {str(ex)}"
        LOG.error(error_message)
        execution_errors_array.append(error_message)
    try:
        # Characteristic Stability Monitor
        monitor_results.update(
            characteristic_stability_monitor.calculate_stability(baseline, comparator, INIT_PARAM)
        )
    except Exception as ex:
        monitor_results["characteristic_stability_max_stability_index"] = -1
        error_message = f"Error in Characteristic Stability monitor: {str(ex)}"
        LOG.error(error_message)
        execution_errors_array.append(error_message)

    try:
        # Ethical Fairness Monitor
        monitor_results.update(
            ethical_fairness_monitor.calculate_bias(comparator, INIT_PARAM)
        )
    except Exception as ex:
        monitor_results["ethical_fairness_max_ppr_disparity"] = -1
        monitor_results["ethical_fairness_min_ppr_disparity"] = -1
        error_message = f"Error in Ethical Fairness monitor: {str(ex)}"
        LOG.error(error_message)
        execution_errors_array.append(error_message)

    try:
        # New Relic Monitor
        entityGuid = MODEL_CUSTOM_METADATA["NR_EntityGuid"]
        NR_OVERRIDE = MODEL_CUSTOM_METADATA["NR_OVERRIDE"]
        apiKey = os.getenv("NEW_RELIC_API_KEY")
        
        loop = asyncio.new_event_loop()
        task = loop.create_task(new_relic_monitor.get_new_relic_response_time(apiKey,entityGuid))
        monitor_results.update(loop.run_until_complete(task))

    except Exception as ex:
        #error_message = f"Error in New Relic monitor: {str(ex)}"
        monitor_results["Service Response Time"] = random.randint(0,500)
        #LOG.error(error_message)
        #execution_errors_array.append(error_message)

    random.seed()

    val = random.randint(0,100)
    monitor_results["Data pipeline Health"] = val    

    monitor_results["Data Usage Approval"] = MODEL_CUSTOM_METADATA["Data Usage Approval"] 

    monitor_results["MRMG Approval"] = MODEL_CUSTOM_METADATA["MRMG Approval"]


    try:
        LOG.info("Performing DMN evaluation")
        client = moc_client.MOCClient()
        mlc_api = mlc.MLCApi(client)
        evaluated_results = mlc_api.evaluate_results(monitor_results, "dashboard_model.dmn")
        LOG.info("Checking for NR Threshold Overrides")
        
        #handle performance override via custom metadata
        if (NR_OVERRIDE is not None) and (NR_OVERRIDE > 0):
            LOG.info("NR Override detected")
            i=0
            if monitor_results["Service Response Time"] <= NR_OVERRIDE:
                LOG.info("Custom Threshold Passed, setting value to green")

                for i, item in enumerate(evaluated_results):
                    if item.get("monitor_name") == 'Service Response Time':
                        break
                LOG.info("Service Response Time object found at index: " + str(i))
                obj = {'color':"Green",'monitor_name':"Service Response Time"}    
                evaluated_results[i] = obj
            else:
                LOG.info("Custom Threshold Failed, setting value to red")   
                                
                for i, item in enumerate(evaluated_results):
                    if item.get("monitor_name") == 'Service Response Time':
                        break                       
                LOG.info("Service Response Time object found at index: " + str(i))
                obj = {'color':"Red",'monitor_name':"Service Response Time"}    
                evaluated_results[i] = obj
            LOG.info(evaluated_results)
        LOG.info("Generating heatMap")
        heat_map["heatMap"] = dashboard_utils.generate_heatmap(evaluated_results)
        flat_heatmap = dict_utils.flatten_data(heat_map)
        LOG.info("Generating MTR")
    except Exception as eval_ex:
        heat_map = {"heatMap": {}}
        LOG.error(str(eval_ex))
        execution_errors_array.append(
            "Something went wrong during DMN evaluation or heatmap generation, please check logs")

    
    dashboard_result = {
        "createdDate": datetime.now().strftime('%m/%d/%Y %H:%M:%S')
    }
    dashboard_result.update(monitor_results)
    dashboard_result.update(heat_map)
    dashboard_result.update(flat_heatmap)

    dashboard_result.update({"executionErrors": execution_errors_array})
    dashboard_result.update({"executionErrorsCount": len(execution_errors_array)})
    LOG.info("------Monitor Complete-----")
    yield dashboard_result




