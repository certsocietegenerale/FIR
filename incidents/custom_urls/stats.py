from django.urls import re_path

from incidents import views

app_name='stats'

urlpatterns = [
    re_path(r'^yearly$', views.yearly_stats, name='yearly'),
    re_path(r'^data/yearly/incidents$', views.data_yearly_incidents, name='data_yearly_incidents'),

    re_path(r'^data/yearly/bl$', views.data_yearly_bl, name='data_yearly_bl'),
    re_path(r'^data/yearly/bl/(?P<year>\d+)/incidents$', views.data_yearly_bl, {'type': 'incidents'}, name='data_yearly_bl'),
    re_path(r'^data/yearly/bl/(?P<year>\d+)/events$', views.data_yearly_bl, {'type': 'events'}, name='data_yearly_bl_events'),  # events
    re_path(r'^data/yearly/bl/detection$', views.data_yearly_bl_detection, name='data_yearly_bl_detection'),
    re_path(r'^data/yearly/bl/severity$', views.data_yearly_bl_severity, name='data_yearly_bl_severity'),
    re_path(r'^data/yearly/bl/category$', views.data_yearly_bl_category, name='data_yearly_bl_category'),
    re_path(r'^data/yearly/bl/plan$', views.data_yearly_bl_plan, name='data_yearly_bl_plan'),

    # compare with previous year

    # html view
    re_path(r'^yearly/compare/$', views.yearly_compare, name='yearly_compare'),
    re_path(r'^yearly/compare/(?P<year>\d+)$', views.yearly_compare, name='yearly_compare'),

    # over time (by type)
    re_path(r'^data/yearly/compare/(?P<year>\d+)/(?P<type>\w+)$', views.data_yearly_compare, name='data_yearly_compare'),
    # evolution (by divisor and type)
    re_path(r'^data/yearly/compare/evolution/(?P<year>\d+)/(?P<type>\w+)/(?P<divisor>\w+)$', views.data_yearly_evolution, name='data_yearly_evolution'),
    re_path(r"^data/yearly/(?P<field>\w+)$", views.data_yearly_field, name="data_yearly_field"),

    # major incidents
    re_path(r'^quarterly/major$', views.quarterly_major, name='quarterly_major'),
    re_path(r'^quarterly/major/(?P<start_date>[\d\-]+)$', views.quarterly_major, name='quarterly_major'),

    # per bl
    re_path(r'^data/quarterly/(?P<business_line>[\w\s]+)/variation$', views.data_incident_variation, name='data_incident_variation'),
    re_path(r'^data/quarterly/(?P<business_line>[\w\s]+)/(?P<divisor>\w+)$', views.data_quarterly_bl, name='data_quarterly_bl'),
    re_path(r'^quarterly/close_old$', views.close_old, name='close_old'),
    re_path(r'^quarterly/(?P<business_line>[\w\s]+)$', views.quarterly_bl_stats, name='quarterly_bl_stats'),
    re_path(r'^quarterly/$', views.quarterly_bl_stats, name='quarterly_bl_stats_default'),

    # sandbox
    re_path(r'^sandbox/$', views.sandbox, name='sandbox'),

    # date format 2013-09-19
    re_path(r'^data/sandbox/$', views.data_sandbox, name='data_sandbox'),

    # attributes
    re_path(r'^attributes/$', views.stats_attributes, name='attributes'),
    re_path(r'^data/attributes/basic/$', views.stats_attributes_basic, name='attributes_basic'),
    re_path(r'^data/attributes/table/$', views.stats_attributes_table, name='attributes_table'),
    re_path(r'^data/attributes/over_time/$', views.stats_attributes_over_time, name='attributes_over_time'),
]
