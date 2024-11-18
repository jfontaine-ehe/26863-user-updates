from itertools import chain
from collections import defaultdict
from django.core.files.storage import default_storage
from django.http import JsonResponse
import dropbox
from django.conf import settings

def get_max_entry(entries, key):
    """ Returns the entry with the maximum value for the given key. """
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

def get_max_other_threshold(pfas_results):
    """ Finds the the threshold result for the maximum another analyte. """
    pfoa_result = next((result['result_ppt'] for result in pfas_results if result['analyte'] == 'PFOA'), 0)
    pfos_result = next((result['result_ppt'] for result in pfas_results if result['analyte'] == 'PFOS'), 0)
    return round((pfoa_result + pfos_result) ** 2, 1)
    
def get_max_annuals_by_year(combined_annuals):
    """ Finds the maximum annual production by year from a combined list of records. """
    max_annuals_by_year = defaultdict(lambda: None)
    for record in combined_annuals:
        year = record['year']
        if max_annuals_by_year[year] is None or record['flow_rate_gpm'] > max_annuals_by_year[year]['flow_rate_gpm']:
            max_annuals_by_year[year] = record
    return list(max_annuals_by_year.values())



def upload_to_dropbox(file, pwsid):
    if not file: 
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    # Save file to temporary location on server
    file_path = default_storage.save(f'temp/{file.name}', file)
    
    # Dropbox Access Token (OAuth2 token, not refresh token)
    dropbox_access_token = settings.DROPBOX_OAUTH2_TOKEN
    
    # Upload to Dropbox
    try:
        dbx = dropbox.Dropbox(dropbox_access_token)
        
        # Check if the folder exists or create it
        folder_path = f"/PFAS results/{pwsid}"
        try:
            dbx.files_get_metadata(folder_path)
        except dropbox.exceptions.ApiError as e:
            if isinstance(e.error, dropbox.files.GetMetadataError):
                dbx.files_create_folder_v2(folder_path)

        # Upload the file
        with default_storage.open(file_path, 'rb') as f:
            dropbox_file_path = f"{folder_path}/{file.name}"
            dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode.overwrite)

        return JsonResponse({'success': 'File uploaded to Dropbox successfully'})

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
