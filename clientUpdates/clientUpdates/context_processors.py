from clientUpdates.models import Pws, ClaimPws

def info_bar_context(request):
    if request.user.is_authenticated:
        try:
            pws_record = Pws.objects.get(form_userid=request.user.username)
            claim_pws_record = ClaimPws.objects.get(pwsid=pws_record.pwsid)
            print('test. this is a test.')
            return {
                'pws': pws_record,
                'claim_pws': claim_pws_record,
            }
        except (Pws.DoesNotExist, ClaimPws.DoesNotExist):
            # Optionally, log the error or return default values
            return {}
    return {}