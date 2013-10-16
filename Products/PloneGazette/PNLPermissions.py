#
# $Id$
#
__doc__ = """Define new permissions for newsletter handling
$Id$
"""
__version__ = "$Revision: 110864 $" [11:-2]

from Products.CMFCore.permissions import setDefaultRoles

# New specific permissions

AddNewsletterTheme = 'PNL Add Newsletter Theme'
ChangeNewsletterTheme = 'PNL Change Newsletter Theme'
AddNewsletter = 'PNL Add Newsletter'
ChangeNewsletter = 'PNL Change Newsletter'
AddSubscriber = 'PNL Add Subscriber'
ChangeSubscriber = 'PNL Change Subscriber'
ExternalService = "PNL External Service"
CleanupSubscribers = "PloneGazette: Cleanup Subscribers"

# Default roles for those permissions
setDefaultRoles(AddNewsletterTheme, ('Manager',))
setDefaultRoles(ChangeNewsletterTheme, ('Manager', 'Owner'))
setDefaultRoles(AddNewsletter, ('Manager',))
setDefaultRoles(ChangeNewsletter, ('Manager', 'Owner'))
setDefaultRoles(AddSubscriber, ('Anonymous', 'Manager', 'Owner', 'Member'))
setDefaultRoles(ChangeSubscriber, ('Anonymous', 'Manager', 'Owner'))
setDefaultRoles(ExternalService, ('Manager',))
setDefaultRoles(CleanupSubscribers, ('Manager', 'packrole'))
