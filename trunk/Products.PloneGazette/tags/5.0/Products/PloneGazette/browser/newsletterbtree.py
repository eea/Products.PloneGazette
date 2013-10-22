from Acquisition import aq_inner
from Products.Five import BrowserView
from Products.PloneGazette.browser.base import PGBaseViewMixin
from Products.PloneGazette.browser.interfaces import INewsletterBTreeView
from zope.interface import implements


class NewsletterBTreeView(BrowserView, PGBaseViewMixin):
    implements(INewsletterBTreeView)
    
    def listSubscribers(self):
        context = aq_inner(self.context)
        # blah, acquired from NewsletterTheme
        subscribers = context.getSubscribers()
        result = []
        for s in subscribers:
            # process catalog brains
            result.append({'url':s.getURL(), 
                           'email':s.email,
                           'format':s.format,
                           'id':s.id,
                           'active':s.active,
                           })
        return result

