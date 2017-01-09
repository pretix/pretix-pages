from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/pages/', views.IndexView.as_view(),
        name='index'),
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/pages/create', views.IndexView.as_view(),
        name='create'),
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/pages/(?P<page>\d+)/', views.IndexView.as_view(),
        name='edit'),
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/pages/(?P<page>\d+)/delete', views.IndexView.as_view(),
        name='delete'),
]
