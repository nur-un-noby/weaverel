def site_settings_context(request):
    """
    Context processor to make store settings (announcements, contact info, brand name, currency)
    available across all templates.
    """
    try:
        from store_settings.models import SiteConfiguration
        config = SiteConfiguration.get_solo()
    except Exception:
        config = None

    return {
        'site_config': config,
        'CURRENCY_SYMBOL': '৳',
        'CURRENCY_CODE': 'BDT',
    }
