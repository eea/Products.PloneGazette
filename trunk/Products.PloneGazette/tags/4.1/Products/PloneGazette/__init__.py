#
# $Id$
#

"""Newsletter Plone"""

__version__ = "$Revision: 110864 $" [11:-2]

from zope.i18nmessageid import MessageFactory
PloneGazetteFactory = MessageFactory('plonegazette')

from Products.Archetypes import listTypes
from Products.Archetypes.public import process_types
from Products.CMFCore import permissions
from Products.CMFCore.utils import ContentInit
from Products.CMFCore.utils import registerIcon
from Products.PloneGazette.PNLPermissions import AddNewsletterTheme, ChangeNewsletter
from Products.PloneGazette.config import PROJECTNAME

import NewsletterTheme, Newsletter, Subscriber, Section, NewsletterTopic

import patches  #applies patches

#from Products.PloneGazette.config import product_globals
#DirectoryView.registerDirectory('skins', product_globals)
#DirectoryView.registerDirectory('skins/PloneGazette', product_globals)

## Types to register

contentConstructors = (Newsletter.addNewsletter, Subscriber.addSubscriber, NewsletterTopic.addNewsletterTopic)
contentClasses = (Newsletter.Newsletter, Subscriber.Subscriber, NewsletterTopic.NewsletterTopic)
factoryTypes = (Newsletter.Newsletter.factory_type_information,
                Subscriber.Subscriber.factory_type_information,
                NewsletterTopic.NewsletterTopic.factory_type_information)


def initialize(context):

    import NewsletterReference
    import NewsletterRichReference
    import NewsletterBTree

    ContentInit(
        'Plone Gazette Newsletter Theme',
        content_types = (NewsletterTheme.NewsletterTheme,),
        permission=AddNewsletterTheme,
        extra_constructors = (NewsletterTheme.addNewsletterTheme,),
        fti = NewsletterTheme.NewsletterTheme.factory_type_information).initialize(context)

    ContentInit(
        'Plone Gazette Newsletter Section',
        content_types = (Section.Section,),
        permission = ChangeNewsletter,
        extra_constructors = (Section.addSection,),
        fti = Section.Section.factory_type_information).initialize(context)

    ContentInit(
        'Plone Gazette resources',
        content_types = contentClasses,
        permission = permissions.AddPortalContent,
        extra_constructors = contentConstructors,
        fti = factoryTypes).initialize(context)

    registerIcon(NewsletterTheme.NewsletterTheme, 'skins/PloneGazette/NewsletterTheme.gif', globals())
    registerIcon(Newsletter.Newsletter, 'skins/PloneGazette/Newsletter.gif', globals())
    registerIcon(Subscriber.Subscriber, 'skins/PloneGazette/Subscriber.gif', globals())
    registerIcon(Section.Section, 'skins/PloneGazette/Section.gif', globals())
    registerIcon(NewsletterTopic.NewsletterTopic, 'skins/PloneGazette/NewsletterTopic.gif', globals())

    # Archetypes init
    content_types, constructors, ftis = process_types(listTypes(PROJECTNAME), PROJECTNAME)

    ContentInit(
        PROJECTNAME + ' Content',
        content_types = content_types,
        permission = permissions.AddPortalContent,
        extra_constructors = constructors,
        fti = ftis,).initialize(context)

    return
