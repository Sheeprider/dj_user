# -*- coding: utf-8 -*-
import simplejson as json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as log_user, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as login_view
# from django.contrib.sites.models import Site
# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, HttpResponse  # , HttpResponseNotAllowed
from django.template.response import TemplateResponse
from django.shortcuts import RequestContext, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from facebook import GraphAPIError, GraphAPI, FacebookAuthError

from user.forms import (
    CustomAuthenticationForm,
    BaseUserCreationForm,
    BaseUserEditionForm,
    BaseUserDeleteForm,)
    # StudentAboutForm,
    # StudentProfileForm,
    # StudentPasswordForm,
    # ContactForm
from user.utils import get_facebook, clean_fb_session


def login(request, *args, **kwargs):
    if request.user and request.user.is_authenticated():
        # TODO : set next variable in session for facebook login
        next = request.GET.get('next', reverse(settings.LOGIN_REDIRECT_URL))
        return HttpResponseRedirect(next)
    return login_view(request, authentication_form=CustomAuthenticationForm, *args, **kwargs)


def home(request):
    """
    Home view…
    """
    tpl = 'pages/home.html'
    c = RequestContext(request)
    return TemplateResponse(request, tpl, c)


def _baseuser_edit(request):
    """Display BaseUser edition form."""
    tpl = 'user/edit.html'
    baseuser = get_object_or_404(get_user_model(), id=request.user.id)
    form = BaseUserEditionForm(instance=baseuser)
    c = RequestContext(request)

    if request.method == 'POST':
        form = BaseUserEditionForm(request.POST, request.FILES, instance=baseuser)
        success = u'Votre profil a correctement été mis à jour'
        fail = u'Erreur lors de la mise à jour, merci de corriger les erreurs indiquées.'
        if form.is_valid():
            form.save()
            messages.success(request, success, fail_silently=True,)
            # refresh request's user
            request.user = get_user_model().objects.get(id=request.user.id)
        else:
            messages.error(request, fail, fail_silently=True,)

    c.update({'form': form})
    return TemplateResponse(request, tpl, c)
baseuser_edit = login_required(_baseuser_edit)


def _baseuser_delete(request):
    """
    Display BaseUser deletion form.
    Submission is meant to be done with ajax.
    """
    tpl = 'user/delete.html'
    baseuser = get_object_or_404(get_user_model(), id=request.user.id)
    form = BaseUserDeleteForm()
    c = RequestContext(request)

    if request.method == 'POST':
        form = BaseUserDeleteForm(request.POST)
        success = u'Compte Supprimé'
        if form.is_valid(user=baseuser):
            baseuser.delete()
            messages.success(request, success, fail_silently=True,)
            # Log user out
            logout_url = reverse('user:logout')
            if request.is_ajax():
                return HttpResponse(json.dumps({'url': logout_url}), content_type="application/json")
            return HttpResponseRedirect(logout_url)
        else:
            if request.is_ajax():
                return HttpResponse(json.dumps(form.errors), content_type="application/json")

    c.update({'form': form})
    return TemplateResponse(request, tpl, c)
baseuser_delete = login_required(_baseuser_delete)


class BaseUserCreationView(FormView):
    """Student creation view, add a nice message after registering sucessfully."""
    template_name = 'user/register.html'
    form_class = BaseUserCreationForm
    success_url = reverse_lazy('user:login')

    def get(self, request, *args, **kwargs):
        # Update initial data with facebook data if present in session
        fb_token = request.session.get('fb_token')
        if fb_token:
            access_token = fb_token.get('access_token')
            g = GraphAPI(access_token)
            try:
                me = g.get('me')
            except GraphAPIError:
                clean_fb_session(request.session)
            else:
                self.initial.update(email=me.get('email'), fb_token=fb_token, fb_id=me.get('id'))

        response = super(BaseUserCreationView, self).get(request, *args, **kwargs)
        return response

    def post(self, request, *args, **kwargs):
        response = super(BaseUserCreationView, self).post(request, *args, **kwargs)
        # Create the user and add a message.
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Student with email:{0} successfully created.'.format(form.cleaned_data.get('email')),
                fail_silently=True,
            )
            clean_fb_session(request.session)
        return response


#  ==================
#  = Facebook Views =
#  ==================
def fb_auth(request, *args, **kwargs):
    f = get_facebook()
    # TODO : ask for avatar ?
    auth_url = f.get_auth_url(scope=['email'], display='page')
    return HttpResponseRedirect(auth_url)


def fb_callback(request, *args, **kwargs):
    # Get oauth token from facebook with client's code
    f = get_facebook()
    code = request.GET.get('code')
    if not code:
        # The authorisation was refused or failed
        messages.error(
            request,
            _("Couldn't connect to facebook."),
            fail_silently=True,
        )
        # Return to profile edition for logged-in user
        # TODO : Change redirect for Teachers
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('user:edit'))
        # Return to account creation
        return HttpResponseRedirect(reverse('user:register'))

    try:
        json_token = f.get_access_token(code)
    except FacebookAuthError, e:
        # TODO : Facebook unavailable
        messages.error(request, e.message, fail_silently=True,)
        return HttpResponseRedirect(reverse('user:login'))

    # Log user in if this facebook account is associated with a django user
    access_token = json_token.get('access_token')
    try:
        g = GraphAPI(access_token)
        me = g.get('me')
    except GraphAPIError, e:
        # TODO : GraphAPI unavailable
        messages.error(request, e.message, fail_silently=True,)
        return HttpResponseRedirect(reverse('user:login'))
    fb_id = me.get('id')
    if not request.user.is_authenticated():
        user = authenticate(access_token=access_token, fb_id=fb_id)
        if user is not None and user.is_active:
            log_user(request, user)

    # Save token if user is authenticated
    # or redirect to account creation
    # TODO : manage token expiration ?
    if request.user.is_authenticated():
        if not request.user.fb_id is fb_id:
            # Association with new FB account
            try:
                request.user.fb_id = fb_id
            except ValidationError, e:
                # FB account already associated with a user
                messages.error(request, e.message, fail_silently=True,)
            else:
                request.user.fb_token = json_token
                request.user.save()
        return HttpResponseRedirect(reverse('user:edit'))
    else:
        request.session.update({'fb_token': json_token, 'fb_id': fb_id})
        return HttpResponseRedirect(reverse('user:register'))


def _fb_disconnect(request, *args, **kwargs):
    request.user.fb_id = None
    request.user.fb_token = None
    request.user.save()
    return HttpResponseRedirect(reverse('user:edit'))
fb_disconnect = login_required(_fb_disconnect)


# def contact(request):
#     tpl = 'pages/contact.html'
#     Student_email = Student.objects.get(id=request.user.id).email if request.user.id else None
#     Student_name = Student.objects.get(id=request.user.id).name if request.user.id else None
#     form = ContactForm(initial={'email': Student_email, 'name': Student_name})
#     data = {
#         'form': form,
#     }

#     if request.method == 'POST':
#         form = ContactForm(request.POST, initial={'email': Student_email, 'name': Student_name})
#     if form.is_valid():
#         form.send_mail()
#         messages.success(request, _(u'Message envoyé.'))
#         return HttpResponseRedirect(reverse('pages.home'))
#     else:
#         data.update(form=form)
#     return render_to_response(
#         tpl,
#         data,
#         RequestContext(request),
#     )
