from zope.interface import Interface
from zope.schema import Text
from Products.PloneGazette import PloneGazetteFactory as _

class INewsletterBTree(Interface):
    """ BTree folder - holds subscribers """
    
class INewsletterTheme(Interface):
    """ Base content object for newsletters and subscribers """

    extra_filters = Text(title=_("IMAP bouncing detection filters"), 
                         default=u"",
                         required=False)
