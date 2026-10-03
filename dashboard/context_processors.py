from .models import FooterSettings


def footer_settings(request):
    settings = FooterSettings.objects.filter(pk=1).first()
    if settings is None:
        settings = FooterSettings(pk=1)
    return {'footer_settings': settings}
