from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import ugettext_lazy as _

from pretix.control.signals import nav_event


@receiver(nav_event, dispatch_uid="pages_nav")
def control_nav_import(sender, request=None, **kwargs):
    url = resolve(request.path_info)
    return [
        {
            'label': _('Pages'),
            'url': reverse('plugins:pretix_pages:index', kwargs={
                'event': request.event.slug,
                'organizer': request.event.organizer.slug,
            }),
            'active': (url.namespace == 'plugins:pretix_pages'),
            'icon': 'file-text',
        }
    ]
