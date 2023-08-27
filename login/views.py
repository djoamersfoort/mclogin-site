from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.contrib.auth import login as auth_login
from requests_oauthlib import OAuth2Session
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest
from django.shortcuts import render
from requests import post
from .models import Link


class AuthorizeView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, uuid):
        try:
            link = Link.objects.get(user=request.user)
        except Link.DoesNotExist:
            link = Link(user=request.user, mc_uuid=uuid)
            link.save()

        if link.mc_uuid != uuid:
            return HttpResponseForbidden("Already linked")

        post("http://localhost:3000/authorize", json={
            'target': str(uuid),
            'firstName': request.user.first_name
        })

        return render(request, 'authorized.html')


@method_decorator(never_cache, name='dispatch')
class LoginView(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        oauth = OAuth2Session(client_id=settings.IDP_CLIENT_ID,
                              redirect_uri=settings.IDP_REDIRECT_URL,
                              scope=settings.IDP_API_SCOPES)
        auth_url, state = oauth.authorization_url(
            settings.IDP_AUTHORIZE_URL,
            state=request.GET.get('next')
        )
        return HttpResponseRedirect(auth_url)


class LoginResponseView(View):
    def get(self, request: HttpRequest, *args, **kwargs):
        oauth = OAuth2Session(client_id=settings.IDP_CLIENT_ID,
                              redirect_uri=settings.IDP_REDIRECT_URL)
        full_response_url = request.build_absolute_uri()
        full_response_url = full_response_url.replace('http:', 'https:')
        try:
            access_token = oauth.fetch_token(settings.IDP_TOKEN_URL,
                                             authorization_response=full_response_url,
                                             client_secret=settings.IDP_CLIENT_SECRET)
        except Exception as e:
            # Something went wrong getting the token
            return HttpResponseForbidden('Geen toegang: {0}'.format(e))

        if 'access_token' in access_token and access_token['access_token'] != '':
            user_profile = oauth.get(settings.IDP_API_URL).json()
            username = "idp-{0}".format(user_profile['id'])

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User()
                user.username = username
                user.set_unusable_password()

            user.first_name = user_profile['firstName']
            user.last_name = user_profile['lastName']
            user.save()

            auth_login(request, user)
            return HttpResponseRedirect(request.GET.get('state'))
        else:
            return HttpResponseForbidden('IDP Login mislukt')
