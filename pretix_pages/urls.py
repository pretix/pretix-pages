from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/pages/$',
        views.PageList.as_view(),
        name='index'),
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/pages/create$',
        views.PageCreate.as_view(),
        name='create'),
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/pages/(?P<page>\d+)/$',
        views.PageUpdate.as_view(),
        name='edit'),
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/pages/(?P<page>\d+)/delete$',
        views.PageDelete.as_view(),
        name='delete'),
]

event_patterns = [
    url(r'^page/(?P<slug>[^/]+)/$', views.ShowPageView.as_view(), name='show'),
]
