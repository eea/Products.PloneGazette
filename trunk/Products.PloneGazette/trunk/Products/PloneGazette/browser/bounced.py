from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import base_hasattr
from Products.Five import BrowserView
from five.formlib import formbase
from Products.PloneGazette import PloneGazetteFactory as _
from Products.PloneGazette.browser.base import PGBaseViewMixin
from Products.PloneGazette.config import PG_CATALOG
from zope import schema
from zope.formlib import form
from zope.interface import Interface
import logging

logger = logging.getLogger('PloneGazette')

try:
    from elementtree.ElementTree import ElementTree, Element, tostring
except ImportError:
    #XXX: the code in this module has been tested only with elementtree; 
    #     using xml.etree may not actually work properly; xml.etree is only
    #     available in python >= 2.5, while elementtree needs to be installed on 
    #     python 2.4
    try:
        from xml.etree import ElementTree
        Element = ElementTree.Element
        tostring = ElementTree.tostring
    except ImportError:
        raise Exception("You need to install elementtree or use Python >= 2.5")


class ManageBouncedSubscribers(BrowserView,  PGBaseViewMixin):
    """Page to manage the Subscribers marked as hard bouncing"""

    def __call__(self,):
        base_url = "%s/subscribers_infos" % self.context.absolute_url()
        if "SUBMIT" not in self.request.form:
            return super(ManageBouncedSubscribers, self).__call__()

        count = self.context.remove_subscribers()
        tool = getToolByName(self.context, 'plone_utils')
        tool.addPortalMessage(_("removed_x_subscribers", 
                                default="Removed ${no} subscribers",
                                mapping={'no':count}
                                ))
        return self.request.response.redirect(base_url)


class IAddBouncedSubscribersSchema(Interface):
    """A schema for a form to add bouncing subscribers"""

    bounced_addresses = schema.Text(title=u"Bounced addresses", 
            description=u"Line separated, in format newsletter_id|email_address", 
            required=True)

    enable_automatic_cleanup = schema.Bool(title=u"Enable automatic cleanup",
            description=u"If enabled, an automatic cleanup of subscribers will be performed",
            default=False)


class AddBouncedSubscribers(formbase.FormBase, PGBaseViewMixin):
    """This is the handler to be used by the external bounced email detection script
    to announce PG of the bounced subscribers


    XXX: don't forget to order by newsletter order the bounces on the external handler side
    """
    form_fields = form.Fields(IAddBouncedSubscribersSchema)

    @form.action(u"Submit")
    def handle_submit(self, action, data):
        # The format for the incomming data is:
        # newsletter_id|email_address
        # If the newsletter id is missing, then it should be:
        # |email_address
        
        self.context.add_bounced_subscribers(data['bounced_addresses'])

        return "OK"


class GetBouncedServiceParameters(BrowserView):
    """Allows the external handler for bounced emails to retrieve some configuration parameters
    """

    def __call__(self):
        s = Element("settings")

        f = Element("filters")
        f.text = self.context.extra_filters
        s.append(f)

        p = Element("verp_prefix")
        p.text = self.context.verp_prefix
        s.append(p)

        e_ns = Element("newsletters")
        for nl in self.context.objectValues("Newsletter"):
            n = Element("newsletter")
            n.text = nl.id
            e_ns.append(n)
        s.append(e_ns)

        return tostring(s, 'utf-8')

