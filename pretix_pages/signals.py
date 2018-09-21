from django.dispatch import receiver
from django.template.loader import get_template
from django.urls import resolve, reverse
from django.utils.translation import ugettext_lazy as _
from pretix.base.signals import logentry_display, event_copy_data
from pretix.control.signals import html_head, nav_event
from pretix.multidomain.urlreverse import eventreverse
from pretix.presale.signals import (
    footer_link, front_page_bottom, html_head as html_head_presale, checkout_confirm_messages
)

from .models import Page


@receiver(nav_event, dispatch_uid="pages_nav")
def control_nav_pages(sender, request=None, **kwargs):
    if not request.user.has_event_permission(request.organizer, request.event, 'can_change_event_settings',
                                             request=request):
        return []
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


@receiver(signal=event_copy_data, dispatch_uid="pages_copy_data")
def event_copy_data_receiver(sender, other, **kwargs):
    for p in Page.objects.filter(event=other):
        p.pk = None
        p.event = sender
        p.save()


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


@receiver(footer_link, dispatch_uid="pages_footer_links")
def footer_link_pages(sender, request=None, **kwargs):
    cached = sender.cache.get('pages_footer_links')
    if not cached:
        cached = [
            {
                'label': p.title,
                'url': eventreverse(sender, 'plugins:pretix_pages:show', kwargs={
                    'slug': p.slug
                })
            } for p in Page.objects.filter(event=sender, link_in_footer=True)
        ]
        sender.cache.set('pages_footer_links', cached)

    return cached


@receiver(signal=front_page_bottom, dispatch_uid="pages_frontpage_links")
def pretixpresale_front_page_bottom(sender, **kwargs):
    cached = sender.cache.get('pages_frontpage_links')
    if cached is None:
        pages = list(Page.objects.filter(event=sender, link_on_frontpage=True))
        if pages:
            template = get_template('pretix_pages/front_page.html')
            cached = template.render({
                'event': sender,
                'pages': pages
            })
        else:
            cached = ""
        sender.cache.set('pages_frontpage_links', cached)

    return cached


@receiver(html_head, dispatch_uid="pages_html_head")
def html_head_control(sender, request=None, **kwargs):
    url = resolve(request.path_info)
    if url.namespace == 'plugins:pretix_pages':
        template = get_template('pretix_pages/control_head.html')
        return template.render({})
    else:
        return ""


@receiver(html_head_presale, dispatch_uid="pages_html_head_presale")
def html_head_presale(sender, request=None, **kwargs):
    url = resolve(request.path_info)
    if url.namespace == 'plugins:pretix_pages':
        template = get_template('pretix_pages/presale_head.html')
        return template.render({})
    else:
        return ""


@receiver(checkout_confirm_messages, dispatch_uid="pages_confirm_messages")
def confirm_messages(sender, *args, **kwargs):
    cached = sender.cache.get('pages_confirm_messages')
    if cached is None:
        pages = list(Page.objects.filter(event=sender, require_confirmation=True))
        if pages:
            cached = {
                'pages': _('I have read and agree with the content of the following pages: {plist}').format(
                    plist=', '.join([
                        '<a href="{url}" target="_blank">{title}</a>'.format(
                            title=str(p.title),
                            url=eventreverse(sender, 'plugins:pretix_pages:show', kwargs={
                                'slug': p.slug
                            })
                        ) for p in pages
                    ])
                )
            }
        else:
            cached = {}
        sender.cache.set('pages_confirm_messages', cached)
    return cached
