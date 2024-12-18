# Custom models and forms
from .models import Pws, Source, PfasResult, FlowRate, ClaimSource, ClaimFlowRate, ClaimPfasResult
from .forms import MaxFlowRateUpdateForm, AnnualProductionForm, PfasResultUpdateForm, ContactForm

# Custom functions
from .utils.handler import handle_update
from .utils.tables_utils import add_pfoas_if_missing, get_max_other_threshold, get_latest_entries
from .utils.calculations import calc_ppt_result, calc_gpm_flow_rate

# Django functions
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import JsonResponse
from itertools import chain


class CustomLoginView(LoginView):
    template_name = 'login.html'
    success_url = reverse_lazy('dashboard')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')  # Redirect to the dashboard if the user is already logged in
        return super().dispatch(request, *args, **kwargs)

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else: 
        return redirect('login')

@login_required
def dashboard(request):
    # Retrieve the PWS associated with the logged-in user; otherwise, throw an error.
    pws_record = Pws.objects.get(form_userid=request.user.username)
    if not pws_record: 
        return redirect('some-error-page') 
    
    # Pull all the sources filed in the claims portal
    sources = Source.objects.filter(pwsid=pws_record.pwsid)
    
    context = {
        'pws': pws_record,
        'sources': sources,
    }

    return render(request, 'dashboard.html', context)


# The logic: 
    ## 1. Get relevant rows from the Claims table and any rows from the EHE table that have been updated by the user. See point 4 below. 
    ## 2. Combine the two tables, sort in decreasing order by result per analyte per source and keep only the max result per analyte per source. 
    ## 3a. For PFAS results show PFOA, PFOS, and max other analyte. 
    ## 3b. Max Flow Rate
    ## 3c. Annual Production
    ## 4. If the user updates any value, this is pushed to EHE tables where the updated_by_water_provider column is updated to True. 
    ## 5. Repeat the process from 1 to 4. 
# Note: steps 1 to 3 are processed in source_detail_view. The updates are processed in the relevant update functions below. 



@login_required
def source_detail_view(request, pwsid, source_name):
    claim_source = get_object_or_404(ClaimSource, pwsid=pwsid, source_name=source_name)

    #### PFAS Results ####
    # columns = ['pwsid', 'water_source_id', 'source_name', 'analyte', 'result_ppt', 'sampling_date', 'analysis_date', 'lab_sample_id', 'data_origin']
    claim_pfas_results = ClaimPfasResult.objects.filter(pwsid=claim_source.pwsid, source_name=source_name).exclude(analyte__isnull=True)
    updated_pfas_results = PfasResult.objects.filter(pwsid=claim_source.pwsid, source_name=source_name, updated_by_water_provider=True)
    latest_pfas_results = get_latest_entries(updated_pfas_results)
    # combined_pfas_results = get_combined_results(claim_pfas_results, latest_pfas_results, columns)
    
    combined_pfas_results = []
    for claim_result in claim_pfas_results:
        analyte = claim_result.analyte
        latest_result = next((res for res in latest_pfas_results if res.analyte == analyte), None)

        result = {
            'pwsid': claim_result.pwsid,
            'water_source_id': claim_result.water_source_id,
            'source_name': claim_result.source_name,
            'analyte': analyte,
            'lower_bound': claim_result.result_ppt,
            'result_ppt': latest_result.result_ppt if latest_result else claim_result.result_ppt,
            'sampling_date': latest_result.sampling_date if latest_result else claim_result.sampling_date,
            'analysis_date': latest_result.analysis_date if latest_result else claim_result.analysis_date,
            'lab_sample_id': latest_result.lab_sample_id if latest_result else claim_result.lab_sample_id,
            'data_origin': latest_result.data_origin if latest_result else claim_result.data_origin,
        }
        combined_pfas_results.append(result)
       
    # max_pfas_results = get_max_results_by_analyte(combined_pfas_results)
    pfas_results = add_pfoas_if_missing(combined_pfas_results, claim_source.pwsid, claim_source.water_source_id, claim_source.source_name)
    max_other_threshold = get_max_other_threshold(pfas_results)
    
    impacted = True if not claim_source.all_nds or updated_pfas_results else False

    #### Max Flow Rate and Annuals ####
    # columns_flow = ['pwsid', 'water_source_id', 'source_name', 'source_variable', 'year', 'flow_rate', 'unit', 'flow_rate_gpm', 'data_origin']
    claim_flow_rates = ClaimFlowRate.objects.filter(pwsid=claim_source.pwsid, source_name=source_name)
    updated_flow_rates = FlowRate.objects.filter(pwsid=claim_source.pwsid, source_name=source_name, updated_by_water_provider=True)
    latest_max_flow = get_latest_entries(updated_flow_rates, source_variable='VFR')
    latest_annuals = get_latest_entries(updated_flow_rates, source_variable='AFR')
    latest_flow_rates = list(chain(latest_max_flow, latest_annuals))

    years_to_process = list(range(2013, 2024)) + [None] # None for max flow rate 

    combined_flow_rates = []
    # Process each year once
    for year in years_to_process:
        latest_flow_rate = next((fr for fr in latest_flow_rates if fr.year == year), None)
        claim_flow_rate = next((cf for cf in claim_flow_rates if cf.year == year), None)
        
        # Lower bound from ClaimFlowRate
        lower_bound = claim_flow_rate.flow_rate_gpm if claim_flow_rate else 0

        # Append combined entry
        combined_flow_rates.append({
            'pwsid': claim_source.pwsid,
            'water_source_id': latest_flow_rate.water_source_id if latest_flow_rate else (claim_flow_rate.water_source_id if claim_flow_rate else None),
            'source_name': source_name,
            'year': year,
            'source_variable': latest_flow_rate.source_variable if latest_flow_rate else (claim_flow_rate.source_variable if claim_flow_rate else 'AFR'),
            'flow_rate': latest_flow_rate.flow_rate if latest_flow_rate else (claim_flow_rate.flow_rate if claim_flow_rate else 0),
            'unit': latest_flow_rate.unit if latest_flow_rate else (claim_flow_rate.unit if claim_flow_rate else 'GPY'),
            'flow_rate_gpm': latest_flow_rate.flow_rate_gpm if latest_flow_rate else (claim_flow_rate.flow_rate_gpm if claim_flow_rate else 0),
            'flow_rate_gpy': ((latest_flow_rate.flow_rate_gpm if latest_flow_rate else (claim_flow_rate.flow_rate_gpm if claim_flow_rate else 0)) * 1440 * 365),
            'flow_rate_mgd': ((latest_flow_rate.flow_rate_gpm if latest_flow_rate else (claim_flow_rate.flow_rate_gpm if claim_flow_rate else 0)) * 1440 / 1_000_000),
            'flow_rate_afpy': ((latest_flow_rate.flow_rate_gpm if latest_flow_rate else (claim_flow_rate.flow_rate_gpm if claim_flow_rate else 0)) * 1440 * 365 / 325851),
            'lower_bound': lower_bound,  # Always from ClaimFlowRate
            'data_origin': latest_flow_rate.data_origin if latest_flow_rate else ('Placeholder' if not claim_flow_rate else claim_flow_rate.data_origin),
        })
    
    max_flow_rate = next((fr for fr in combined_flow_rates if fr['year'] is None), None)
    annuals = [fr for fr in combined_flow_rates if fr['year'] is not None]

    # Prepare context for rendering
    context = {
        'claim_source': claim_source,
        'impacted': impacted,
        'max_flow_rate': max_flow_rate,
        'annuals': annuals,
        'pfas_results': pfas_results,
        'max_other_threshold': max_other_threshold
    }

    return render(request, 'source_detail.html', context)

@login_required
def update_pfas_result_view(request):
    def calc_pfas_fields(instance, cleaned_data):
        instance.result = float(cleaned_data['result'])
        instance.unit = cleaned_data['unit']
        instance.result_ppt = calc_ppt_result(instance.result, instance.unit)

    return handle_update(
        request,
        form_class=PfasResultUpdateForm,
        extra_fields={
            'analyte': 'analyte',
            'sampling_date': 'sampling_date',
            'analysis_date': 'analysis_date',
            'lab': 'lab',
            'analysis_method': 'analysis_method',
            'lab_sample_id': 'lab_sample_id', 
            'comments': 'comments'
        },
        calc_func=calc_pfas_fields,
        source_variable=None
    )

@login_required
def update_max_flow_rate_view(request):
    def calc_max_flow_rate_fields(instance, cleaned_data):
        instance.flow_rate = cleaned_data['flow_rate']
        instance.unit = cleaned_data['unit']
        instance.flow_rate_gpm = calc_gpm_flow_rate(instance.flow_rate, instance.unit)

    return handle_update(
        request,
        form_class=MaxFlowRateUpdateForm,
        extra_fields={
            'comments': 'comments'
        },
        calc_func=calc_max_flow_rate_fields,
        source_variable='VFR'
    )

@login_required
def update_annual_production_view(request):
    def calc_annual_production_fields(instance, cleaned_data):
        instance.flow_rate = cleaned_data['flow_rate']
        instance.unit = cleaned_data['unit']
        instance.flow_rate_gpm = calc_gpm_flow_rate(instance.flow_rate, instance.unit)
        instance.year = cleaned_data['year']
        print(instance)
    return handle_update(
        request,
        form_class=AnnualProductionForm,
        extra_fields={
            'flow_rate_reduced': 'flow_rate_reduced',
            'comments': 'comments'
        },
        calc_func=calc_annual_production_fields,
        source_variable='AFR'
    )

@login_required
def contact_view(request):
    pwsid = request.user.username
    recipients = settings.EMAIL_RECIPIENTS
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            full_message = f"From: {name}\n\n{message}"

            email_message = EmailMessage(
                subject=f"{subject} (from {pwsid})",
                body=full_message,
                from_email=settings.EMAIL_HOST_USER,  
                to=recipients,
                reply_to=[email], 
            )
            email_message.send(fail_silently=False)

            # Return a JSON response for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'message': 'Email sent successfully.'})

            return render(request, 'dashboard.html')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Invalid form submission'}, status=400)
        
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})



@login_required
def activity_view(request):
    pwsid = request.user.username

    pfas_results = PfasResult.objects.filter(pwsid=pwsid).values(
        'submit_date', 'source_name', 'analyte', 'result_ppt'
    )

    # Format PFAS log entries
    pfas_logs = [
        {
            'date': result['submit_date'].strftime('%Y-%m-%d'),
            'source_name': result['source_name'],
            'table_name': 'PFAS Result',
            'change': f"{result['analyte']} value changed to {result['result_ppt']} ng/L",
        }
        for result in pfas_results
    ]

    # Retrieve flow rate changes
    flow_rates = FlowRate.objects.filter(pwsid=pwsid).values(
        'submit_date', 'source_name', 'source_variable', 'flow_rate', 'unit'
    )

    # Format flow rate log entries
    flow_logs = [
    {
        'date': flow['submit_date'].strftime('%Y-%m-%d'),
        'source_name': flow['source_name'],
        'table_name': 'Flow Rate',
        'source_variable': flow['source_variable'],  # Keep the original value for logic
        'change': f"{'Annual Production' if flow['source_variable'] == 'AFR' else 'Max Flow Rate'} changed to {flow['flow_rate']} {flow['unit']}",
    }
        for flow in flow_rates
    ]

    # Combine and sort logs
    activity_logs = sorted(chain(pfas_logs, flow_logs), key=lambda x: x['date'], reverse=True)

    # Pass logs to template
    return render(request, 'activity.html', {'activity_logs': activity_logs})