# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer
from ftw.oidcauth.plugin import OIDCPlugin
from zope.component.hooks import getSite
from App.config import getConfiguration
import os
import json
from pathlib import Path
from Products.CMFCore.utils import getToolByName
from pprint import pprint
import io
DEFAULT_ID_OIDC = 'oidc'
TITLE_OIDC = 'Open ID connect'

@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            'ftw.oidcauth:uninstall',
        ]
def _add_oidc(portal, pluginid, title): 
    pas = portal.acl_users
    if pluginid in pas.objectIds():
        return title + ' already installed.'
    plugin = OIDCPlugin(pluginid, title=title)
    pas._setObject(pluginid, plugin)
    plugin = pas[plugin.getId()]  # get plugin acquisition wrapped!
    for info in pas.plugins.listPluginTypeInfo():
        interface = info['interface']
        if not interface.providedBy(plugin):
            continue
        pas.plugins.activatePlugin(interface, plugin.getId())
        pas.plugins.movePluginsDown(
            interface,
            [x[0] for x in pas.plugins.listPlugins(interface)[:-1]],
        )
def _remove_plugin(pas, pluginid=DEFAULT_ID_OIDC):
    if pluginid in pas.objectIds():
        pas.manage_delObjects([pluginid])

def post_install(context):
    """Post install script"""
    _add_oidc(getSite(), DEFAULT_ID_OIDC, TITLE_OIDC)


def uninstall(context):
    """Uninstall script"""
    aclu = getSite().acl_users
    _remove_plugin(aclu, DEFAULT_ID_OIDC)
