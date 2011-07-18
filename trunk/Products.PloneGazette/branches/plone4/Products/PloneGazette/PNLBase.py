#
# $Id$
#

"""Basic services for most content classes"""

__version__ = "$Revision: 110864 $" [11:-2]

# Zope core import
from App.class_init import InitializeClass
from AccessControl import Permissions, getSecurityManager, ClassSecurityInfo, Unauthorized

# CMF/Plone imports
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ListFolderContents
from PNLPermissions import ChangeNewsletterTheme

class PNLContentBase:
    """Shared by all that's in a NewsletterCentral
    """
    security = ClassSecurityInfo()

    security.declarePublic('getTheme')
    def getTheme(self):
        """Returns the NewsletterTheme parent object or None"""

        obj = self
        while 1:
            obj = obj.aq_parent
            if obj.meta_type == 'NewsletterTheme':
                return obj
            if not obj:
                return None
        return

    security.declarePublic('getNewsletter')
    def getNewsletter(self):
        """Returns the NewsletterTheme parent object or None"""

        obj = self
        while obj:
            if obj.meta_type == 'Newsletter':
                return obj
            obj = obj.aq_parent
        return None

    security.declarePublic('ploneCharset')
    def ploneCharset(self):
        """The default charset of this Plone instance"""

        portal_properties = getToolByName(self, 'portal_properties')
        charset = portal_properties.site_properties.getProperty('default_charset').strip()
        return charset
        
    security.declareProtected(ListFolderContents, 'listFolderContents')
    def listFolderContents( self, spec=None, contentFilter=None, suppressHiddenFiles=0 ):
        """
        Hook around 'contentValues' to let 'folder_contents'
        be protected.  Duplicating skip_unauthorized behavior of dtml-in.

        In the world of Plone we do not want to show objects that begin with a .
        So we have added a simply check.  We probably dont want to raise an
        Exception as much as we want to not show it.

        """

        items = self.contentValues(spec=spec, filter=contentFilter)
        l = []
        for obj in items:
            id = obj.getId()
            v = obj
            try:
                if suppressHiddenFiles and id[:1]=='.':
                    raise Unauthorized(id, v)
                if getSecurityManager().validate(self, self, id, v):
                    l.append(obj)
            except (Unauthorized, 'Unauthorized'):
                pass
        return l
    
    # For plone 2.1+ to show unindexed content
#    security.declareProtected(ChangeNewsletterTheme, 'getFolderContents')
#    def getFolderContents(self, contentFilter=None,batch=False,b_size=100,full_objects=False):
#        """Override getFolderContents to show all objects"""
#        contents = self.listFolderContents(contentFilter=contentFilter)
#        if batch:
#            from Products.CMFPlone import Batch
#            b_start = self.REQUEST.get('b_start', 0)
#            batch = Batch(contents, b_size, int(b_start), orphan=0)
#            return batch
#        return contents

InitializeClass(PNLContentBase)
