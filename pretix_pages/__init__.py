from django.apps import AppConfig


class PluginApp(AppConfig):
    name = 'pretix_pages'
    verbose_name = 'Static content for your pretix event'

    class PretixPluginMeta:
        name = 'Static content for your pretix event'
        author = 'Raphael Michel'
        description = 'pretix plugin that allows you to add static pages to your event site, for example for a FAQ, terms of service, etc.'
        visible = True
        version = '1.0.0'

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_pages.PluginApp'
