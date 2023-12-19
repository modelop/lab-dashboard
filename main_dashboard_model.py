import json
from datetime import datetime

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


from pathlib import Path
import numpy as np
import pandas as pd

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
def metrics(baseline) -> dict:
    dashboard_result = {
        "createdDate": datetime.now().strftime('%m/%d/%Y %H:%M:%S'),
        "modelUseCategory": "INSURANCE",
        "modelOrganization": "Claims Processing",
    }
    summary_results = '''
    {
    "summary results":"this is a summary result"
    }  
    '''
    custom_cards = '''
    {
      "customCards": [
        {
          "name":"# of Models",
          "value":"1"
        }, {
          "name":"# of Reports",
          "value":"1"
        }, {
          "name":"# of Pending Reports",
          "value":"1"
        }
      ]
    }  
    '''
    custom_cols = '''
    {
      "customColumns": [
        {
          "name": "Reporting Quarter",
          "value": "FY23 Q2"
        },
        {
          "name":"Overall Rating",
          "value":"Use Caution"
        }
      ]
    }  
    '''
    heatmap = '''
    {
      "heatMap": {
        "Overall Assessment": {
          "testResult": "Green"
        },
        "Primary Metric 1": {
          "testResult": "Green"
        },
        "Primary Metric 2": {
          "testResult": "Green"
        },
        "Primary Metric 3": {
          "testResult": "Green"
        },
        "Primary Metric 4": {
          "testResult": "Green"
        },
        "Primary Metric 5": {
          "testResult": "Green"
        }
      }
    }
    '''
    flat_heatmap = '''
    {
    "summary results":"this is a summary result"
    }  
    '''
    dashboard_result.update(json.loads(summary_results))
    dashboard_result.update(json.loads(custom_cards))
    dashboard_result.update(json.loads(custom_cols))
    dashboard_result.update(json.loads(heatmap))
    dashboard_result.update(json.loads(flat_heatmap))
    yield dashboard_result
