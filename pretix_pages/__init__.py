from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PluginApp(AppConfig):
    name = 'pretix_pages'
    verbose_name = 'Pages'

    class PretixPluginMeta:
        name = _('Pages')
        author = 'Raphael Michel'
        category = 'FEATURE'
        description = _('Allows you to add static pages to your event site, for example for a FAQ, '
                        'terms of service, etc.')
        visible = True
        version = '1.3.1'

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_pages.PluginApp'
