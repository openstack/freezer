from django.conf.urls import patterns
from django.conf.urls import url

from .views import IndexView
from openstack_dashboard.dashboards.devfreezer.freezerweb import views


urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
   url(r'^\?tab=mypanel_tabs_tab$',
        views.IndexView.as_view(), name='mypanel_tabs')
)
