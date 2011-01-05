from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import base_hasattr
from Products.PloneGazette.NewsletterTheme import DEFAULT_REMOVE_NOTICE_TEMPLATE
from Products.PloneGazette.config import PG_CATALOG
import logging

logger = logging.getLogger('PloneGazette')

def isNotPloneGazetteProfile(context):
    return context.readDataFile('plonegazette.txt') is None


def importVarious(context):
    """
    """
    if isNotPloneGazetteProfile(context):
        return 

    site = context.getSite()
    #migrateAttributes(site)
    
    wtool = getToolByName(site, 'portal_workflow')
    ctool = getToolByName(site, 'portal_catalog')
    newsletterthemes = [s.getObject() for s in ctool(portal_type='NewsletterTheme')]
    for nl in newsletterthemes:
        if not base_hasattr(nl, PG_CATALOG):
            logger.info('Migrating Subscriber objects to catalog for NewsletterTheme %s' % nl.getId())
            nl._initCatalog()
            # find subscribers in newsletter theme and 'subscribers' folder
            subscribers = [s for s in nl.objectValues('Subscriber')]
            folder = nl.getSubscriberFolder()
            if folder is not None:
                subscribers.extend([s for s in folder.objectValues('Subscriber')])
            for s in subscribers:
                # migrate attributes
                if s._internalVersion == 1:
                    update_catalog = True
                    s.email    = s.title
                    s.fullname = ''
                    del s.title
                    s._internalVersion = 2
                # index all subscribers
                s.indexObject()
            logger.info('Migration of Subscriber objects done.')

    update_security = False
    chain = wtool.getChainFor('Subscriber')
    if 'one_state_workflow' not in chain:
        logger.info('Setting plone_workflow for Subscriber objects')
        wtool.setChainForPortalTypes(('Subscriber',), ('plone_workflow',))
        wf = wtool.getWorkflowById('plone_workflow')
        update_security = True
        logger.info('Settingplone_workflow for Subscriber objects done.')
        # we don't need allowedRolesAndUsers index, because subscribers are not listed
        # in default templates nor indexed in portal_catalog
        
    return ''


def importGoogle(context):
    """
    """
    if isNotPloneGazetteProfile(context):
        return 

    site = context.getSite()
    pt = getToolByName(site, 'portal_types')
    newsletter_theme = getattr(pt, 'NewsletterTheme')
    newsletter_theme.addAction(name="Google Analitycs", id="ga", action="string:${object_url}/NewsletterTheme_googleForm", 
			       condition="", category="object", permission="PNL Change Newsletter Theme", visible="1")


def migrateAttributes(self):
    """ Migrate Newsletter instances to have all required attributes
    """
    if isNotPloneGazetteProfile(context):
        return 

    ctool = getToolByName(self, 'portal_catalog')
    nls = ctool(portal_type='Newsletter')
    for nl in nls:
        obj = nl.getObject()
        if obj is not None:
            if not base_hasattr(obj, '_dynamic_content'):
                setattr(obj, '_dynamic_content', None)
                obj._p_changed = 1

            
def migrateInternalV3(context):
    """For version 3 of the Subscriber content type, adds an index for the bounce number
    and some default attributes
    """
    if isNotPloneGazetteProfile(context):
        return 
    
    site = context.getSite()
    ctool = getToolByName(site, 'portal_catalog')
    newsletterthemes = [s.getObject() for s in ctool(portal_type='NewsletterTheme')]
    for nl in newsletterthemes:
        catalog = nl[PG_CATALOG]
        if 'is_bouncing' not in catalog.indexes():
            catalog.addIndex('is_bouncing', 'FieldIndex')

        if not base_hasattr(nl, 'removeNoticeTemplate'):
            nl.removeNoticeTemplate = DEFAULT_REMOVE_NOTICE_TEMPLATE

        if not base_hasattr(nl, 'verp_prefix'):
            nl.verp_prefix = u""

        if not base_hasattr(nl, 'extra_filters'):
            nl.extra_filters = u""

        if not base_hasattr(nl, 'automatic_cleanup'):
            nl.automatic_cleanup = False

        if not base_hasattr(nl, 'removeNoticeMailSubject'):
            nl.automatic_cleanup = u"You have been automatically removed from this newsletter"

    logger.info('Migration of of content types to internal v3 done.')
