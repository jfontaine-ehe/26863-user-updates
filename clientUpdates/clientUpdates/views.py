from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from .models import Pws, Source, FlowRate, PfasResult
from .forms import MaxFlowRateUpdateForm, AnnualProductionForm, PfasResultUpdateForm
import logging

logger = logging.getLogger('clientUpdates')
class CustomLoginView(LoginView):
    template_name = 'login.html'
    success_url = reverse_lazy('dashboard')

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else: 
        return redirect('login')

@login_required
def dashboard(request):
    # Retrieve the PWS associated with the logged-in user
    pws_record = Pws.objects.get(form_userid=request.user.username)

    if not pws_record: 
        return redirect('some-error-page') 
    
    sources = Source.objects.filter(pwsid=pws_record.pwsid, file_source=True)
    
    # source_names = sources.values_list('source_name', flat=True)
    # max_flow_rates = FlowRate.objects.filter(pwsid=pws_record.pwsid, source_name__in=source_names, source_variable='VFR')
    # annuals = FlowRate.objects.filter(pwsid=pws_record.pwsid, source_name__in=source_names, source_variable='AFR')
    # pfas_results = PfasResult.objects.filter(pwsid=pws_record.pwsid, source_name__in=source_names)

    context = {
        'pws': pws_record,
        'sources': sources,
        # 'max_flow_rates': max_flow_rates,
        # 'annuals': annuals,
        # 'pfas_results': pfas_results,
    }

    return render(request, 'dashboard.html', context)

def get_analyte_result(pfas_results, analyte):
    if analyte in ['PFOA', 'PFOS']:
        try:
            result = pfas_results.get(analyte=analyte).result_ppt
            result = result if result else 0
        except PfasResult.DoesNotExist:
            result = 0
        return analyte, result
    elif analyte == 'max_other':
        # Get the maximum of all analytes except PFOA and PFOS
        max_other_row = pfas_results \
            .exclude(analyte__in=['PFOA', 'PFOS']) \
            .exclude(result_ppt__isnull = True) \
            .order_by('-result_ppt') \
            .first()
        
        return (max_other_row.analyte, max_other_row.result_ppt) if max_other_row else (None, 0)

@login_required
def source_detail_view(request, pwsid, source_name): 
    source = get_object_or_404(Source, pwsid=pwsid, source_name=source_name)
    max_flow_rate = FlowRate.objects.filter(pwsid=source.pwsid, source_name=source_name, source_variable='VFR').first() # there should only be one max flow rate per source
    annuals = FlowRate.objects.filter(pwsid=source.pwsid, source_name=source_name, source_variable='AFR')
    pfas_results = PfasResult.objects.filter(pwsid=source.pwsid, source_name=source_name)
    
    _, pfoa_result = get_analyte_result(pfas_results, 'PFOA')
    _, pfos_result = get_analyte_result(pfas_results, 'PFOS')
    max_other_analyte, max_other_result = get_analyte_result(pfas_results, 'max_other')
    
    max_other_threshold = round((pfoa_result + pfos_result) ** 2, 1)
    
    if max_other_result > max_other_threshold:
        pfas_results_to_show = pfas_results.filter(analyte__in=['PFOA', 'PFOS', max_other_analyte])
    else:
        pfas_results_to_show = pfas_results.filter(analyte__in=['PFOA', 'PFOS'])

    # Check if a 2023 entry exists for this source, otherwise create a placeholder
    annual_2023 = FlowRate.objects.filter(pwsid=pwsid, source_name=source_name, year=2023).first()

    # if not annual_2023:
    #     # Create a placeholder for 2023 if data doesn't exist
    #     annual_2023 = {'flow_rate': 'None provided', 'unit': ''}

    context = {
        'source': source,
        'max_flow_rate': max_flow_rate,
        'annuals': annuals,
        'annual_2023': annual_2023, 
        'pfas_results_to_show': pfas_results_to_show, 
        'max_other_threshold': max_other_threshold
    }

    return render(request, 'source_detail.html', context)

def calc_gpm_flow_rate(flow_rate, unit):
    if unit == 'mgd':
        flow_rate_gpm = flow_rate * 1e6 / 1440
    elif unit == 'gpm':
        flow_rate_gpm = flow_rate
    elif unit == 'gpy':
        flow_rate_gpm = flow_rate * 1e6 / (365 * 1440)
    elif unit == 'afpy':
        flow_rate_gpm = flow_rate * 325851 / (365 * 1440)
    else:
        raise ValueError(f"Unsupported unit '{unit}' provided.")
    
    return flow_rate_gpm

@login_required
def update_max_flow_rate_view(request, row_names):
    max_flow_rate = get_object_or_404(FlowRate, row_names=row_names)
    
    if request.method == 'POST':
        form = MaxFlowRateUpdateForm(request.POST)
        if form.is_valid():
            new_unit = form.cleaned_data['unit']
            new_flow_rate = form.cleaned_data['flow_rate']
            flow_rate_gpm = calc_gpm_flow_rate(new_flow_rate, new_unit)

            # Print/log the updates instead of saving during development phase
            logger.info(f"Updating flow_rate_gpm for row {row_names}:")
            logger.info(f"Old flow rate: {max_flow_rate.flow_rate} {max_flow_rate.unit}, New flow rate: {new_flow_rate} {new_unit}")

            max_flow_rate.flow_rate = new_flow_rate
            max_flow_rate.unit = new_unit
            max_flow_rate.flow_rate_gpm = flow_rate_gpm
            # max_flow_rate.save()
            messages.success(request, f"Max flow rate updated successfully.")
            return redirect('source-detail', pwsid=max_flow_rate.pwsid, source_name=max_flow_rate.source_name)
    else:
        form = MaxFlowRateUpdateForm(instance=max_flow_rate)

    return redirect('source-detail', pwsid=max_flow_rate.pwsid, source_name=max_flow_rate.source_name)


@login_required
def add_update_annual_production_view(request):
    if request.method == 'POST':
        pwsid = request.POST.get('pwsid')
        source_name = request.POST.get('source_name')
        form = AnnualProductionForm(request.POST)
        
        if form.is_valid():
            logger.debug(f"Received form data: {form.cleaned_data}")
            
            year = form.cleaned_data['year'] # should just be 2023 for now
            new_flow_rate = form.cleaned_data['flow_rate']
            new_unit = form.cleaned_data['unit']
            flow_rate_gpm = calc_gpm_flow_rate(new_flow_rate, new_unit)

            logger.debug(f"Calculated flow rate in GPM: {flow_rate_gpm}")

            # Check if 2023 data already exists
            # can be modified if we want the ability to update other years. 
            annual_2023 = FlowRate.objects.filter(pwsid=pwsid, source_name=source_name, source_variable='AFR', year=year).first()

            if annual_2023:
                # Update existing 2023 entry
                logger.info(f"Updating existing 2023 production data for source {source_name}.")
                annual_2023.flow_rate = new_flow_rate
                annual_2023.unit = new_unit
                annual_2023.flow_rate_gpm = flow_rate_gpm
                logger.info(f"Old flow_rate_gpm: {annual_2023.flow_rate_gpm}, New calculated flow_rate_gpm: {flow_rate_gpm}")
                logger.info(f"Preparing to update annual production record for PWSID: {pwsid}, Source: {source_name}, Year: {year}")
            else:
                # Add a new row for 2023
                logger.info(f"Adding new 2023 production data of {flow_rate_gpm} for source {source_name}.")
                annual_2023 = FlowRate(
                    pwsid=pwsid,
                    submit_date = timezone.now(),
                    source_name=source_name,
                    sample_id=source_name,
                    source_variable='AFR',
                    year=year,
                    flow_rate=new_flow_rate,
                    flow_rate_gpm=flow_rate_gpm,
                    unit=new_unit,
                )
                logger.info(f"Preparing to add new annual production record for PWSID: {pwsid}, Source: {source_name}, Year: {year}")
            
            annual_2023.save()
            messages.success(request, f"Annual production for ", {year}, " added/updated successfully.")
            return redirect('source-detail', pwsid=pwsid, source_name=source_name)
        else:
            # Log form errors if form validation fails
            logger.error(f"Form validation failed with errors: {form.errors}")
    else:
        form = AnnualProductionForm
    
    logger.debug(f"Rendering the form for Annual Production input")
    messages.error(request, "Invalid request.")
    return redirect('source-detail', pwsid=pwsid, source_name=source_name)

def calc_ppt_result(result, unit):
    if unit == 'ppt':
        result_ppt = result 
    elif unit == 'ppb':
        result_ppt = result * 1e3
    elif unit == 'ppm':
        result_ppt = result * 1e6
    else:
        raise ValueError(f"Unsupported unit '{unit}' provided.")

    return result_ppt

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import logging

logger = logging.getLogger(__name__)

@login_required
def update_pfas_result_view(request, row_names):
    # Fetch the existing PFAS result or return a 404 if not found
    pfas_result = get_object_or_404(PfasResult, row_names=row_names)

    logger.debug("Fetched PFAS result with row_names: %d", pfas_result.row_names)

    if request.method == 'POST':
        form = PfasResultUpdateForm(request.POST, instance=pfas_result)

        if form.is_valid():
            logger.debug("Received valid form data: %s", form.cleaned_data)

            # Calculate result in ppt based on unit and value provided
            result_ppt = calc_ppt_result(form.cleaned_data['result'], form.cleaned_data['unit'])
            logger.debug("Calculated result in ppt: %s", result_ppt)

            # Save form instance without committing immediately
            # pfas_result = form.save(commit=False)
            # pfas_result.result_ppt = result_ppt
            # pfas_result.save()

            logger.info("Added or updated %s result of %s ppt for %s.", form.cleaned_data['analyte'], result_ppt, pfas_result.source_name)
            messages.success(request, 'PFAS result updated successfully.')

            return redirect('source-detail', pwsid=pfas_result.pwsid, source_name=pfas_result.source_name)
        else:
            logger.error("Form validation failed with errors: %s", form.errors)
            messages.error(request, "Form validation failed. Please correct the errors below.")
            return redirect('source-detail', pwsid=pfas_result.pwsid, source_name=pfas_result.source_name)

    # Handle GET request to render form with existing data
    form = PfasResultUpdateForm(instance=pfas_result)
    logger.debug("Rendering the form for PFAS result input")
    return render(request, 'update_pfas_result_modal.html', {'form': form, 'pfas_result': pfas_result})