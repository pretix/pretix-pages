from django.views.generic import ListView

from pretix.control.permissions import EventPermissionRequiredMixin
from .models import Page


class IndexView(EventPermissionRequiredMixin, ListView):
    model = Page
    context_object_name = 'pages'
    paginate_by = 20
    template_name = 'pretix_pages/index.html'
