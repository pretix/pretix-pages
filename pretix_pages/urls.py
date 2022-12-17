from django.urls import path

from . import views

urlpatterns = [
    path('control/event/<str:organizer>/<str:event>/pages/',
        views.PageList.as_view(),
        name='index'),
    path('control/event/<str:organizer>/<str:event>/pages/create',
        views.PageCreate.as_view(),
        name='create'),
    path('control/event/<str:organizer>/<str:event>/pages/<int:page>/',
        views.PageUpdate.as_view(),
        name='edit'),
    path('control/event/<str:organizer>/<str:event>/pages/<int:page>/delete',
        views.PageDelete.as_view(),
        name='delete'),
    path('control/event/<str:organizer>/<str:event>/pages/<int:page>/up',
        views.page_move_up,
        name='up'),
    path('control/event/<str:organizer>/<str:event>/pages/<int:page>/down',
        views.page_move_down,
        name='down'),
]

event_patterns = [
    path('page/<str:slug>/', views.ShowPageView.as_view(), name='show'),
]
