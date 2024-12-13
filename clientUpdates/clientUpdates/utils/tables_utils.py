from collections import defaultdict
from django.db.models import OuterRef, Subquery
from itertools import chain



def get_max_results_by_analyte(combined_pfas_results):
    """ Finds the maximum result per analyte from a combined list of records. """
    max_results_by_analyte = defaultdict(lambda: None)
    for record in combined_pfas_results:
        analyte = record['analyte']
        if max_results_by_analyte[analyte] is None or record['result_ppt'] > max_results_by_analyte[analyte]['result_ppt']:
            max_results_by_analyte[analyte] = record
    return list(max_results_by_analyte.values())



def add_pfoas_if_missing(pfas_results, pwsid, water_source_id, source_name):
    """ Add PFOA and PFOS if they are not in the list. """
    analytes_to_include = ['PFOA', 'PFOS']
    for analyte in analytes_to_include:
        if not any(result['analyte'] == analyte for result in pfas_results):
            pfas_results.append({
                'pwsid': pwsid,
                'water_source_id': water_source_id,
                'source_name': source_name,
                'analyte': analyte,
                'result_ppt': 0,
                'sampling_date': None,
                'analysis_date': None,
                'lab_sample_id': None,
                'data_origin': 'N/A'
            })
    return pfas_results



def get_max_other_threshold(pfas_results):
    """ Finds the threshold result for the maximum another analyte. """
    pfoa_result = next((result['result_ppt'] for result in pfas_results if result['analyte'] == 'PFOA'), 0)
    pfos_result = next((result['result_ppt'] for result in pfas_results if result['analyte'] == 'PFOS'), 0)
    return round((pfoa_result + pfos_result) ** 2, 1)



def get_max_entry(entries, key):
    """ Returns the entry with the maximum value for the given key. """
    if not entries:
        return None
    return max(entries, key=lambda x: x[key], default=None)



def get_combined_results(queryset_1, queryset_2, columns):
    """ Combines two querysets by selecting only the specified columns. """
    results_1 = list(queryset_1.values(*columns))
    results_2 = list(queryset_2.values(*columns))
    return list(chain(results_1, results_2))



def get_latest_entries(queryset, source_variable=None):
    """
    Returns the latest entry from EH&E PFAS results or Flow Rate table.
    Handles `source_variable` conditions for AFR and VFR specifically.

    Arguments:
        queryset: The queryset to filter.
        source_variable: Specifies whether to process 'AFR', 'VFR', or other cases.

    Returns:
        A queryset containing the latest entries based on the specified conditions.
    """
    if source_variable == 'AFR':
        # Get the latest entries for each year where source_variable is 'AFR'
        latest_annuals = queryset.filter(source_variable='AFR', year=OuterRef('year')).order_by('-submit_date')
        return queryset.filter(row_names__in=Subquery(latest_annuals.values('row_names')[:1]))
    elif source_variable == 'VFR':
        # Get the single latest entry for source_variable 'VFR'
        return queryset.filter(source_variable='VFR').order_by('-submit_date')[:1]
    else:
        # Handle PFAS results, getting the latest entry per analyte
        latest_pfas_results = queryset.filter(analyte=OuterRef('analyte')).order_by('-submit_date')
        return queryset.filter(row_names__in=Subquery(latest_pfas_results.values('row_names')[:1]))



def get_filtered_annuals(combined_annuals, all_nds):
    """
    Filters annual production records based on source.all_nds value.
    - If `all_nds` is True, include all years from 2013 to 2022.
    - If `all_nds` is False, include non-zero years from 2013 to 2022.
    - Always include year 2023 for adding or updating.
    - If impacted sources have less than 3 non-zero years, add the highest year(s) with zero production to ensure 3 years are shown.
    """
    filtered_annuals = []
    non_zero_years = []
    zero_years = []

    for record in combined_annuals:
        year = record['year']
        flow_rate = record['flow_rate']

        if year == 2023:
            # Always include 2023 for adding or updating
            filtered_annuals.append(record)
        elif all_nds:
            # For unimpacted sources, include all years from 2013 to 2022
            if 2013 <= year <= 2022:
                filtered_annuals.append(record)
        elif not all_nds:
            # For impacted sources, separate non-zero and zero flow rate years
            if 2013 <= year <= 2022:
                if flow_rate > 0:
                    non_zero_years.append(record)
                else:
                    zero_years.append(record)

    # For impacted sources, ensure at least 3 years are shown
    if not all_nds:
        filtered_annuals.extend(non_zero_years)
        if len(non_zero_years) < 3:
            zero_years_sorted = sorted(zero_years, key=lambda x: x['year'], reverse=True)
            filtered_annuals.extend(zero_years_sorted[:3 - len(non_zero_years)])

    # Check if 2023 entry exists; if not, create a placeholder for 2023
    if not any(record['year'] == 2023 for record in filtered_annuals):
        filtered_annuals.append({
            'year': 2023,
            'flow_rate': 0,
            'unit': 'GPY',
            'data_origin': 'EHE portal',  
            'updated_by_water_provider': True  
        })

    # Sort filtered annuals by year in increasing order
    filtered_annuals = sorted(filtered_annuals, key=lambda x: x['year'])

    return filtered_annuals



def get_max_annuals_by_year(combined_annuals):
    """ Finds the maximum annual production by year from a combined list of records. """
    max_annuals_by_year = defaultdict(lambda: None)
    for record in combined_annuals:
        year = record['year']
        if max_annuals_by_year[year] is None or record['flow_rate_gpm'] > max_annuals_by_year[year]['flow_rate_gpm']:
            max_annuals_by_year[year] = record
    return list(max_annuals_by_year.values())