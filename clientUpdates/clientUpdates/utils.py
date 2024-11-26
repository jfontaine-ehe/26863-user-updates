import os

import dropbox
import logging
from itertools import chain
from collections import defaultdict
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect

logger = logging.getLogger('clientUpdates')

def handle_update(request, form_class, extra_fields, calc_func=None, source_variable=None):
    """
    Handles common update logic for PFAS results, max flow rate, and annual production.
    """
    if request.method == 'POST':
        pwsid = request.POST.get('pwsid')
        source_name = request.POST.get('source_name')
        form = form_class(request.POST, request.FILES)

        if form.is_valid():
            logger.debug("Received valid form data: %s", form.cleaned_data)

            # Save form instance without committing immediately
            instance = form.save(commit=False)

            # Add shared fields
            instance.pwsid = pwsid
            instance.source_name = source_name
            instance.submit_date = timezone.now()
            instance.filename = form.cleaned_data.get('filename').name
            instance.data_origin = "EHE Update Portal"
            instance.updated_by_water_provider = True

            # Add extra fields
            for field, value in extra_fields.items():
                setattr(instance, field, form.cleaned_data.get(value, value))

            # Calculate additional fields if calc_func is provided
            if calc_func:
                calc_func(instance, form.cleaned_data)

            # Add source variable if provided
            if source_variable:
                instance.source_variable = source_variable

            try:
                # TODO: Joe, please ensure this works for PFAS results, max flow rate, and annual production updates. 
                instance.save()
            except Exception as e:
                logger.error("Error saving instance: %s", e)
                messages.error(request, "Failed to save updates due to a system error.")
                return redirect('source-detail', pwsid=pwsid, source_name=source_name)
            
            logger.info(f"{source_variable} updated successfully for {source_name}.")
            messages.success(request, f"{source_variable} updated successfully.")

            # Upload file to Dropbox
            # TODO: Joe, please ensure that this works.
            file = request.FILES.get('filename')
            filetype = 'Flow Rate' if source_variable else 'PFAS Results'
            if file:
                upload_to_dropbox(file, filetype, pwsid)

            return redirect('source-detail', pwsid=pwsid, source_name=source_name)

        else:
            logger.error("Form validation failed with errors: %s", form.errors)
            messages.error(request, "Form validation failed. Please correct the errors below.")
            return redirect('source-detail', pwsid=pwsid, source_name=source_name)

    messages.error(request, "Invalid request.")
    return redirect('source-detail', pwsid=request.POST.get('pwsid'), source_name=request.POST.get('source_name'))



def calc_ppt_result(result, unit):
    """ Returns results after converting from ppm, ppb, or ppt to ppt. """
    if unit == 'ppt':
        result_ppt = result 
    elif unit == 'ppb':
        result_ppt = result * 1e3
    elif unit == 'ppm':
        result_ppt = result * 1e6
    else:
        raise ValueError(f"Unsupported unit '{unit}' provided.")

    return result_ppt

def calc_gpm_flow_rate(flow_rate, unit):
    """ Returns flow rate after converting form MGD, MGY, GPM, GPY, or AFPY to GPM. """
    if unit == 'mgd':
        flow_rate_gpm = flow_rate * 1e6 / 1440
    elif unit == 'gpm':
        flow_rate_gpm = flow_rate
    elif unit == 'gpy':
        flow_rate_gpm = flow_rate / (365 * 1440)
    elif unit == 'mgy':
        flow_rate_gpm = flow_rate * 1e6 / (365 * 1440)
    elif unit == 'afpy':
        flow_rate_gpm = flow_rate * 325851 / (365 * 1440)
    else:
        raise ValueError(f"Unsupported unit '{unit}' provided.")
    
    return flow_rate_gpm


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
    """ Finds the the threshold result for the maximum another analyte. """
    pfoa_result = next((result['result_ppt'] for result in pfas_results if result['analyte'] == 'PFOA'), 0)
    pfos_result = next((result['result_ppt'] for result in pfas_results if result['analyte'] == 'PFOS'), 0)
    return round((pfoa_result + pfos_result) ** 2, 1)

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


def upload_to_dropbox(file, filetype, pwsid):
    """
    Upload a file to Dropbox under the specified folder.
    
    Args:
        file: The uploaded file object.
        pwsid: A unique identifier for the folder in Dropbox.
    
    Returns:
        JsonResponse: A response indicating success or failure.
    """
    if not file:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    
    dropbox_access_token = settings.DROPBOX_OAUTH2_TOKEN
    if not dropbox_access_token:
        return print("no token")
        #return JsonResponse({'error': 'Dropbox access token not configured'}, status=500)
    
    try:
        # Initialize Dropbox client
        dbx = dropbox.Dropbox(oauth2_access_token=dropbox_access_token, oauth2_refresh_token= settings.DROPBOX_OAUTH2_REFRESH_TOKEN,
                              app_key = settings.DROPBOX_APP_KEY, app_secret= settings.DROPBOX_APP_SECRET)
        
        # Define the folder and file paths in Dropbox
        folder_path = f"/{filetype}/{pwsid}"
        dropbox_file_path = f"{folder_path}/{file.name}"
        
        # Ensure the folder exists
        try:
            dbx.files_get_metadata(folder_path)
        except dropbox.exceptions.ApiError as e:
            if isinstance(e.error, dropbox.files.GetMetadataError):
                dbx.files_create_folder_v2(folder_path)
        
        # Upload the file
        dbx.files_upload(file.read(), dropbox_file_path, mode=dropbox.files.WriteMode.overwrite)
        
        # Return success response
        return JsonResponse({'success': 'File uploaded to Dropbox successfully', 'path': dropbox_file_path})

    except dropbox.exceptions.AuthError as e:
        return JsonResponse({'error': 'Invalid Dropbox access token'}, status=401)
    except dropbox.exceptions.ApiError as e:
        return JsonResponse({'error': f'Dropbox API error: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)

