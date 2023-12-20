import json
import re
from datetime import datetime
from typing import List, Optional, Dict
import random
import modelop.schema.infer as infer
import modelop.utils as utils
import modelop_sdk.apis.mlc_api as mlc
import modelop_sdk.restclient.moc_client as moc_client
import modelop_sdk.utils.logging as logger
from modelop_sdk.utils import dashboard_utils, dict_utils
import modelop_sdk.apis.model_manage_api as model_manage
import uuid
from dateutil.parser import parse
from pathlib import Path
import pandas as pd

LOG = logger.configure_logger()
RATING = ""
QUARTER = ""

heatMapColors = ["Gray", "Yellow", "Green", "Green", "Green", "Green", "Red"]
aryOrgs = ["Insurance","Residuals","Credit","Fraud","AML","Insider Threats","Marketing","Trade Analytics","Capital Markets","Asset Management","Payments","Lockbox OCR"]
aryRatings = ["Use Caution","Not performing","As Expected","As Expected"]
aryQuarter = ["FY23 Q1","FY23 Q2","FY23 Q3","FY23 Q4"]
def generate_heatmap_color() -> str:
    global RATING
    if RATING == "As Expected":
        return "Green"
    else:
        return heatMapColors[random.randint(0, len(heatMapColors) - 1)]
def generate_org() -> str:
    return aryOrgs[random.randint(0,len(aryOrgs) - 1)]
def generate_rating() -> str:
    global RATING
    RATING = aryRatings[random.randint(0,len(aryRatings) - 1)]
    return RATING
def generate_quarter() -> str:
    global QUARTER
    QUARTER = aryQuarter[random.randint(0,len(aryQuarter) - 1)]
    return QUARTER
def generate_category() -> str:
    return ""

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
    global RATING
    global QUARTER

    dashboard_result = {
        "createdDate": datetime.now().strftime('%m/%d/%Y %H:%M:%S'),
    }

    primary_metrics = {
        "Primary Metrics": [
            {"":1,"Metric": "Outcome 1", "Value": "False"},
            {"":2,"Metric": "Outcome 2", "Value": "True"},
            {"":3,"Metric": "Outcome 3", "Value": "0.284"},
            {"":4,"Metric": "Data 1", "Value": "True"},
            {"":5,"Metric": "Data 2", "Value": "True"}
        ]
    }

    custom_cards = '''
    {
      "customCards": [
        {
          "name":"# of Models",
          "value": 1
        }, {
          "name":"# of Reports",
          "value": 1
        }
      ]
    }  
    '''
    custom_cols = {
      "customColumns": [
        {
          "name": "Reporting Quarter",
          "value": generate_quarter()
        },
        {
          "name": "Overall Rating",
          "value": generate_rating()
        }
      ]
    }  
    
    heatmap = {
      "heatMap": {
        "Overall Assessment": {
          "testResult": generate_heatmap_color()
        },
        "Primary Metric 1": {
          "testResult": generate_heatmap_color()
        },
        "Primary Metric 2": {
          "testResult": generate_heatmap_color()
        },
        "Primary Metric 3": {
          "testResult": generate_heatmap_color()
        },
        "Primary Metric 4": {
          "testResult": generate_heatmap_color()
        },
        "Primary Metric 5": {
          "testResult": generate_heatmap_color()
        }
      }
    }
    flat_heatmap = '''
    {
    }  
    '''
    dashboard_result.update(primary_metrics)
    dashboard_result.update(json.loads(custom_cards))
    dashboard_result.update(custom_cols)
    dashboard_result.update(heatmap)

    summary_results = {
        "Model Organization": generate_org(),
        "Last Report Quarter": QUARTER,
        "Last Report Rating": RATING,
        "Last Report": "https://mocaasin.modelop.center/#/models/business-models/snapshot/ee2542c4-8b49-40f9-b80a-21ab09e70781/monitoring/tests/97c835e8-b2b6-42e5-96b1-939460b449fc"
    }

    dashboard_result.update(summary_results)
    dashboard_result.update(json.loads(flat_heatmap))
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


def calculate_risk_count():
    risk = DEPLOYABLE_MODEL.get("storedModel", {}).get("modelMetaData", {}).get("modelRisk", "0")
    try:
        int(risk[-1])
    except:
        risk = "0"
    t1 = 1 <= int(risk[-1]) <= 3
    t4 = 4 <= int(risk[-1]) <= 5
    return {"risk_1_2_3": 1 if t1 else 0, "risk_4_5": 1 if t4 else 0}


class ValueEntry(Dict):
    def __init__(self, key: str, value, color: str = None):
        super().__init__()
        if color is not None:
            self.update({"key": key, "value": value, "color": color})
        else:
            self.update({"key": key, "value": value})


class CustomCard(Dict):
    def __init__(self, value: List[ValueEntry], name: str = "Custom Card"):
        super().__init__()
        self.update({"name": name, "value": value})


class preformatted(str):
    def __init__(self, val):
        super().__init__()


def generate_custom_entry(value_list,
                          sub_column_list: Optional[List[str]] = None,
                          color_list: Optional[List[str]] = None,
                          name: Optional[str] = "CustomCard") -> CustomCard:
    entries = []
    for i in range(len(value_list)):
        if type(value_list[i]) is preformatted:
            val = value_list[i]
        else:
            val = parse_number(value_list[i])
        color = None
        if color_list is not None:
            color = color_list[i]
        entries.append(ValueEntry(sub_column_list[i], val, color))
    return CustomCard(entries, name=name)


def calculate_custom_cards(cards: List[CustomCard]):
    return {"customCards": cards}


def calculate_custom_columns(columns: List[CustomCard]):
    return {"customColumns": columns}


def parse_number(value):
    if value is None:
        return "N/A"
    return float(re.sub(r'[^\w.]', '', str(value)))

#
# This main method is utilized to simulate what the engine will do when calling the above metrics function.  It takes
# the json formatted data, and converts it to a pandas dataframe, then passes this into the metrics function for
# processing.  This is a good way to develop your models to be conformant with the engine in that you can run this
# locally first and ensure the python is behaving correctly before deploying on a ModelOp engine.
#
def main():
    raw_json = Path('example_job.json').read_text()
    init_param = {'rawJson': raw_json}

    init(init_param)
    df1 = pd.read_csv("example_data.csv")
    df2 = pd.read_csv("example_data.csv")
    print(json.dumps(next(metrics(df1, df2)), indent=2))


if __name__ == '__main__':
    main()