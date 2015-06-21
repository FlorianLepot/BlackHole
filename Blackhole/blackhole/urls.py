from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'blackhole.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'web/login.html'}),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/web/'}),

    url(r'^password/change/$',
        'django.contrib.auth.views.password_change',
        {'template_name': 'web/password_change.html'},
        name='password_change'),
    url(r'^password/change/done/$',
		RedirectView.as_view(url='/web/'),
        name='password_change_done'),
 
    url(r'^admin/', include(admin.site.urls)),
    url(r'^web/', include('web.urls')),
)
