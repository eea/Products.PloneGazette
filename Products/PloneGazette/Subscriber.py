#
# $Id$
#

"""
Subscriber main class
"""

# Standard Python imports
import string

# Zope core imports
from App.class_init import InitializeClass
from AccessControl import Permissions, getSecurityManager, ClassSecurityInfo, Unauthorized
from AccessControl.SecurityManagement import newSecurityManager
from DateTime import DateTime

# CMF/Plone imports
from Products.CMFCore.permissions import View, ManageProperties, ListFolderContents, ModifyPortalContent
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFCore.PortalContent import PortalContent
from Products.CMFCore.utils import getToolByName

# Product specific imports
from PNLPermissions import *
from PNLUtils import ownerOfObject
from PNLUtils import checkMailAddress
from PNLBase import PNLContentBase
from Products.PloneGazette.config import PG_CATALOG, MAXIMUM_BOUNCES
#################
## The factory ##
#################

def addSubscriber(self, id, email = '', REQUEST = {}):
    """
    Factory method for a Subscriber object
    """
    obj = Subscriber(id, email)
    self._setObject(id, obj)
    getattr(self, id)._post_init()
    if REQUEST.has_key('RESPONSE'):
        return REQUEST.RESPONSE.redirect(self.absolute_url() + '/manage_main')

#################################
## The Subscriber content type ##
#################################

class Subscriber(PortalContent, DefaultDublinCoreImpl, PNLContentBase):
    """Subscriber class"""

    bounces = None
    
    ########################################
    ## Registration info for portal_types ##
    ########################################

    factory_type_information = {
        'id': 'Subscriber',
        'portal_type': 'Subscriber',
        'meta_type': 'Subscriber',
        'description': 'A newletter subscriber (has no sense oudside a NewsletterTheme object)',
        'content_icon': 'Subscriber.gif',
        'product': 'PloneGazette',
        'factory': 'addSubscriber',
        'immediate_view': 'Subscriber_edit',
        'global_allow': 0,
        'filter_content_types': 0,
        'allowed_content_types': (),
        'actions': (
            {
                'id': 'view',
                'name': 'View',
                'action': 'string:${object_url}/Subscriber_view',
                'permissions': (View,),
                'category': 'object'
                },
            {
                'id': 'edit',
                'name': 'Edit',
                'action': 'string:${object_url}/Subscriber_editForm',
                'permissions': (ChangeSubscriber,),
                'category': 'object',
                },
            ),
        'aliases' : {
                'edit'       : 'Subscriber_editForm',
            }, 
    }
    
    ###########################
    ## Basic class behaviour ##
    ###########################

    meta_type = factory_type_information['meta_type']

    manage_options = PortalContent.manage_options

    # Standard security settings
    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    # Init method
    security.declarePrivate('__init__')
    def __init__(self, id, email=''):
        """__init__(self, id, email='')"""

        # version 2 - adds email and fullname
        #           - removes title attribute 
        self._internalVersion = 2
        self.id = id
        self.title = '' #not used, just to keep it compatible with ver 2.0
        self.fullname = '' # not used in templates yet
        self.email = email
        self.format = 'HTML'
        self.active = False
        self.creation_date = DateTime()

        # version 3 - add the bounces attribute
        self.bounces = []
        return

    security.declarePrivate('_post_init')
    def _post_init(self):
        """
        _post_init(self) => Post-init method (that is, method that is called AFTER the class has been set into the ZODB)
        """

        self.indexObject()
        return

    def __setstate__(self,state):
        """Updates"""
        
        Subscriber.inheritedAttribute("__setstate__") (self, state)
        if not hasattr(self, 'fullname'):
            self.fullname = ''
        if not hasattr(self, 'email'):
            self.email = self.title

    #############################
    ## Content editing methods ##
    #############################

    # Edit method (change this to suit your needs)
    # This edit method should only change attributes that are neither 'id' or metadatas.
    security.declareProtected(ChangeSubscriber, 'edit')
    def edit(self, format='', active=False, email=''):
        """
        edit(self, text = '') => object modification method
        """

        # Change attributes
        self.format = format
        self.active = not not active
        self.email = email.strip()

        # Reindex
        self.reindexObject()
        return

    security.declarePublic('Title')
    def Title(self):
        return self.fullname or self.email

    security.declarePublic('SearchableText')
    def SearchableText(self):
        return ' '.join([self.fullname, self.email])

    security.declarePublic('activateOnFirstTime')
    def activateOnFirstTime(self, REQUEST):
        """Activation for first time access
        """
        firsttime = REQUEST.form.get('firsttime')
        if firsttime:
#            newSecurityManager(REQUEST, ownerOfObject(self.getTheme()))
            self.active = True
        return

    def checkMailAddress(self, mail):
        return checkMailAddress(self,mail)

    security.declarePublic('is_bouncing')
    def is_bouncing(self):
        """Is this subscriber bouncing? """
        return self.bounces and (len(self.bounces) >= MAXIMUM_BOUNCES)
    
    #####################
    ## Utility methods ##
    #####################

    security.declareProtected(ChangeSubscriber, 'mailingInfo')
    def mailingInfo(self):
        """returns None or (email, format, edit_url) tuple."""
        
        if self.active:
            return self.email, self.format, self.absolute_url() + '/Subscriber_editForm'
        return

    ############################
    ## Hooks for base classes ##
    ############################

    # Indexing to subscribers_catalog
    # All indexing methods uses this method to get corrent catalog
    def _getCatalogTool(self):
        return getattr(self.getTheme(), PG_CATALOG, None)

    # Overwritten CMFCore/CMFCatalogAware
    # If subscribers container contains more then 10.000 subscriber
    # objects this function make the add process to take minutes
    def reindexObjectSecurity(self, skip_self=False):
        pass

# Class instanciation
InitializeClass(Subscriber)
