from django import forms
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView, ListView, CreateView, UpdateView

from pretix.control.permissions import EventPermissionRequiredMixin
from .models import Page


class PageList(EventPermissionRequiredMixin, ListView):
    model = Page
    context_object_name = 'pages'
    paginate_by = 20
    template_name = 'pretix_pages/index.html'


class PageForm(forms.ModelForm):

    class Meta:
        model = Page
        fields = (
            'title', 'slug', 'text', 'link_in_footer', 'link_on_frontpage'
        )


class PageEditForm(PageForm):
    slug = forms.CharField(label=_('URL form'), disabled=True)


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
        messages.success(request, _('The selected category has been deleted.'))
        return HttpResponseRedirect(self.get_success_url())


class PageUpdate(EventPermissionRequiredMixin, PageDetailMixin, UpdateView):
    model = Page
    form_class = PageEditForm
    template_name = 'pretix_pages/form.html'
    context_object_name = 'page'

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


class PageCreate(EventPermissionRequiredMixin, CreateView):
    model = Page
    form_class = PageForm
    template_name = 'pretix_pages/form.html'

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
