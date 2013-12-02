from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse_lazy
# from django.views.generic.base import TemplateView

from user.forms import CustomPasswordResetForm
from user.views import BaseUserCreationView


urlpatterns = patterns(
    '',
    url(
        r'^deconnexion/$',
        'django.contrib.auth.views.logout_then_login',
        name='logout'),
    url(
        r'^compte/creer$',
        BaseUserCreationView.as_view(),
        name='register'),
    # Password recovery
    url(
        r'^compte/mot-de-passe-oublie/$',
        'django.contrib.auth.views.password_reset',
        {
            'template_name': 'user/reset_password.html',
            'post_reset_redirect': reverse_lazy('user:home'),
            'email_template_name': 'user/reset_password_email.html',
            'password_reset_form': CustomPasswordResetForm,
        },
        name='password.reset',),
    url(
        r'^compte/reset-mot-de-passe/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm',
        {
            'template_name': 'user/reset_password_done.html',
            'post_reset_redirect': reverse_lazy('user:login'),
        },
        name='password.reset.done',),
)
urlpatterns += patterns(
    'user.views',
    url(
        r'^connexion/$',
        'login',
        {
            'template_name': 'user/login.html',
        },
        name='login'),
    # Facebook
    url(
        r'^fb_auth/$',
        'fb_auth',
        name='fb.auth'),
    url(
        r'^fb_callback/$',
        'fb_callback',
        name='fb.callback'),
    url(
        r'^fb_disconnect/$',
        'fb_disconnect',
        name='fb.disconnect'),
    url(
        r'^$',
        'home',
        name='home'),
    # Account edition
    url(r'^compte/editer$', 'baseuser_edit', name='edit'),
    url(r'^compte/supprimer$', 'baseuser_delete', name='delete'),
)
