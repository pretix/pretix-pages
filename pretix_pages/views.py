import bleach
from django import forms
from django.contrib import messages
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    CreateView, DeleteView, ListView, TemplateView, UpdateView,
)
from pretix.base.forms import I18nModelForm
from pretix.control.permissions import EventPermissionRequiredMixin
from pretix.presale.utils import event_view

from .models import Page


class PageList(EventPermissionRequiredMixin, ListView):
    model = Page
    context_object_name = 'pages'
    paginate_by = 20
    template_name = 'pretix_pages/index.html'

    def get_queryset(self):
        return Page.objects.filter(event=self.request.event)


class PageForm(I18nModelForm):

    def __init__(self, *args, **kwargs):
        self.event = kwargs.get('event')
        super().__init__(*args, **kwargs)

    class Meta:
        model = Page
        fields = (
            'title', 'slug', 'text', 'link_in_footer', 'link_on_frontpage', 'require_confirmation'
        )

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if Page.objects.filter(slug=slug, event=self.event).exists():
            raise forms.ValidationError(
                _('You already have a page on that URL.'),
                code='duplicate_slug',
            )
        return slug


class PageEditForm(PageForm):
    slug = forms.CharField(label=_('URL form'), disabled=True)

    def clean_slug(self):
        return self.instance.slug


class PageDetailMixin:
    def get_object(self, queryset=None) -> Page:
        try:
            return Page.objects.get(
                event=self.request.event,
                id=self.kwargs['page']
            )
        except Page.DoesNotExist:
            raise Http404(_("The requested page does not exist."))

    def get_success_url(self) -> str:
        return reverse('plugins:pretix_pages:index', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })


class PageDelete(EventPermissionRequiredMixin, PageDetailMixin, DeleteView):
    model = Page
    form_class = PageForm
    template_name = 'pretix_pages/delete.html'
    context_object_name = 'page'

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.log_action('pretix_pages.page.deleted', user=self.request.user)
        self.object.delete()
        messages.success(request, _('The selected page has been deleted.'))
        return HttpResponseRedirect(self.get_success_url())


class PageEditorMixin:

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['event'] = self.request.event
        return kwargs


class PageUpdate(EventPermissionRequiredMixin, PageDetailMixin, PageEditorMixin, UpdateView):
    model = Page
    form_class = PageEditForm
    template_name = 'pretix_pages/form.html'
    context_object_name = 'page'

    def get_success_url(self) -> str:
        return reverse('plugins:pretix_pages:edit', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
            'page': self.object.pk
        })

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx['locales'] = []
        for lng in self.request.event.settings.locales:
            dataline = (
                self.object.text.data[lng]
                if self.object.text is not None and (
                    isinstance(self.object.text.data, dict)
                ) and lng in self.object.text.data
                else ""
            )
            ctx['locales'].append((lng, dataline))
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        messages.success(self.request, _('Your changes have been saved.'))
        if form.has_changed():
            self.object.log_action(
                'pretix_pages.page.changed', user=self.request.user, data={
                    k: form.cleaned_data.get(k) for k in form.changed_data
                }
            )
        return super().form_valid(form)


class PageCreate(EventPermissionRequiredMixin, PageEditorMixin, CreateView):
    model = Page
    form_class = PageForm
    template_name = 'pretix_pages/form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx['locales'] = [
            (l, "")
            for l in self.request.event.settings.locales
        ]
        return ctx

    def get_success_url(self) -> str:
        return reverse('plugins:pretix_pages:index', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })

    @transaction.atomic
    def form_valid(self, form):
        form.instance.event = self.request.event
        messages.success(self.request, _('The new page has been created.'))
        ret = super().form_valid(form)
        form.instance.log_action('pretix_pages.page.added', data=dict(form.cleaned_data),
                                 user=self.request.user)
        return ret


@method_decorator(event_view, name='dispatch')
class ShowPageView(TemplateView):
    template_name = 'pretix_pages/show.html'

    def get_page(self):
        try:
            return Page.objects.get(
                event=self.request.event,
                slug=self.kwargs['slug']
            )
        except Page.DoesNotExist:
            raise Http404(_("The requested page does not exist."))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        page = self.get_page()
        ctx['page'] = page

        attributes = dict(bleach.ALLOWED_ATTRIBUTES)
        attributes['a'] = ['href', 'title', 'target']
        attributes['p'] = ['class']
        attributes['li'] = ['class']

        ctx['content'] = bleach.clean(str(page.text), tags=bleach.ALLOWED_TAGS + [
            'p',
            'br',
            's',
            'sup',
            'sub',
            'u',
            'h3',
            'h4',
            'h5',
            'h6'
        ], attributes=attributes)
        return ctx
