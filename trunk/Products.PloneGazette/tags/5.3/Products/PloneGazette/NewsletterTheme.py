#
# $Id$
#

"""NewsletterCentral class"""

from AccessControl import SpecialUsers
from AccessControl import getSecurityManager, ClassSecurityInfo
from AccessControl.SecurityManagement import newSecurityManager, setSecurityManager
from Acquisition import aq_parent
from App.class_init import InitializeClass
from OFS import Folder
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault import SkinnedFolder
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFPlone.utils import base_hasattr, safe_unicode, log
from Products.MailHost.MailHost import _mungeHeaders
from Products.PageTemplates import Expressions
from Products.PloneGazette import PloneGazetteFactory as _
from Products.PloneGazette.PNLBase import PNLContentBase
from Products.PloneGazette.PNLPermissions import ChangeNewsletterTheme
from Products.PloneGazette.PNLUtils import ownerOfObject, checkMailAddress
from Products.PloneGazette.catalog import manage_addSubscribersCatalog
from Products.PloneGazette.config import PG_CATALOG
from Products.PloneGazette.interfaces import INewsletterTheme
from email.Header import Header
from zope.i18n import translate
from zope.interface import implements
from zope.tales.tales import CompilerError
import csv
import email.Message
import email.Utils
import os
import random
import string
import transaction

#from Products.PageTemplates.TALES import CompilerError


DEFAULT_UNSUBSCRIBE_TEMPLATE = """Dear subscriber,

You received this email to inform that you have been unsubscribed from this newsletter service.
You'll no longer receive our next newsletters at %(email)s

PLEASE DON'T REPLY TO THIS MAIL"""

DEFAULT_CONFIRM_TEMPLATE = """Dear subscriber,

You received this email to confirm that you want to unsubscribed from this newsletter service.
By doing this you'll no longer receive our next newsletters at %(email)s .

In order to unsubscribe please click this link:
%(url)s

PLEASE DON'T REPLY TO THIS MAIL"""

DEFAULT_ACTIVATION_SUBJECT = """Please activate your newsletter account"""

DEFAULT_ACTIVATION_TEMPLATE = """Dear subscriber,

We have received and recorded your newsletter subscription.
You must now activate your account to receive our newsletters.
To do this, just browse to this URL...
%(url)s
Then you'll receive our next newsletters at %(email)s

PLEASE DON'T REPLY TO THIS MAIL"""
# NewsletterTheme definition

DEFAULT_NEWSLETTER_FOOTER = """Thank you for subscribing to this newsletter.<br />
You can <a href="%(url)s">change your preferences</a> at any time.
"""

DEFAULT_REMOVE_NOTICE_TEMPLATE = """Dear subscriber,

You received this email because you have just been automatically removed from our
newsletter service %(url_service)s.

This action was caused by the repeated failure to deliver the newsletter that you
have signed up for. If you wish to receive the newsletter you'll have to register
again at %(url_register)s.

PLEASE DON'T REPLY TO THIS MAIL
"""

ADMIN_REMOVAL_REPORT_TEMPLATE = """Dear newsletter admin,
You are receiving this report because this email address is configured as the
notification address for the Newsletter Service at %(url_service)s.

As a result of automatic checks for bounced subscribers, the following %(no)s
subscribers have been removed permanently:

%(addresses)s
"""

#################
## The factory ##
#################
def addNewsletterTheme(self, id, title = '', REQUEST = {}):
    """
    Factory method for a NewsletterTheme object
    """
    obj = NewsletterTheme(id, title)
    self._setObject(id, obj)
    getattr(self, id)._post_init()
    if REQUEST.has_key('RESPONSE'):
        return REQUEST.RESPONSE.redirect('manage_main')
    return

########################################
## The NewsletterCentral content type ##
########################################

class NewsletterTheme(SkinnedFolder.SkinnedFolder, DefaultDublinCoreImpl, PNLContentBase):
    """NewsletterTheme class
    """
    ########################################
    ## Registration info for portal_types ##
    ########################################
    implements(INewsletterTheme)

    factory_type_information = {
        'id': 'NewsletterTheme',
        'portal_type': 'NewsletterTheme',
        'meta_type': 'NewsletterTheme',
        'description': 'Manage your newsletters with this',
        'content_icon': 'NewsletterTheme.gif',
        'product': 'PloneGazette',
        'factory': 'addNewsletterTheme',
        'immediate_view': 'NewsletterTheme_view',
        'filter_content_types': 1,
        'allowed_content_types': ('Newsletter', 'Subscriber', 'NewsletterBTree'),
        'actions': (
            {'id': 'view',
             'name': 'View',
             'action': 'string:${object_url}/NewsletterTheme_view',
             'permissions': (View,)},

            {'id': 'subscribe',
             'name': 'Subscribe',
             'action': 'string:${object_url}/NewsletterTheme_subscribeForm',
             'permissions': (View,)},

            {'id' : 'infos',
             'name' : 'Informations',
             'action' : 'string:${object_url}/subscribers_infos',
             'permissions' : (ChangeNewsletterTheme,)},

            {'id': 'edit',
             'name': 'Edit',
             'action': 'string:${object_url}/NewsletterTheme_editForm',
             'permissions': (ChangeNewsletterTheme,)},

            {'id': 'ga',
             'name': 'Google Analytics',
             'action': 'string:${object_url}/NewsletterTheme_googleForm',
             'permissions': (ChangeNewsletterTheme,)},

            {'id' : 'NewsletterTheme_importForm',
             'name' : 'Import',
             'action' : 'string:${object_url}/NewsletterTheme_importForm',
             'permissions' : (ChangeNewsletterTheme,)},
            ),
        'aliases' : {
                '(Default)'  : 'NewsletterTheme_view',
                'view'       : 'NewsletterTheme_view',
                'index.html' : '',
                'edit'       : 'base_edit',
                'properties' : 'base_metadata',
                'sharing'    : 'folder_localrole_form',
        },
        }

    ###########################
    ## Basic class behaviour ##
    ###########################

    meta_type = portal_type = 'NewsletterTheme'

    manage_options = Folder.Folder.manage_options + CMFCatalogAware.manage_options

    # Standard security settings
    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    _csv_import_log = ''
    _new_object = False
    alternative_portal_url = None

    # Dummy permission instanciation.
    # Permissions has to be "dummily" instanciated in order to be reachable for the factory_type_information structure.
    # In order to be very clear, we just declare each and every permission we use in this product.
    # security.declareProtected(ChangeNewsletterTheme, "dummyMethod_editPermission")

    def __init__(self, id, title=''):
        """__init__(self, id, title='')"""
        # NOTE : We shouldn't call parent's __init__ method as it would link to PortalFolder.__init__ and this
        # method sets 'self.id' and 'self.title' which is unuseful for us.

        global DEFAULT_ACTIVATION_TEMPLATE
        global DEFAULT_UNSUBSCRIBE_TEMPLATE
        DefaultDublinCoreImpl.__init__(self)
        self._internalVersion = 2
        self._subscribersCount = 0
        self.id = id
        self.format_list = ['HTML', 'Text']
        self.default_format = 'HTML'
        self.title = title
        self.description = ''
        self.testEmail = ''
        self.authorEmail = ''
        self.replyto = ''
        self.activationMailSubject = DEFAULT_ACTIVATION_SUBJECT
        self.activationMailTemplate = DEFAULT_ACTIVATION_TEMPLATE
        self.newsletterFooter = DEFAULT_NEWSLETTER_FOOTER
        self.notify = False
        self.renderTemplate = ''
        self._v_renderTemplate = None
        self.extraRecipients = ''
        self._v_extraRecipients = None
        self.subscriber_folder_id = ''
        self.unsubscribeMailSubject = "You have been unsubscribed from this newsletter"
        self.unsubscribeMailTemplate = DEFAULT_UNSUBSCRIBE_TEMPLATE
        self.confirmMailSubject = "Please confirm your unsubscribe."
        self.confirmMailTemplate = DEFAULT_CONFIRM_TEMPLATE
        self._new_object = True
        self.alternative_portal_url = None
        self.utm_source = ''
        self.utm_medium = 'email'

        #bouncing subscribers support
        self.extra_filters = u""
        self.verp_prefix = u""
        self.automatic_cleanup = False
        self.removeNoticeMailSubject = "You have been automatically removed from this newsletter"
        self.removeNoticeTemplate = DEFAULT_REMOVE_NOTICE_TEMPLATE
        return

    @property
    def _scatalog(self):
        return getattr(self, PG_CATALOG, None)

    security.declarePrivate('_post_init')
    def _post_init(self):
        """Post-init method (that is, method that is called AFTER the class has been set into the ZODB)
        """

        self.indexObject()
        self._initCatalog()
        return

    security.declareProtected(ChangeNewsletterTheme, 'edit')
    def edit(self, title='',  default_format='', testEmail='', authorEmail='', replyto='',
             activationMailSubject='', activationMailTemplate='', newsletterFooter='', notify=False,
             renderTemplate='', extraRecipients='', subscriber_folder_id='',
             unsubscribeMailSubject='', unsubscribeMailTemplate='', confirmMailSubject='', confirmMailTemplate='',
             alternative_portal_url=None, extra_filters=u"", verp_prefix=u"", automatic_cleanup=False,
             removeNoticeMailSubject="", removeNoticeTemplate=""):
        """Changes values"""

        self.title = title.strip()
        self.default_format = default_format
        self.testEmail = testEmail.strip()
        self.authorEmail = authorEmail.strip()
        self.replyto = replyto.strip()
        self.activationMailSubject = activationMailSubject.strip()
        self.activationMailTemplate = activationMailTemplate.strip()
        self.newsletterFooter = newsletterFooter.strip()
        self.notify = notify
        self.renderTemplate = renderTemplate.strip()
        self.extraRecipients = extraRecipients.strip()

        self.extra_filters = extra_filters
        self.verp_prefix = verp_prefix
        self.automatic_cleanup = automatic_cleanup
        self.removeNoticeTemplate = removeNoticeTemplate
        self.removeNoticeMailSubject = removeNoticeMailSubject

        dummy = self.getRenderTemplate(recompile=1)
        dummy = self.getExtraRecipients(recompile=1)

        if self._new_object and title:
            plone_tool = getToolByName(self, 'plone_utils')
            newid = plone_tool.normalizeString(title)
            parent = self.aq_parent
            if newid not in parent.objectIds():
                transaction.savepoint(optimistic=True)
                self._v_cp_refs = 1
                parent.manage_renameObject(self.id, newid)
                self._setId(newid)

        self._new_object=False

        self.reindexObject()
        self.subscriber_folder_id = subscriber_folder_id
        self.unsubscribeMailSubject = unsubscribeMailSubject.strip()
        self.unsubscribeMailTemplate = unsubscribeMailTemplate.strip()
        self.confirmMailSubject = confirmMailSubject.strip()
        self.confirmMailTemplate = confirmMailTemplate.strip()
        self.alternative_portal_url = alternative_portal_url
        return

    security.declareProtected(ChangeNewsletterTheme, 'edit_google')
    def edit_google(self, utm_source='', utm_medium=''):
        """Changes Google values"""
        self.utm_source = utm_source.strip()
        self.utm_medium = utm_medium.strip()
        return

    security.declareProtected(View, 'getNewsletters')
    def getNewsletters(self):
        """
        Return the "Newsletter" objects
        """
        mtool = getToolByName(self, 'portal_membership')
        wf = getToolByName(self, 'portal_workflow')

        checkPermission = mtool.checkPermission

        isLogged = not mtool.isAnonymousUser()
        result = [ x for x in self.objectValues('Newsletter') if
                            checkPermission('View', x) and
                            (isLogged or
                            wf.getInfoFor(x, 'review_state') == 'published')]
        return result

    security.declarePublic('createSubscriberObject')
    def createSubscriberObject(self, id):
        """
        """

        target_folder = self.getSubscriberFolder()
        if target_folder is None:
            target_folder = self

        target_folder.invokeFactory(self.getSubscriberTypes()[0], id)
        obj = getattr(target_folder, id)
        return obj

    security.declarePublic('getSubscriberFolder')
    def getSubscriberFolder(self):
        """
        Return the folder where subscriber objects will be create.
        It will be a "NewsletterBTree" if it exist, or the "NewsletterTheme" itself.
        """
        target_folder = None
        subscriber_folder_id = self.subscriber_folder_id
        if subscriber_folder_id and subscriber_folder_id in self.objectIds('NewsletterBTree'):
            target_folder = getattr(self, subscriber_folder_id)

        return target_folder

    security.declarePublic('getSubscriberById')
    def getSubscriberById(self, id):
        """
        """
        subscriber = None
        result = self._scatalog(id=id)
        if result:
            path = result[0].getPath()
            subscriber = self.unrestrictedTraverse(path)

        return subscriber

    ##################
    ## UI handlings ##
    ##################

    security.declarePrivate('_getRandomIdForSubscriber')
    def _getRandomIdForSubscriber(self):
        """
        """
        validChars = [c for c in string.letters + string.digits if ord(c) < 128]
        newId = "%05d" % self._subscribersCount + ''.join([random.choice(validChars) for x in range(5)])
        return newId

    def getSubscriberTypes(self):
        '''return all possible subscriber portal types'''
        return ['Subscriber']

    security.declarePublic('subscribeFormProcess')
    def subscribeFormProcess(self, REQUEST=None):
        """Handles NewsletterTheme_subscribeForm"""

        if REQUEST is None:
            REQUEST = self.REQUEST
        errors = {}
        data = {}
        charset = self.ploneCharset()

        if REQUEST.form.has_key('email'):
            # Form submitted
            emailaddress = REQUEST.form.get('email', '').strip()
            data['email'] = emailaddress

            email_verify = REQUEST.form.get('email_verify', 'not_submitted')

            format = REQUEST.form.get('format', self.default_format)
            data['format'] = format

            if not self.checkMailAddress(emailaddress):
                errors['email'] = _('This is not a valid mail address')
                return data, errors

             # This is an automated request, probably a bot, we fake a succesful registration"
            if email_verify:
                data['success'] = 1
                return data, errors

            if self.alreadySubscriber(emailaddress):
                errors['email'] = _('There is already a subscriber with this address')
            if not errors:
                # Creating the new account
                self._subscribersCount += 1
                newId = self._getRandomIdForSubscriber()
                # Continue method as owner of this object for "invokeFactory" security checkings.
                # (creating new objects through invokeFactory is not possible as anonymous because an owner is required)
                oldSecurityManager = getSecurityManager()
                newSecurityManager(REQUEST, SpecialUsers.system)
                newSubscriber = self.createSubscriberObject(newId)
                newSubscriber.edit(format=format, active=0, email=emailaddress)
                setSecurityManager(oldSecurityManager)

                # Make URL for editing this object
                subscriberEditUrl = newSubscriber.absolute_url() + '/Subscriber_editForm'   # :( FIXME
                #actions_tool = getToolByName(self, 'portal_actions')
                #actions = actions_tool.listFilteredActionsFor(object=newSubscriber)
                #subscriberEditUrl = [action['url'] for action in actions['object']
                #                     if action['id'] == 'edit'][0]

                # Make and send the activation mail
                """
                mailBody = ("From: %s\r\n"
                            "To: %s\r\n"
                            "Content-Type: text/plain; charset=%s\r\n"
                            "Subject: %s\r\n\r\n")
                mailBody = mailBody % (self.authorEmail, data['email'],
                                       self.ploneCharset(), self.activationMailSubject)
                #mailBody += self.activationMailTemplate % {'url': self.absolute_url() + '?active=%s&format=%s' % (newId, format), 'email': emailaddress}
                mailBody += self.activationMailTemplate % {'url': self.id + '?active=%s&format=%s' % (newId, format), 'email': emailaddress}

                """
                mailMsg=email.Message.Message()
                mailMsg["To"]=data['email']
                mailMsg["From"]=self.authorEmail
                mailMsg["Subject"]=str(Header(safe_unicode(self.activationMailSubject), 'utf8'))
                mailMsg["Date"]=email.Utils.formatdate(localtime=1)
                mailMsg["Message-ID"]=email.Utils.make_msgid()
                mailMsg["Mime-version"]="1.0"

                bodyText = self.activationMailTemplate % {'url': self.id + '?active=%s&format=%s' % (newId, format), 'email': emailaddress}
                mailMsg["Content-type"]="text/plain"
                mailMsg.set_payload(safe_unicode(bodyText).encode(charset), charset)
                #mailMsg.preamble="Mime message\n"
                mailMsg.epilogue="\n" # To ensure that message ends with newline

                try:
                    #TODO: is
                    self.sendmail(self.authorEmail, (emailaddress,), mailMsg, subject = mailMsg['subject'])
                except Exception, e:
                    raise
                    # The email could not be sent, probably the specified address doesn't exist
                    #errors['email'] = translate('Email could not be sent. Error message is: ${error}', mapping={'error':str(e)}, context=self)
                    #data['email'] = emailaddress
                    #data['format'] = self.default_format
                    #transaction.abort()
                    #return data, errors

                if self.notify:
                    # Notify the NewsletterTheme owner
                    """mailBody = ("From: %s\r\n"
                                "To: %s\r\n"
                                "Content-Type: text/plain; charset=%s\r\n"
                                "Subject: %s : %s\r\n\r\n"
                                "%s\n%s")
                    mailBody = mailBody % (self.authorEmail, self.testEmail,
                                           self.ploneCharset(),
                                           self.title,
                                           translate("Newsletter new subscriber", domain='plonegazette', context=REQUEST),
                                           translate("See the new account at...", domain='plonegazette', context=REQUEST),
                                           subscriberEditUrl)
                    subject = "Subject: %s : %s" % (self.title,
                                           translate("Newsletter new subscriber", domain='plonegazette', context=REQUEST))
                    """
                    subject = "%s : %s" % (self.title,
                                           translate("Newsletter new subscriber", domain='plonegazette', context=REQUEST))
                    mailMsg=email.Message.Message()
                    mailMsg["To"]=self.testEmail
                    mailMsg["From"]=self.authorEmail
                    mailMsg["Subject"]=str(Header(safe_unicode(subject), 'utf8'))
                    mailMsg["Date"]=email.Utils.formatdate(localtime=1)
                    mailMsg["Message-ID"]=email.Utils.make_msgid()
                    mailMsg["Mime-version"]="1.0"

                    bodyText = "%s\n%s\n%s%s" % (translate("See the new account at...", context=REQUEST, domain='plonegazette'),
                                           subscriberEditUrl, 'E-mail address: ', data['email'])
                    mailMsg["Content-type"]="text/plain"
                    #mailMsg.set_charset(charset)
                    mailMsg.set_payload(safe_unicode(bodyText).encode(charset), charset)
                    #mailMsg.preamble="Mime message\n"
                    mailMsg.epilogue="\n" # To ensure that message ends with newline

                    self.sendmail(self.authorEmail, (self.testEmail,), mailMsg, subject = mailMsg['subject'])
                data['success'] = 1
        else:
            # First entry in the form
            data['email'] = ''
            data['format'] = self.default_format
        return data, errors

    security.declarePublic('confirmUnsubscribe')
    def confirmUnsubscribe(self, subscriber_id):
        """The subscriber receives a confirm unsubscribe mail
        """
        subscriber = self.getSubscriberById(subscriber_id)
        if subscriber is not None:
            charset = self.ploneCharset()
            subscriber_email = subscriber.email.strip()

            # Make and send the unsubscribe mail
            mailMsg=email.Message.Message()
            mailMsg["To"]=subscriber_email
            mailMsg["From"]=self.authorEmail
            mailMsg["Subject"]=str(Header(safe_unicode(self.confirmMailSubject), 'utf8'))
            mailMsg["Date"]=email.Utils.formatdate(localtime=1)
            mailMsg["Message-ID"]=email.Utils.make_msgid()
            mailMsg["Mime-version"]="1.0"

            bodyText = self.confirmMailTemplate % {'email': subscriber_email, 'url': self.id + '/unSubscribe?subscriber_id=%s' % subscriber.id}
            mailMsg["Content-type"]="text/plain"
            mailMsg.set_payload(safe_unicode(bodyText).encode(charset), charset)
            mailMsg.epilogue="\n" # To ensure that message ends with newline

            self.sendmail(self.authorEmail, (subscriber_email,), mailMsg, subject = mailMsg['subject'])

    security.declarePublic('unSubscribe')
    def unSubscribe(self, subscriber_id, REQUEST=None):
        """The subscriber clicked the Unsubscribe button
        """
        subscriber = self.getSubscriberById(subscriber_id)
        if subscriber is not None:
            charset = self.ploneCharset()
            subscriber_email = subscriber.email.strip()

            # Make and send the unsubscribe mail
            mailMsg=email.Message.Message()
            mailMsg["To"]=subscriber_email
            mailMsg["From"]=self.authorEmail
            mailMsg["Subject"]=str(Header(safe_unicode(self.unsubscribeMailSubject), 'utf8'))
            mailMsg["Date"]=email.Utils.formatdate(localtime=1)
            mailMsg["Message-ID"]=email.Utils.make_msgid()
            mailMsg["Mime-version"]="1.0"

            bodyText = self.unsubscribeMailTemplate % {'email': subscriber_email}
            mailMsg["Content-type"]="text/plain"
            mailMsg.set_payload(safe_unicode(bodyText).encode(charset), charset)
            mailMsg.epilogue="\n" # To ensure that message ends with newline

            self.sendmail(self.authorEmail, (subscriber_email,), mailMsg, subject = mailMsg['subject'])

            parent = subscriber.aq_parent
            newSecurityManager(REQUEST, SpecialUsers.system)
            parent.manage_delObjects([subscriber_id,])

        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(self.absolute_url() + '/NewsletterTheme_unsubscribed')
        return

    def removeSubscriber(self, subscriber):
        charset = self.ploneCharset()
        subscriber_email = subscriber.email.strip()

        url_service = self.absolute_url()
        url_register = "%s/NewsletterTheme_subscribeForm" % url_service

        # Make and send the unsubscribe mail
        mailMsg=email.Message.Message()
        mailMsg["To"]=subscriber_email
        mailMsg["From"]=self.authorEmail
        mailMsg["Subject"]=str(Header(safe_unicode(self.removeNoticeMailSubject), 'utf8'))
        mailMsg["Date"]=email.Utils.formatdate(localtime=1)
        mailMsg["Message-ID"]=email.Utils.make_msgid()
        mailMsg["Mime-version"]="1.0"

        bodyText = self.removeNoticeTemplate % {'url_service': url_service,
                                                'url_register':url_register}
        mailMsg["Content-type"]="text/plain"
        mailMsg.set_payload(safe_unicode(bodyText).encode(charset), charset)
        mailMsg.epilogue="\n" # To ensure that message ends with newline

        try:
            self.sendmail(self.authorEmail, subscriber_email,
                                mailMsg, subject = mailMsg['subject'])
        except:
            log("Could not send a PloneGazzette unsubscribe message to %s, removing subscriber anyway." % subscriber_email)

        parent = aq_parent(subscriber)
        parent.manage_delObjects([subscriber.id])

    def notifyRemoval(self, addresses):
        charset = self.ploneCharset()
        admin_email = self.testEmail

        url_service = self.absolute_url()
        url_register = "%s/NewsletterTheme_subscribeForm" % url_service

        # Make and send the unsubscribe mail
        mailMsg=email.Message.Message()
        mailMsg["To"]=admin_email
        mailMsg["From"]=self.authorEmail
        mailMsg["Subject"]=str(Header(safe_unicode("Automated bouncing subscriber removal report"), 'utf8'))
        mailMsg["Date"]=email.Utils.formatdate(localtime=1)
        mailMsg["Message-ID"]=email.Utils.make_msgid()
        mailMsg["Mime-version"]="1.0"

        bodyText = ADMIN_REMOVAL_REPORT_TEMPLATE % {'url_service': url_service,
                                                    'no':len(addresses),
                                                    'addresses':'\n'.join(addresses)}
        mailMsg["Content-type"]="text/plain"
        mailMsg.set_payload(safe_unicode(bodyText).encode(charset), charset)
        mailMsg.epilogue="\n" # To ensure that message ends with newline

        self.sendmail(self.authorEmail, (admin_email), mailMsg, subject = mailMsg['subject'])

    def checkMailAddress(self, mail):
        """ Check Email address and return a boolean with the indicated result
        """
        return checkMailAddress(self, mail)

    def checkTalExpressions(self, talExpressions, state=None, errors=None):
        """
        Check TALES expressions for edit_form validation
        """
        talEngine = Expressions.getEngine()
        for fieldId, value in talExpressions:
            if not value:
                continue
            try:
                dummy = talEngine.compile(value)
            except CompilerError, e:
                msg = _('TALES compilation error: ${error}', mapping={'error':str(e)})
                if state is not None:
                    state.setError(fieldId, msg)
                if errors is not None:
                    errors[fieldId] = msg
        if state is not None:
            return state
        elif errors is not None:
            return errors
        return

    ##############
    ## Utilities #
    ##############

    def _is_consecutive(self, all_data, initial_data, new_id):
        """Computes if the given newsletter id is consecutive with those found in initial_data

        @param all_data: A list of all newsletter ids, ordered by their date
        @param initial_data: A list of newsletter ids that are already recorded as bounced
        @param new_id: The newsletter id which we need to find out if it's
                       consecutive to those in initial_data
        """
        x = all_data.index(initial_data[-1])
        y = all_data.index(new_id)
        return (y - x) == 1

    security.declareProtected("PNL External Service", "add_bounced_subscribers")
    def add_bounced_subscribers(self, bounced):
        """Adds bouncing statuses to subscribers.

        Called by xmlrpc and the manage_add_bounced_subscribers view
        """
        bounces = []
        rows = filter(None, bounced.split('\n'))
        for row in rows:
            newsletter, email = row.split('|')
            bounces.append((newsletter, email))

        catalog = self.get_subscribers_catalog()
        newsletters = [n.id for n in self.objectValues("Newsletter")]

        for (newsletter_id, email) in bounces:
            results = catalog.searchResults(email=email)
            if not results:
                continue
            subscriber = results[0].getObject()
            if base_hasattr(subscriber, 'bounces'):
                sb = subscriber.bounces
                if newsletter_id in sb:
                    continue    #the newsletter has already been marked as bounced
                if len(sb) == 0:
                    sb = [newsletter_id]
                elif self._is_consecutive(newsletters, sb, newsletter_id):
                    sb.append(newsletter_id)
                else:
                    sb = [newsletter_id]
            else:
                sb = [newsletter_id]

            subscriber.bounces = sb
            subscriber._p_changed = True
            catalog.reindexObject(subscriber)

        if self.automatic_cleanup:
            self.remove_subscribers()

    security.declarePrivate('remove_subscribers')
    def remove_subscribers(self):
        bouncers = self.get_bouncing_subscribers()
        count = len(bouncers)
        catalog = self.get_subscribers_catalog()
        results = catalog.searchResults()
        totalcount = len(results)
        if count >= totalcount:
            return 0

        addresses = []
        for s in bouncers:
            addresses.append(s.email)
            self.removeSubscriber(s)

        self.notifyRemoval(addresses)
        return count

    security.declarePrivate('get_bouncing_subscribers')
    def get_bouncing_subscribers(self):
        catalog = self.get_subscribers_catalog()
        results = catalog.searchResults(is_bouncing=True)
        return map(lambda o:o.getObject(), results)

    security.declarePrivate("get_subscribers_catalog")
    def get_subscribers_catalog(self):
        catalog = getattr(self, PG_CATALOG, None)
        if catalog is None:
            raise ValueError("Could not find the PloneGazette subscribers catalog")
        return catalog

    security.declarePublic('alreadySubscriber')
    def alreadySubscriber(self, email):
        """Checks wether email is in the subscribers
        """
        catalog = self._scatalog
        return not not catalog(email=email)

    security.declarePublic('sendmail')
    def sendmail(self, mailfrom, mailto, mailBody, subject = None):
        """"""
        from zope.sendmail.interfaces import IMailDelivery
        from zope.component import getUtility
        mail_host = getUtility(IMailDelivery, name='Mail')
        messageText, mto, mfrom = _mungeHeaders(mailBody, mailto, mailfrom,
                                subject, charset='utf-8', msg_type='text/html')
        mail_host.send(fromaddr=mfrom, toaddrs=mto, message=messageText)

    security.declarePublic('getRenderTemplate')
    def getRenderTemplate(self, recompile=0):
        """Returns the template that renders the HTML newsletter
        recompile=1 -> recompile TAL expression"""

        talEngine = Expressions.getEngine()
        try:
            dummy = self._v_renderTemplate
        except AttributeError, e:
            recompile = 1
        if recompile:
            if self.renderTemplate:
                self._v_renderTemplate = talEngine.compile(self.renderTemplate)
            else:
                self._v_renderTemplate = None
        if self._v_renderTemplate:
            data = {'here': self}
            template = self._v_renderTemplate(talEngine.getContext(data))
        else:
            template = getattr(self, 'newsletter_mua_formatter')
        return template

    security.declarePublic('getExtraRecipients')
    def getExtraRecipients(self, recompile=0):
        """Provides a TALES compiled extra list of recipients
        recompile=1 -> recompile TAL expression"""

        talEngine = Expressions.getEngine()
        try:
            dummy = self._v_extraRecipients
        except AttributeError, e:
            recompile = 1
        if recompile:
            # Not used since last cache extraction
            if self.extraRecipients:
                self._v_extraRecipients = talEngine.compile(self.extraRecipients)
            else:
                self._v_extraRecipients = None
        if self._v_extraRecipients:
            data = {'here': self}
            return self._v_extraRecipients(talEngine.getContext(data))()
        else:
            return []

    security.declareProtected(ChangeNewsletterTheme, 'mailingInfos')
    def mailingInfos(self):
        """Return mailing info from all subscribers"""

        subscribers = self.getSubscribers()
        mi = []
        for s in subscribers:
            if s.active:
                mi.append((s.email, s.format, s.getURL() + '/Subscriber_editForm'))
        return mi

    security.declarePrivate('_getStatsForSubscriber')
    def _getStatsForSubscriber(self, subscriber, stats, listing):
        """
        """
        format = subscriber.format
        active = subscriber.active
        if format == 'HTML':
            if active:
                stats['htmlactive'] += 1
            else:
                stats['htmlinactive'] += 1
        else:
            if active:
                stats['plaintextactive'] += 1
            else:
                stats['plaintextinactive'] += 1

        # getURL = brain
        url = getattr(subscriber, 'getURL', subscriber.absolute_url)()
        # the same dict is generated in newsletterbtree_view browser class, so change in this
        # dict has to be propagated to the newsletterbtree view class too.
        listing.append({'email' : subscriber.email, 'id':subscriber.id, 'url' : url, 'active' : active, 'format' : format})

        return (stats, listing)

    security.declareProtected(ChangeNewsletterTheme, 'subscriberStats')
    def subscriberStats(self):
        """Returns a dict with statistics about subscribers"""
        def checkfilter(subscriber, email, active, format):
            if email!='':
                emailOk = email in subscriber.email
            else:
                emailOk = True
            if active!=-1:
                activeOk = active==subscriber.active
            else:
                activeOk = True
            if format!='':
                formatOk = format in subscriber.format
            else:
                formatOk = True
            return emailOk and activeOk and formatOk


        listing = []
        stats = {'total': 0,
                 'htmlactive': 0,
                 'plaintextactive': 0,
                 'htmlinactive': 0,
                 'plaintextinactive': 0,
                 'totalhtml': 0,
                 'totalplaintext': 0,
                 'totalactive': 0,
                 'totalinactive': 0}

        filterEmail = self.REQUEST.get('email', '')
        filterActive = int(self.REQUEST.get('active', -1))
        filterFormat = self.REQUEST.get('format', '')

        subscribers = self.getSubscribers()
        stats['total'] = stats['total'] + len(subscribers)
        for subscriber in subscribers:
            if checkfilter(subscriber, filterEmail, filterActive, filterFormat):
                stats, listing = self._getStatsForSubscriber(subscriber, stats, listing)

        stats['totalhtml'] = stats['htmlactive'] + stats['htmlinactive']
        stats['totalplaintext'] = stats['plaintextactive'] + stats['plaintextinactive']
        stats['totalactive'] = stats['htmlactive'] + stats['plaintextactive']
        stats['totalinactive'] = stats['htmlinactive'] + stats['plaintextinactive']
        return (stats, listing)

    security.declareProtected(ChangeNewsletterTheme, 'extraRecipientStats')
    def extraRecipientStats(self):
        """Returns a dict with statistics about extra recipients"""
        extraRecipients = self.getExtraRecipients()
        stats = {'total': len(extraRecipients),
                 'html': 0,
                 'plaintext': 0}
        for mail, html, editurl in extraRecipients:
            if html:
                stats['html'] += 1
            else:
                stats['plaintext'] += 1
        return stats

    ############################
    ## portal_catalog support ##
    ############################

    security.declarePublic('SearchableText')
    def SearchableText(self):
        return self.title

    ##########################
    ## CSV import features
    #########################

    security.declareProtected(ChangeNewsletterTheme, 'createSubscribersFromCSV')
    def createSubscribersFromCSV(self, file_upload):
        """
        Create all subscribers objects from csv file uploaded
        """

        # Reset old log
        self._csv_import_log = ''

        filename = file_upload.filename
        filedatas = file_upload.read()
        var_directory = self.Control_Panel.getCLIENT_HOME()

        dialect = csv.excel

        # first, create a temp file on file system
        self._createTempFile(var_directory, filename, filedatas)

        # open temp csv file
        reader = csv.DictReader(open('%s/%s' % (var_directory, filename)), ['email', 'active', 'format'], dialect=dialect)

        # get target folder for subscribers object, or create it if not exist
        subscriber_folder = self.getSubscriberFolder()
        if subscriber_folder is None:
            self.invokeFactory('NewsletterBTree', 'subscribers')
            self.subscriber_folder_id = 'subscribers'
            subscriber_folder = getattr(self, 'subscribers')

        # remove headers
        first_row = reader.next()
        if first_row['email']!='email':
            return "You must add headers to the csv file : email, active, format ('email' at least)"


        # for each row, create a subscriber object
        default_format = self.default_format
        k = 0
        already_used = []
        not_valid = []
        for row in reader:

            # get the field value, or the default value
            if row['active']=='1':
                active = True
            elif row['active']=='0':
                active = False
            else:
                active = False

            if row['format']:
                if row['format'].lower()=='html':
                    format = 'HTML'
                elif row['format'].lower()=='text':
                    format = 'Text'
                else:
                    format = default_format
            else:
                format = default_format

            email = row['email']
            email = email.strip()

            # check mail address validity
            if not self.checkMailAddress(email):
                not_valid.append(email)
            else:
                # check if subscriber already exist
                if self.alreadySubscriber(email):
                    already_used.append(email)
                else:
                    newId = self._getRandomIdForSubscriber()
                    subscriber = self.createSubscriberObject(newId)

                    subscriber.edit(format=format, active=active, email=email)
                    k += 1
                    self._subscribersCount += 1

        # remove temp csv file
        os.remove('%s/%s' % (var_directory, filename))

        self._logCSVImportResult(not_valid, already_used)

        msg = ''
        if k:
            msg += '%s subcribers created. ' % str(k)
        if len(already_used):
            msg += '%s users were already subscriber on this newsletter theme. ' % len(already_used)

        if len(not_valid):
            msg += '%s emails were not valid. ' % len(not_valid)

        return msg

    security.declareProtected(ChangeNewsletterTheme, 'getCSVImportLogs')
    def getCSVImportLogs(self):
        """
        """
        return self._csv_import_log.strip()

    security.declarePrivate('_logCSVImportResult')
    def _logCSVImportResult(self, not_valid, already_used):
        """
        """
        result = ''
        if len(already_used):
            result += '<h2>Already subscribed</h2>'
            result += '<p>'
            result += '<br />'.join(already_used)
            result += '</p>'
        if len(not_valid):
            result += '<h2>Not valid emails</h2>'
            result += '<p>'
            result += '<br />'.join(not_valid)
            result += '</p>'
        self._csv_import_log = result
        return

    security.declarePrivate('_createTempFile')
    def _createTempFile(self, home, filename, filedatas):
        """
        Create a temp file inside zope "var" directory
        """
        temp_file = open('%s/%s' % (home, filename), 'w')
        temp_file.write(filedatas)
        temp_file.close()
        return

    # do not allow anonymous to list all subscribers
    security.declareProtected(ChangeNewsletterTheme, 'getSubscribers')
    def getSubscribers(self, full_objects=False):
        # get all items from catalog (all subscribers)
        cat = getattr(self, PG_CATALOG, None)
        if cat is None:
            return []
        result = cat()
        if full_objects:
            result = [x.getObject() for x in result]
        return result

    def _initCatalog(self):
        """Add subscribers catalog"""

        if not base_hasattr(self, PG_CATALOG):
            add_catalog = manage_addSubscribersCatalog
            add_catalog(self)

        catalog = getattr(self, PG_CATALOG)
        catalog.refreshCatalog()
        return catalog

    def __setstate__(self,state):
        """Updates"""
        NewsletterTheme.inheritedAttribute("__setstate__") (self, state)
        if not hasattr(self, 'utm_source'):
            self.utm_source = ''
        if not hasattr(self, 'utm_medium'):
            self.utm_medium = ''

# Class instanciation
InitializeClass(NewsletterTheme)
