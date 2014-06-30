#
# $Id$
#

"""Misc utilities"""

import re
from Products.CMFDefault.utils import checkEmailAddress
from Products.CMFDefault.exceptions import EmailAddressInvalid

def checkMailAddress(obj, someAddr):
    """Checks the validity of a mail address"""
    # #5353 use checkEmailAddress from CMFDefault utils instead of
    # validateSingleEmailAddress from plone_utils as the plone email validator 
    # is better at detecting invalid addreses
    try:
        checkEmailAddress(someAddr)
    except EmailAddressInvalid:
        return False
    return True

from AccessControl import SpecialUsers

def ownerOfObject(obj):
    """Provides acl_user acquisition wrapped owner of object"""
    udb, uid = obj.getOwnerTuple()
    root = obj.getPhysicalRoot()
    udb = root.unrestrictedTraverse(udb, None)
    if udb is None:
        user = SpecialUsers.nobody
    else:
        user = udb.getUserById(uid, None)
        if user is None:
            user = SpecialUsers.nobody
        else:
            user = user.__of__(udb)
    return user

def escPercent(text):
    """Replace '%' with '%%' except '%('"""
    pat = re.compile(r'%(?!\()')
    return pat.sub('%%', text)
