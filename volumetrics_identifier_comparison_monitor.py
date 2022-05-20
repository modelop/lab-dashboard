import modelop_sdk.utils.logging as logger
from modelop.ootb_monitors.volumetrics_identifier_comparison import volumetrics_identifier_comparison
from modelop_sdk.utils import dashboard_utils as dashboard_utils


def calculate_volumetrics_identifier_comparison(baseline, comparator, init_param,
                                                remove_breakdown: bool = False) -> dict:
    """
    Source : https://github.com/modelop/moc_monitors/tree/main/src/modelop/ootb_monitors/volumetrics_identifier_comparison

    Evaluation Metrics (Source:https://modelop.atlassian.net/wiki/spaces/~355140182/pages/2286944283/Dashboard+3.0+monitors):
        identifiers_match
    ---- Heatmap criteria
        identifiers_match = true → GREEN
        identifiers_match = false → RED
        identifiers_match is NULL or Monitor error → GRAY
    """
    LOG = logger.configure_logger()

    dashboard_utils.assert_df_not_none_and_not_empty(baseline, "Required baseline")
    dashboard_utils.assert_df_not_none_and_not_empty(comparator, "Required comparator")

    volumetrics_identifier_comparison.init(init_param)

    monitor_results = volumetrics_identifier_comparison.metrics(baseline, comparator)
    for result in monitor_results:
        vol_id_comp_results = result

    LOG.debug(f"Removing breakout details is {remove_breakdown}")

    if remove_breakdown:
        LOG.debug("Removing breakout details")
        vol_id_comp_results = remove_breakdown_details(vol_id_comp_results)

    return vol_id_comp_results


def remove_breakdown_details(volumetrics_results):
    """
    Method that removes the breakdown sections of the volumetrics results, because they are too verbose
    """
    volumetrics_array = volumetrics_results["volumetrics"]
    for volumetric_entry in volumetrics_array:
        values_content = volumetric_entry["values"]
        for key, value in values_content.items():
            if key.startswith("dataframe_"):
                dataframe_entry = values_content[key]
                if dataframe_entry.get("extra_identifiers") is not None:
                    extra_identifiers = dataframe_entry.get("extra_identifiers")
                    if extra_identifiers.get("breakdown") is not None:
                        extra_identifiers["breakdown"] = {}

    return volumetrics_results
