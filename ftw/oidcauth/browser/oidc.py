from Products.CMFPlone.browser.login.logout import LogoutView
from Products.Five import BrowserView
from ftw.oidcauth.browser.oidc_tools import OIDCClientAuthentication
from ftw.oidcauth.errors import OIDCBaseError
from six.moves.urllib.parse import parse_qsl, urlencode
from zExceptions import NotFound as zNotFound
from zope.component import getMultiAdapter
from zope.interface import implements
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import NotFound
import logging

logger = logging.getLogger('ftw.oidc')


class OIDCView(BrowserView):
    """Endpoints for OIDC"""

    implements(IPublishTraverse)

    def __init__(self, context, request):
        super(OIDCView, self).__init__(context, request)
        self.method = None

    def publishTraverse(self, request, name):
        if self.method is None:
            if name == 'callback':
                self.method = name
            elif name == 'logout':
                self.method = name
            else:
                raise NotFound(self, name, request)
        else:
            raise NotFound(self, name, request)
        return self

    def __call__(self):
        if self.method == 'callback':
            self.callback()
        elif self.method == 'logout':
            self.logout()
        else:
            raise zNotFound()

    def callback(self):
        code = self.request.form.get('code')
        state = self.request.form.get('state')
        client_auth = OIDCClientAuthentication(
            self.request, code, state)
        try:
            client_auth.authorize()
        except OIDCBaseError as ex:
            self.set_error_response(ex.status_code, ex.message)
            return

        if client_auth.has_been_authorized:
            self.request.response.redirect(client_auth.get_redirect())
            return
        else:
            self.set_error_response(400, 'Invalid Request')
            return

    def set_error_response(self, status, message):
        response = self.request.response
        response.setHeader('Content-Type', 'text/plain')
        response.setStatus(status, lock=1)
        response.setBody(message, lock=1)

    def logout(self):
        p = OIDCClientAuthentication.get_oidc_plugin()
        base_url = get_base_url(self.context, self.request)
        original_redirect = self.request.get('redirect')
        redirect = base_url
        if original_redirect:
            if original_redirect.startswith("http:") or original_redirect.startswith("https:"):
                redirect = original_redirect
            else:
                redirect = base_url + original_redirect

        logout_base_url = p.end_session_endpoint
        params = {}
        if "?" in p.end_session_endpoint:
            url_parts = p.end_session_endpoint.split("?")
            logout_base_url = url_parts[0]
            params.update(dict(parse_qsl(url_parts[1])))
        params["client_id"] = p.client_id
        params["post_logout_redirect_uri"] = redirect
        logout_url = "{}?{}".format(logout_base_url, urlencode(params))
        self.request.response.redirect(logout_url)


class OIDCLogoutView(LogoutView):
    def __call__(self):
        if OIDCClientAuthentication.get_oidc_plugin().end_session_endpoint:
            base_url = get_base_url(self.context, self.request)
            next_ = self.request.get('next')
            oidc_logout = base_url + '/oidc/logout'
            if next_ is None or not next_.startswith(oidc_logout):
                if next_:
                    oidc_logout = "{}?{}".format(oidc_logout, urlencode({'redirect': next_}))
                redirect = "{}?{}".format(base_url + '/logout', urlencode({'next': oidc_logout}))
                self.request.response.redirect(redirect)
                return

        super(OIDCLogoutView, self).__call__()


def get_base_url(context, request):
    return getMultiAdapter((context, request), name="plone_portal_state").navigation_root_url()
