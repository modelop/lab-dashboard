import json
from datetime import datetime

import modelop.schema.infer as infer
import modelop.utils as utils
import modelop_sdk.apis.mlc_api as mlc
import modelop_sdk.restclient.moc_client as moc_client
import modelop_sdk.utils.logging as logger
from modelop_sdk.utils import dashboard_utils, dict_utils
import modelop_sdk.apis.model_manage_api as model_manage
import uuid
from dateutil.parser import parse


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
    result = {}
    heat_map = {}
    flat_heatmap = {}
    execution_errors_array = []
    results_with_defaults = {
        "CSI_maxCSIValue": -99,
        "auc": -99,
        "r2_score": 99,
        "Bias_maxPPRDisparityValue": -99,
        "Bias_minPPRDisparityValue": -99,
        "DataDrift_maxKolmogorov-SmirnovPValue": -99,
        "ConceptDrift_maxKolmogorov-SmirnovPValueValue": -99
    }

    client = moc_client.MOCClient()
    mtr_summary_api = model_manage.ModelTestResultSummariesApi(client)
    mtr_api = model_manage.ModelTestResultsApi(client)
    mlc_api = mlc.MLCApi(client)

    def get_associated_model_latest_mtrs_mapper(model_association):
        associated_model_id = uuid.UUID(model_association.get("associatedModel", {}).get("id"))
        associated_model_name = model_association.get("associatedModel", {}).get("storedModel", {}).get("modelMetaData", {}).get("name", "No name found")
        response_of_model_test_result_summaries = mtr_summary_api.find_all_by_optional(
            deployable_model_id=uuid.UUID(DEPLOYABLE_MODEL.get("id")),
            associated_model_snapshot_id=associated_model_id,
            sort="createdDate,desc", page=0, size=1)
        if len(response_of_model_test_result_summaries.get("_embedded", {}).get("modelTestResultSummaries", [])) > 0:
            mtr_summary = response_of_model_test_result_summaries.get("_embedded", {}).get("modelTestResultSummaries", [])[0]
            mtr = mtr_api.get(mtr_summary.get("id"))
            return mtr
        else:
            LOG.error(f"Couldn't find Model Test Result for deployableModel " + str(DEPLOYABLE_MODEL.get("id")) +
                      " and associated model " + str(associated_model_name) + " (" + str(associated_model_id) + ")")
            return None

    LOG.info("Number of associated models in the business model: " + str(len(DEPLOYABLE_MODEL.get("associatedModels", []))))
    if len(DEPLOYABLE_MODEL.get("associatedModels", [])) == 0:
        raise Exception("No associated models were found in the current business model ")

    mtrs = list(map(get_associated_model_latest_mtrs_mapper, DEPLOYABLE_MODEL.get("associatedModels", [])))
    mtrs = list(filter(None, mtrs))
    result = {}
    result.update(combine_model_test_results(mtrs))
    result.update(extract_model_fields(execution_errors_array))

    try:
        results_with_defaults.update(result)
        LOG.info("Performing DMN evaluation")
        job = json.loads(JOB.get("rawJson", {}))
        evaluated_results = mlc_api.evaluate_results(results_with_defaults, "dashboard_model.dmn", additional_assets=job.get("additionalAssets", []))
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
    dashboard_result.update(results_with_defaults)
    dashboard_result.update(dashboard_result)
    dashboard_result.update(heat_map)
    dashboard_result.update(flat_heatmap)
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


def combine_model_test_results(mtrs) -> dict:
    result = {}
    mtrs.sort(key=lambda elem: parse(elem.get("createdDate")))
    for mtr in mtrs:
        if mtr is not None:
            result.update(mtr.get("testResults", {}))
    return result