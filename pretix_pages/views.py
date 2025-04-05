import bleach
import lxml.html
from django import forms
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Max
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from i18nfield.forms import I18nFormField
from pretix.base.forms import I18nModelForm, I18nMarkdownTextarea
I18nMarkdownTextarea
from pretix.control.permissions import (
    EventPermissionRequiredMixin, event_permission_required,
)
from pretix.helpers.compat import CompatDeleteView
from pretix.multidomain.urlreverse import build_absolute_uri
from urllib.request import urlopen

from .models import Page


class PageList(EventPermissionRequiredMixin, ListView):
    model = Page
    context_object_name = "pages"
    paginate_by = 20
    template_name = "pretix_pages/index.html"
    permission = "can_change_event_settings"

    def get_queryset(self):
        return Page.objects.filter(event=self.request.event)


def page_move(request, page, up=True):
    """
    This is a helper function to avoid duplicating code in page_move_up and
    page_move_down. It takes a page and a direction and then tries to bring
    all pages for this event in a new order.
    """
    try:
        page = request.event.page_set.get(id=page)
    except Page.DoesNotExist:
        raise Http404(_("The requested page does not exist."))
    pages = list(request.event.page_set.order_by("position", "title"))

    index = pages.index(page)
    if index != 0 and up:
        pages[index - 1], pages[index] = pages[index], pages[index - 1]
    elif index != len(pages) - 1 and not up:
        pages[index + 1], pages[index] = pages[index], pages[index + 1]

    for i, p in enumerate(pages):
        if p.position != i:
            p.position = i
            p.save()

    request.event.cache.clear()
    messages.success(request, _("The order of pages has been updated."))


@event_permission_required("can_change_event_settings")
def page_move_up(request, organizer, event, page):
    page_move(request, page, up=True)
    return redirect(
        "plugins:pretix_pages:index",
        organizer=request.event.organizer.slug,
        event=request.event.slug,
    )


@event_permission_required("can_change_event_settings")
def page_move_down(request, organizer, event, page):
    page_move(request, page, up=False)
    return redirect(
        "plugins:pretix_pages:index",
        organizer=request.event.organizer.slug,
        event=request.event.slug,
    )


class PageForm(I18nModelForm):
    text = I18nFormField(
        required=False,
        widget=I18nMarkdownTextarea,
        widget_kwargs={'attrs': {
            'rows': '12',
        }}
    )

    def __init__(self, *args, **kwargs):
        self.event = kwargs.get("event")
        super().__init__(*args, **kwargs)

    class Meta:
        model = Page
        fields = (
            "title",
            "slug",
            "text",
            "link_in_footer",
            "link_on_frontpage",
            "require_confirmation",
        )

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if Page.objects.filter(slug=slug, event=self.event).exists():
            raise forms.ValidationError(
                _("You already have a page on that URL."),
                code="duplicate_slug",
            )
        return slug

    mimes = {
        "image/gif": "gif",
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }

    def clean_text(self):
        t = self.cleaned_data["text"]
        content_type = self.instance.content_type or 'html'
        if content_type == 'html':
            for locale, html in t.data.items():
                etrees = lxml.html.fragments_fromstring(html)
                t.data[locale] = ""
                for etree in etrees:
                    # Find all data:-based image URLs, store them to CDN and replace the image node
                    for image in etree.xpath("//img"):
                        original_image_src = image.attrib["src"]
                        if original_image_src.startswith("data:"):
                            ftype = original_image_src.split(";")[0][5:]
                            if ftype in self.mimes:
                                with urlopen(original_image_src) as response:
                                    cfile = ContentFile(response.read())
                                    nonce = get_random_string(length=32)
                                    name = "pub/{}/pages/img/{}.{}".format(
                                        self.event.organizer.slug, nonce, self.mimes[ftype]
                                    )
                                    stored_name = default_storage.save(name, cfile)
                                    stored_url = default_storage.url(stored_name)
                                    image.attrib["src"] = stored_url
                    t.data[locale] += lxml.html.tostring(etree).decode()

        # TODO: store embedded images in markdown
        return t


class PageEditForm(PageForm):
    slug = forms.CharField(label=_("URL form"), disabled=True)

    def clean_slug(self):
        return self.instance.slug


class PageDetailMixin:
    def get_object(self, queryset=None) -> Page:
        try:
            return Page.objects.get(event=self.request.event, id=self.kwargs["page"])
        except Page.DoesNotExist:
            raise Http404(_("The requested page does not exist."))

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_pages:index",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )


class PageDelete(EventPermissionRequiredMixin, PageDetailMixin, CompatDeleteView):
    model = Page
    template_name = "pretix_pages/delete.html"
    context_object_name = "page"
    permission = "can_change_event_settings"

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.log_action("pretix_pages.page.deleted", user=self.request.user)
        self.object.delete()
        messages.success(request, _("The selected page has been deleted."))
        self.request.event.cache.clear()
        return HttpResponseRedirect(self.get_success_url())


class PageEditorMixin:

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.request.event
        return kwargs


class PageUpdate(
    EventPermissionRequiredMixin, PageDetailMixin, PageEditorMixin, UpdateView
):
    model = Page
    form_class = PageEditForm
    template_name = "pretix_pages/form.html"
    context_object_name = "page"
    permission = "can_change_event_settings"

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_pages:edit",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
                "page": self.object.pk,
            },
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx["locales"] = []
        ctx["url"] = build_absolute_uri(
            self.request.event,
            "plugins:pretix_pages:show",
            kwargs={
                "slug": self.object.slug,
            },
        )
        ctx["content_type"] = self.object.content_type

        for lng in self.request.event.settings.locales:
            dataline = (
                self.object.text.data[lng]
                if self.object.text is not None
                and (isinstance(self.object.text.data, dict))
                and lng in self.object.text.data
                else ""
            )
            ctx["locales"].append((lng, dataline))
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        messages.success(self.request, _("Your changes have been saved."))
        if form.has_changed():
            self.object.log_action(
                "pretix_pages.page.changed",
                user=self.request.user,
                data={k: form.cleaned_data.get(k) for k in form.changed_data},
            )
        self.request.event.cache.clear()
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, _("We could not save your changes. See below for details.")
        )
        return super().form_invalid(form)


class PageCreate(EventPermissionRequiredMixin, PageEditorMixin, CreateView):
    model = Page
    form_class = PageForm
    template_name = "pretix_pages/form.html"
    permission = "can_change_event_settings"

    @cached_property
    def content_type(self):
        return self.kwargs['content_type'] if 'content_type' in self.kwargs else 'html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx["locales"] = [
            (locale, "") for locale in self.request.event.settings.locales
        ]
        ctx["content_type"] = self.content_type
        return ctx

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_pages:index",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )

    @transaction.atomic

    def form_valid(self, form):
        form.instance.content_type = self.content_type
        form.instance.event = self.request.event
        form.instance.event = self.request.event
        form.instance.position = (
            self.request.event.page_set.aggregate(p=Max("position"))["p"] or 0
        ) + 1
        messages.success(self.request, _("The new page has been created."))
        ret = super().form_valid(form)
        form.instance.log_action(
            "pretix_pages.page.added",
            data=dict(form.cleaned_data),
            user=self.request.user,
        )
        self.request.event.cache.clear()
        return ret

    def form_invalid(self, form):
        messages.error(
            self.request, _("We could not save your changes. See below for details.")
        )
        return super().form_invalid(form)


class ShowPageView(TemplateView):
    template_name = "pretix_pages/show.html"

    def get_page(self):
        try:
            return Page.objects.get(event=self.request.event, slug=self.kwargs["slug"])
        except Page.DoesNotExist:
            raise Http404(_("The requested page does not exist."))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        page = self.get_page()
        ctx["page"] = page

        if page.content_type == 'markdown':
            # markdown pages are getting sanitized by the rich_text filter
            ctx["content"] = page.text
        else:
            attributes = dict(bleach.ALLOWED_ATTRIBUTES)
            attributes["a"] = ["href", "title", "target"]
            attributes["p"] = ["class"]
            attributes["li"] = ["class"]
            attributes["img"] = ["src"]

            ctx["content"] = bleach.clean(
                str(page.text),
                tags=bleach.ALLOWED_TAGS | {"img", "p", "br", "s", "sup", "sub", "u", "h3", "h4", "h5", "h6"},
                attributes=attributes,
                protocols=bleach.ALLOWED_PROTOCOLS | {"data"},
            )
        return ctx
