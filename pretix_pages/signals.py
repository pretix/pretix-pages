from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import ugettext_lazy as _

from pretix.base.signals import logentry_display
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


@receiver(signal=logentry_display, dispatch_uid="pages_logentry_display")
def pretixcontrol_logentry_display(sender, logentry, **kwargs):
    event_type = logentry.action_type
    plains = {
        'pretix_pages.page.added': _('The page has been created.'),
        'pretix_pages.page.changed': _('The page has been modified.'),
        'pretix_pages.page.deleted': _('The page has been deleted.'),
    }

    if event_type in plains:
        return plains[event_type]
