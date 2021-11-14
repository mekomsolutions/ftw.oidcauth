import Zope2
from Testing.makerequest import makerequest
from zope.globalrequest import setRequest
import transaction
import json
from pathlib import Path
import os
DEFAULT_ID_OIDC = 'oidc'
def configure_oauth(event):
    app = Zope2.app()
    app = makerequest(app)
    app.REQUEST["PARENTS"] = [app]
    setRequest(app.REQUEST)
    container = app.unrestrictedTraverse("/")
    oauth_config_file = os.getenv("OAUTH_CONFIG_FILE", "client.json")
    config_file = os.path.join(oauth_config_file)
    if Path(config_file).exists():
        try:
            f = open(config_file)
            config = json.load(f)
            for plonesite in container.objectValues("Plone Site"):
                pas = plonesite.acl_users
                plugin = pas.get(DEFAULT_ID_OIDC)
                site_config = config[plonesite.getId()]
                if plugin:
                    for key in site_config:
                        value = site_config[key]
                        if key=='properties_mapping':
                            props_data=plugin.get_valid_json(json.dumps(site_config[key]))
                            value = props_data
                        if key=='roles':
                            roles = site_config[key]
                            plugin._roles = tuple([role.strip() for role in roles.split(',') if role])
                        plugin._setPropValue(key, value)
            transaction.commit()
            f.close()
        except FileNotFoundError:
            print("Config File does not exist , leaving unconfigured")
        except:
            print("Unknown Error leaving unconfigured")
