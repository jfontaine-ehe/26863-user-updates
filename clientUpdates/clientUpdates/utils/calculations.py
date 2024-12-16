import math

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



def calc_pfas_score_and_method(pfoa_result, pfos_result, max_other_result):
    """
    Calculate the PFAS score based on PFOA, PFOS, and the highest other analyte result.

    The PFAS score is calculated as:
    - Default Score: Sum of PFOA and PFOS results.
    - Alternate Score: Average of the Default Score and the square root of the highest other analyte result.

    Returns:
        - The calculated PFAS score.
        - The method used to determine the score ("max_pfoa_pfos" or "alternate").
    """
    default_score = pfoa_result + pfos_result
    alternate_score = (default_score + max_other_result ** 0.5) / 2
    if default_score >= alternate_score:
        return default_score, "max_pfoa_pfos"
    return alternate_score, "alternate"



def calc_afr_and_note(annuals, vfr):
    """
    Calculate AFR (Average Flow Rate) based on annual flow rates and VFR, and generate notes.

    Args:
        annuals: A list of annual flow rate records (each containing 'flow_rate_gpm').
        vfr: The maximum VFR value.

    Returns:
        A tuple containing:
            - The calculated AFR value.
            - A note indicating missing data or other observations.
    """
    note_parts = []

    # Handle annual flow rates
    annual_flow_rates = sorted(
        [entry.get('flow_rate_gpm', 0) for entry in (annuals or [])],
        reverse=True
    )
    annual_flow_rates = (annual_flow_rates + [0, 0, 0])[:3]  # Ensure 3 values
    
    if not annuals:
        note_parts.append("no annual production data provided")
    elif len(annuals) < 3:
        note_parts.append(f"only {len(annuals)} years of annual production provided")

    # Calculate AAFR (average of top 3 flow rates)
    aafr = sum(annual_flow_rates) / 3
    
    # Handle missing VFR
    if not isinstance(vfr, (int, float)):
        vfr = 0
        note_parts.append("vfr missing or invalid")
    
    # Calculate AFR (average of AAFR and VFR)
    afr = (aafr + vfr) / 2
    
    # Combine notes
    afr_note = " and ".join(note_parts) if note_parts else None

    return afr, afr_note



def calc_gfes(pfas_score, afr, defendant):
    """
    Calculate the GFE (Good Faith Estimate) based on the PFAS score, AFR, and defendant.

    Args:
        pfas_score: The PFAS score value.
        afr: The AFR (Adjusted Flow Rate) value.
        defendant: The name of the defendant ('Tyco' or 'BASF').

    Returns:
        The calculated GFE value.
    """
    pfas_score = max(pfas_score, 0) if pfas_score is not None else 0
    afr = max(afr, 0) if afr is not None else 0

    if pfas_score == 0 or afr == 0:
        print(f"Warning: PFAS score or AFR is missing. GFE for {defendant} will be zero.")
        return 0


    if defendant == 'Tyco':
        log_gfe = 0.4403859 * math.log(pfas_score) + 0.6939285 * math.log(afr) + 4.3743621
    elif defendant == 'BASF':
        log_gfe = 0.4398083 * math.log(pfas_score) + 0.6938430 * math.log(afr) + 3.5034023
    else:
        print(f"Defendant must be Tyco or BASF")
        return

    gfe = math.exp(log_gfe)
    return gfe