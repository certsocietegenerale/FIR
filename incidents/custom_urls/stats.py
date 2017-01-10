from django.conf.urls import url

from incidents import views

urlpatterns = [
    url(r'^yearly$', views.yearly_stats, name='yearly'),
    url(r'^data/yearly/incidents$', views.data_yearly_incidents, name='data_yearly_incidents'),

    url(r'^data/yearly/bl$', views.data_yearly_bl, name='data_yearly_bl'),
    url(r'^data/yearly/bl/(?P<year>\d+)/incidents$', views.data_yearly_bl, {'type': 'incidents'}, name='data_yearly_bl'),
    url(r'^data/yearly/bl/(?P<year>\d+)/events$', views.data_yearly_bl, {'type': 'events'}, name='data_yearly_bl_events'),  # events
    url(r'^data/yearly/bl/detection$', views.data_yearly_bl_detection, name='data_yearly_bl_detection'),
    url(r'^data/yearly/bl/severity$', views.data_yearly_bl_severity, name='data_yearly_bl_severity'),
    url(r'^data/yearly/bl/category$', views.data_yearly_bl_category, name='data_yearly_bl_category'),
    url(r'^data/yearly/bl/plan$', views.data_yearly_bl_plan, name='data_yearly_bl_plan'),

    # compare with previous year

    # html view
    url(r'^yearly/compare/$', views.yearly_compare, name='yearly_compare'),
    url(r'^yearly/compare/(?P<year>\d+)$', views.yearly_compare, name='yearly_compare'),

    # over time (by type)
    url(r'^data/yearly/compare/(?P<year>\d+)/(?P<type>\w+)$', views.data_yearly_compare, name='data_yearly_compare'),
    # evolution (by divisor and type)
    url(r'^data/yearly/compare/evolution/(?P<year>\d+)/(?P<type>\w+)/(?P<divisor>\w+)$', views.data_yearly_evolution, name='data_yearly_evolution'),
    url(r"^data/yearly/(?P<field>\w+)$", views.data_yearly_field, name="data_yearly_field"),

    # major incidents
    url(r'^quarterly/major$', views.quarterly_major, name='quarterly_major'),
    url(r'^quarterly/major/(?P<start_date>[\d\-]+)$', views.quarterly_major, name='quarterly_major'),

    # per bl
    url(r'^data/quarterly/(?P<business_line>[\w\s]+)/variation$', views.data_incident_variation, name='data_incident_variation'),
    url(r'^data/quarterly/(?P<business_line>[\w\s]+)/(?P<divisor>\w+)$', views.data_quarterly_bl, name='data_quarterly_bl'),
    url(r'^quarterly/close_old$', views.close_old, name='close_old'),
    url(r'^quarterly/(?P<business_line>[\w\s]+)$', views.quarterly_bl_stats, name='quarterly_bl_stats'),
    url(r'^quarterly/$', views.quarterly_bl_stats, name='quarterly_bl_stats_default'),

    # sandbox
    url(r'^sandbox/$', views.sandbox, name='sandbox'),

    # date format 2013-09-19
    url(r'^data/sandbox/$', views.data_sandbox, name='data_sandbox'),

    # attributes
    url(r'^attributes/$', views.stats_attributes, name='attributes'),
    url(r'^data/attributes/basic/$', views.stats_attributes_basic, name='attributes_basic'),
    url(r'^data/attributes/table/$', views.stats_attributes_table, name='attributes_table'),
    url(r'^data/attributes/over_time/$', views.stats_attributes_over_time, name='attributes_over_time'),
]
