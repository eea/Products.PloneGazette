#
# $Id$
#

"""Newsletter class"""

from AccessControl import ClassSecurityInfo
from AccessControl.SpecialUsers import nobody
from AccessControl.requestmethod import postonly
from DateTime import DateTime
from DocumentTemplate.DT_Util import html_quote
from App.class_init import InitializeClass
from OFS import Folder
from PNLBase import PNLContentBase
from PNLPermissions import ChangeNewsletter
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFDefault.SkinnedFolder import SkinnedFolder
from Products.CMFPlone.PloneFolder import OrderedContainer
from Products.CMFPlone.utils import safe_unicode
from elementtree import ElementTree, HTMLTreeBuilder
from email.Header import Header
from urlparse import urlparse
from zope.i18n import translate
from zope.structuredtext.html import HTML as format_stx
import StringIO
import cStringIO
import email.Message
import logging
import re
import traceback
import transaction
from zope.component import adapts

#try:
    #from StructuredText.StructuredText import HTML as format_stx
#except:
    #from Products.CMFCore.utils import format_stx

#try:
    #from OFS.IOrderSupport import IOrderedContainer as IZopeOrderedContainer
    #hasZopeOrderedSupport=1
#except ImportError:
    #hasZopeOrderedSupport=0

# Additional imports for converting relative to absolute links

logger = logging.getLogger('PloneGazette')

#################
## The factory ##
#################

def addNewsletter(self, id, title = '', relatedItem = None, REQUEST = {}):
    """
    Factory method for a Newsletter object
    """
    obj = Newsletter(id, title, relatedItem=relatedItem)
    self._setObject(id, obj)
    getattr(self, id)._post_init()
    if REQUEST.has_key('RESPONSE'):
        return REQUEST.RESPONSE.redirect(self.absolute_url() + '/manage_main')

#################################
## The Newsletter content type ##
#################################

lynx_file_url = re.compile(r'file://localhost[^%]+%\(url\)s')

class Newsletter(SkinnedFolder, OrderedContainer, DefaultDublinCoreImpl, PNLContentBase):
    """Newsletter class"""

    ########################################
    ## Registration info for portal_types ##
    ########################################
    factory_type_information = {
        'id': 'Newsletter',
        'portal_type': 'Newsletter',
        'meta_type': 'Newsletter',
        'description': 'A newletter (has no sense oudside a NewsletterTheme object)',
        'content_icon': 'Newsletter.gif',
        'product': 'PloneGazette',
        'factory': 'addNewsletter',
        'immediate_view': 'folder_listing',
        'global_allow': 0,
        'filter_content_types': 1,
        'allowed_content_types': ('Section', 'Topic', 'NewsletterReference', 'NewsletterRichReference'),
        'actions': (
            {
                'id': 'view',
                'name': 'View',
                'action': 'string:${object_url}/Newsletter_view',
                'permissions': (View, ),
                'category': 'object'
                },
            {
                'id': 'edit',
                'name': 'Edit',
                'action': 'string:${object_url}/Newsletter_editForm',
                'permissions': (ChangeNewsletter,),
                'category': 'object'
                },
            {
                'id': 'test',
                'name': 'Test',
                'action': 'string:${object_url}/Newsletter_testForm',
                'permissions': (ChangeNewsletter,),
                'category': 'object'
                },

            {
                'id': 'send',
                'name': 'Send',
                'action': 'string:${object_url}/Newsletter_sendForm',
                'permissions': (ChangeNewsletter,),
                'category': 'object'
                },
            ),
            'aliases' : {
                '(Default)'  : 'Newsletter_view',
                'view'       : 'Newsletter_view',
                'index.html' : '',
                'edit'       : 'base_edit',
                'properties' : 'base_metadata',
                'sharing'    : 'folder_localrole_form',
            },
        }

    ###########################
    ## Basic class behaviour ##
    ###########################

    meta_type = factory_type_information['meta_type']
    manage_options = Folder.Folder.manage_options

    # Standard security settings
    security = ClassSecurityInfo()
    security.declareObjectProtected(View)
    #security.declareProtected(ChangeNewsletter, "dummyMethod_editPermission")

    _stx_level = 1
    cooked_text = text = text_format = ''
    _new_object = False
    _dynamic_content = None

    # Init method
    security.declarePrivate('__init__')
    def __init__(self, id, title='', description='', text_format='', text='',
                 dateEmitted=None, relatedItem=None, utm_campaign='', utm_term='', utm_content=''):
        """__init__(self, id, title='')"""

        DefaultDublinCoreImpl.__init__(self)
        self.id = id
        self.title = title
        self.description = description
        self._edit(text=text, text_format=text_format)
        self.setFormat(text_format)
        self.dateEmitted = dateEmitted
        self._new_object=True
        self._dynamic_content = None
        self.relatedItem = relatedItem
        self.utm_campaign = id
        self.utm_term = ''
        self.utm_content = ''
        return

    security.declarePrivate('_post_init')
    def _post_init(self):
        """
        _post_init(self) => Post-init method (that is, method that is called AFTER the class has been set into the ZODB)
        """

        self.indexObject()
        return

    #############################
    ## Content editing methods ##
    #############################

    def _edit(self, text, text_format=''):
        """
        """
        level = self._stx_level
        if not text_format:
            text_format = self.text_format

        if self.text_format:
            self.text_format = text_format
        if text_format == 'html':
            self.text = self.cooked_text = text
        elif text_format == 'plain':
            self.text = text
            self.cooked_text = html_quote(text).replace('\n', '<br />')
        else:
            self.cooked_text = format_stx(text=text, level=level)
            self.text = text

    # Edit method (change this to suit your needs)
    # This edit method should only change attributes that are neither 'id' or metadatas.
    security.declareProtected(ChangeNewsletter, 'edit')
    def edit(self, title='', text='', dateEmitted=None, text_format='', utm_campaign='', utm_term='', utm_content=''):
        """
        edit(self, text = '') => object modification method
        """
        level = self._stx_level
        # Change attributes
        if title:
            self.title = title
        if not dateEmitted:
            # if dateEmitted is cleared, clear dynamic content attribute
            # to render newsletter again
            self._dynamic_content = None
        else:
            try:
                self.dateEmitted = DateTime(dateEmitted)
            except:
                self.dateEmitted = None

        self.setFormat(text_format)
        self._edit(text=text, text_format=text_format)

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
        self.utm_campaign = utm_campaign
        self.utm_term = utm_term
        self.utm_content = utm_content

        # Reindex
        self.reindexObject()
        return

    security.declareProtected(View, 'CookedBody')
    def CookedBody(self, stx_level=None, setLevel=0):
        """
        """
        if (self.text_format == 'html' or self.text_format == 'plain'
            or (stx_level is None)
            or (stx_level == self._stx_level)):
            return self.cooked_text
        else:
            cooked = format_stx(self.text, stx_level)
            if setLevel:
                self._stx_level = stx_level
                self.cooked_text = cooked
            return cooked

    security.declareProtected(View, 'Format')
    def Format(self):
        """
        """
        if self.text_format == 'html':
            return 'text/html'
        else:
            return 'text/plain'

    security.declareProtected(ModifyPortalContent, 'setFormat')
    def setFormat(self, format):
        """
        """
        value = str(format)
        if value == 'text/html' or value == 'html':
            self.text_format = 'html'
        elif value == 'text/plain':
            if self.text_format not in ('structured-text', 'plain'):
                self.text_format = 'structured-text'
        elif value =='plain':
            self.text_format = 'plain'
        else:
            self.text_format = 'structured-text'

    ############################
    ## portal_catalog support ##
    ############################

    security.declareProtected(View, 'SearchableText')
    def SearchableText(self):
        "Returns a concatination of all searchable text"

        ret="%s %s %s" % (self.Title(),
                          self.Description(),
                          self.text)
        return ret


    ###################
    security.declarePrivate('changeRelativeToAbsolute')
    def changeRelativeToAbsolute(self, text):
        """
            Kupu, TinyMCE and other editors insert relative URLS for links, images and anchors in content.
            Those links don't work in certain mailclients. This is where this method comes in.
            This changes relative links to absolute ones, without base-tags, because that doesn't work
            in all mailclients.
        """
        tree = HTMLTreeBuilder.TreeBuilder(encoding='utf-8')

        # add a root node for the parser
        tree.feed('<div>%s</div>' % text)
        rootnode = tree.close()

        # add /view to current_url so all links are correct
        current_url = "%s/view" % self.absolute_url()
        parsed_url = urlparse(current_url)

        for x in rootnode.getiterator():
            current_keys = x.keys()
            # fix links and anchors
            if x.tag == "a":
                if "href" in current_keys and "class" in current_keys:
                    if x.attrib['class'] == "internal-link":
                        href = x.attrib['href']
                        relative_part = "/".join(parsed_url[2].split('/')[0:(len(parsed_url[2].split('/'))-len(href.split("../")))])
                        x.attrib['href'] = "%s://%s%s/%s" % (parsed_url[0], parsed_url[1], relative_part, href.split("../")[-1])

                elif "href" in current_keys:
                    # plone 2.5 uses .# for anchors, so we replace this with #
                    if ".#" in x.attrib['href']:
                        x.attrib['href'] = x.attrib['href'].replace('.#','#')

            # fix images
            elif x.tag == "img":
                if "src" in current_keys:
                    src = x.attrib['src']

                    # fix only relative links
                    if src.find('http://') != 0:
                        relative_part = "/".join(parsed_url[2].split('/')[0:(len(parsed_url[2].split('/'))-len(src.split("../")))])
                        x.attrib['src'] = "%s://%s%s/%s" % (parsed_url[0], parsed_url[1], relative_part, src.split("../")[-1])

        tree = ElementTree.ElementTree(rootnode);
        output = StringIO.StringIO()
        tree.write(output)
        text = output.getvalue()
        output.close()

        return text

    security.declarePublic('renderTextHTML')
    def renderTextHTML(self, html=True, force=False, footer_url=None, REQUEST=None):
        """Makes the HTML part for MUA of the newsletter
        """
        theme = self.getTheme()

        # newsletter footer
        template = theme.getRenderTemplate()
        newsletterFooter = theme.newsletterFooter
        if '%(url)s' in newsletterFooter and footer_url is not None:
            newsletterFooter = newsletterFooter.replace('%(url)s', footer_url)

        # fix relative links
        text = self.changeRelativeToAbsolute(self.cooked_text)

        newsletter_body = text
        newsletter_descr = self.description
        newsletter_title = self.title

        # related item
        if self.hasExternalRelation() and self.checkRelated():
            rel_obj = self.getRelatedObject()
            newsletter_body = '<br /><a href="%s" title="Read more">Read more ...</a>' % rel_obj.absolute_url()
            newsletter_descr = rel_obj.Description()
            newsletter_title = rel_obj.Title()

        # google analytics
        ga_query = ''
        if len(self.utm_campaign) > 0:
            ga_query += '&utm_campaign=%s' % self.utm_campaign
        if len(theme.utm_medium) > 0:
            ga_query += '&utm_medium=%s' % theme.utm_medium
        if len(self.utm_term) > 0:
            ga_query += '&utm_term=%s' % self.utm_term
        if len(self.utm_content) > 0:
            ga_query += '&utm_content=%s' % self.utm_content
        if len(theme.utm_source) > 0:
            ga_query += '&utm_source=%s' % theme.utm_source

        tagregexp = "(?i)<a((\s+\w+(\s*=\s*(?:\".*?\"|'.*?'|[^'\">\s]+))?)+\s*|\s*)\/?>"
        urlregexp = "(?i)\s+href=\".+?\""
        for match in re.finditer(tagregexp, newsletter_body):
            tagmatch = match.group()
            for submatch in re.finditer(urlregexp, tagmatch):
                orighrefmatch = submatch.group()
                hrefmatch = orighrefmatch[:len(orighrefmatch)-1]
                if hrefmatch.find('?') == -1: hrefmatch += '?'
                hrefmatch += ga_query + '"'
                newsletter_body = newsletter_body.replace(orighrefmatch, hrefmatch)

        # generate preview
        data = template(id=self.id,
                        body=newsletter_body,
                        description=newsletter_descr,
                        newsletterFooter=newsletterFooter,
                        html=html,
                        title=newsletter_title,
                        date=self.dateEmitted,
                        force=force)

        data = safe_unicode(data)

        if theme.alternative_portal_url:
            portal_url = getToolByName(self, 'portal_url')()
            data = data.replace(portal_url, theme.alternative_portal_url)

        if REQUEST is not None:
            # Called directly from the web; set content-type
            # The publisher will then re-encode for us
            REQUEST.RESPONSE.setHeader('content-type',
                                       'text/html; charset=%s' %
                                       self.ploneCharset())

        return data




    security.declarePublic('renderTextPlain')
    def renderTextPlain(self, force=False, footer_url=None, REQUEST=None):
        """Makes the text/plain part for MUA of the newsletter"""

        html = self.renderTextHTML(html=False, force=force, footer_url=footer_url)

        # portal_tranforms (at least lynx transform) requires encoded data
        html = html.encode('utf8') # encodes everything, good enough
        transform_tool = getToolByName(self, 'portal_transforms')
        text = transform_tool.convertToData('text/plain', html)

#        # Convert to text/html, preferring lynx_dump if available
#        transform_tool = getToolByName(self, 'portal_transforms')
#        lynxAvailable = (
#            'lynx_dump' in transform_tool.objectIds() and
#            transform_tool.lynx_dump.title != 'BROKEN')
#        if lynxAvailable:
#            # Hackery ahead! We'll tell lynx what encodings to use
#            # TODO: fix portal_transforms to deal with encodings
#            if not hasattr(transform_tool.lynx_dump, '_v_transform'):
#                transform_tool.lynx_dump._load_transform()
#            transform = transform_tool.lynx_dump._v_transform
#            oldargs = transform.binaryArgs
#            transform.binaryArgs += ' -assume_charset=utf8'
#            transform.binaryArgs += ' -display_charset=utf8'
#
#            text = transform_tool('lynx_dump', html)
#
#            transform.binaryArgs = oldargs
#
#            if footer_url is None:
#                # fixup URL references
#                text = lynx_file_url.sub('%(url)s', text)
#        else:
#            text = transform_tool.convertToData('text/plain', html)

        if REQUEST is not None:
            # called directly from the web; set content-type
            # The publisher will then re-encode for us
            REQUEST.RESPONSE.setHeader('Content-Type',
                                       'text/plain; charset=%s' %
                                       self.ploneCharset())

        return safe_unicode(text)

    security.declarePublic('renderTextHTMLEncoded')
    def renderTextHTMLEncoded(self, html=True, force=False, footer_url=None, REQUEST=None):
        return self.renderTextHTML(html=html, force=force, footer_url=footer_url, REQUEST=REQUEST).encode(self.ploneCharset())

    security.declarePublic('renderTextPlainEncoded')
    def renderTextPlainEncoded(self, html=True, force=False, footer_url=None, REQUEST=None):
        return self.renderTextPlain(html=html, force=force, footer_url=footer_url, REQUEST=REQUEST).encode(self.ploneCharset())


    security.declareProtected(ChangeNewsletter, 'testSendToMe')
    def testSendToMe(self, REQUEST=None):
        """Sends HTML/mixed and plain text newsletter to the author"""
        if REQUEST is None:
            REQUEST = self.REQUEST
        theme = self.getTheme()
        testemail = theme.testEmail
        editurl = theme.absolute_url() + '/xxx'

        # We want to test the unsubscribe url too and we asume the test subscriber is locade in the theme
        for subscriber in theme.objectValues('Subscriber'):
            if subscriber.Title() == testemail:
                si = subscriber.mailingInfo()
                # si is None if user is inactive
                if si is not None:
                    editurl = si[2]
                break;

        recipients = [(testemail, 'HTML', editurl), (testemail, 'Text', editurl)]
        # force fresh rendering of the template - do not use dynamic content stored in instance.
        errors = self.sendToRecipients(recipients, force=True)
        return self.Newsletter_testForm(errors=errors, sent=1)

    ########################
    ## Sending newsletter ##
    ########################

    def sendBeginSendNotification(self):
        theme = self.getTheme()
        charset = theme.ploneCharset()

        mailto   = theme.testEmail
        mailfrom = theme.authorEmail
        subject  = "Newsletter delivery started"

        body = """The following newsletter has started the message delivery process:
            %s
            %s
            """ % (self.Title(), self.absolute_url())

        msg                 = email.Message.Message()
        msg['To']           = mailto
        msg['From']         = mailfrom
        msg['Subject']      = subject
        msg["Date"]         = email.Utils.formatdate(localtime = 1)
        msg["Message-ID"]   = email.Utils.make_msgid()
        msg["Mime-version"] = "1.0"

        msg["Content-type"]="text/plain"
        msg.set_payload(body, 'utf-8')

        theme.sendmail(mailfrom, (mailto), msg, subject=subject)

    def sendEndSendNotification(self):
        theme = self.getTheme()
        charset = theme.ploneCharset()

        mailto   = theme.testEmail
        mailfrom = theme.authorEmail
        subject  = "Newsletter delivery completed"

        body = """The following newsletter has finished the message delivery process:
            %s
            %s
            """ % (self.Title(), self.absolute_url())

        msg                 = email.Message.Message()
        msg['To']           = mailto
        msg['From']         = mailfrom
        msg['Subject']      = subject
        msg["Date"]         = email.Utils.formatdate(localtime = 1)
        msg["Message-ID"]   = email.Utils.make_msgid()
        msg["Mime-version"] = "1.0"

        msg["Content-type"]="text/plain"
        msg.set_payload(body, 'utf-8')

        theme.sendmail(mailfrom, (mailto), msg, subject=subject)

    security.declareProtected(ChangeNewsletter, 'sendToRecipients')
    def sendToRecipients(self, recipients, force=False):
        """Send the newsletter to a list of recipients

        switched to email.Message.Message
        recipients is a list of tuples in the form:
        [(email, format, editurl),...]
        email is the mail address
        format is 'HTML' to receive HTML/mixed mail
        editurl is the user preference URL"""

        htmlTpl = self.renderTextHTML(force=force)
        hasurl = '%(url)s' in htmlTpl
        plaintextTpl = self.renderTextPlain(force=force)
        theme = self.getTheme()
        verp_prefix = theme.verp_prefix
        mailFrom = theme.authorEmail
        charset = self.ploneCharset()
        errors = []

        mailMethod = theme.sendmail

        # related item
        if self.hasExternalRelation() and self.checkRelated():
            titleForMessage = safe_unicode(self.getRelatedObject().Title())
        else:
            titleForMessage = safe_unicode(self.title)

        titleForMessage = Header(titleForMessage, header_name='Subject',
                                 charset=charset)
        portal_url = getToolByName(self, 'portal_url')()

        self.sendBeginSendNotification()

        for mailTo, format, editurl in recipients:
            if theme.alternative_portal_url:
                editurl = editurl.replace(portal_url,
                                          theme.alternative_portal_url)
            mainMsg         = email.Message.Message()
            mainMsg["To"]   = mailTo
            mainMsg["From"] = mailFrom
            mainMsg["Subject"]      = titleForMessage
            mainMsg["Date"]         = email.Utils.formatdate(localtime = 1)
            mainMsg["Message-ID"]   = email.Utils.make_msgid()
            mainMsg["Mime-version"] = "1.0"

            #deactivated because EEA mailserver can't handle it
            #mainMsg['Return-Path']=make_verp(mailTo, self.id, verp_prefix)

            if format == 'HTML':
                new_htmlTpl = htmlTpl
                if hasurl:
                    new_htmlTpl = new_htmlTpl.replace('%(url)s', editurl)

                new_plaintextTpl = plaintextTpl
                if hasurl:
                    new_plaintextTpl = new_plaintextTpl.replace('%(url)s', editurl)
                mainMsg["Content-type"]="multipart/alternative"
                #mainMsg.preamble="This is the preamble.\n"
                mainMsg.epilogue="\n" # To ensure that message ends with newline

                # plain
                secondSubMsg=email.Message.Message()
                secondSubMsg.add_header("Content-Type", "text/plain", charset= charset)
                secondSubMsg["Content-Disposition"]="inline"
                secondSubMsg.set_payload(safe_unicode(new_plaintextTpl).encode(charset), charset)
                mainMsg.attach(secondSubMsg)
                # html
                subMsg=email.Message.Message()
                subMsg.add_header("Content-Type", "text/html", charset= charset)
                subMsg["Content-Disposition"]="inline"
                subMsg.set_payload(safe_unicode(new_htmlTpl).encode(charset), charset)
                mainMsg.attach(subMsg)
            else:
                new_plaintextTpl = plaintextTpl
                if hasurl:
                    new_plaintextTpl = new_plaintextTpl.replace('%(url)s', editurl)
                mainMsg["Content-type"]="text/plain"
                mainMsg.set_payload(safe_unicode(new_plaintextTpl).encode(charset), charset)
                mainMsg.epilogue="\n" # To ensure that message ends with newline

            try:
                mailMethod(mailFrom, (mailTo,), mainMsg)
            except Exception,e:
                errors.append(mailTo)
                tbfile = cStringIO.StringIO()
                traceback.print_exc(file=tbfile)
                logger.warning('Error when sending to %s\n%s' % (mailTo, tbfile.getvalue()))
                tbfile.close()

        self.sendEndSendNotification()

        return errors

    security.declareProtected(ChangeNewsletter, 'sendToSubscribers')
    @postonly
    def sendToSubscribers(self, REQUEST=None):
        """Sends that newsletter to all subscribers and extra recipients"""
        self.sent_status = True
        transaction.commit()

        theme = self.getTheme()
        set_recipients_mailingInfos = set(theme.mailingInfos())
        # we are sending to all recipients. Render dynamic content and store it persistently
        self._dynamic_content=self.render_dynamic_content(html=True)
#        errors1 = self.sendToRecipients(recipients)
        set_recipients_extraRecipients = theme.getExtraRecipients()
        errors = self.sendToRecipients(list(set_recipients_mailingInfos.union(set_recipients_extraRecipients)))
        self.dateEmitted = DateTime()
        if REQUEST is not None:
            if errors:
                statusMsg = translate(u'SMTP server related errors', domain='plonegazette') ##!: display recipient
            else:
                statusMsg = translate(u'The newsletter has been sent.', domain='plonegazette')
            self.plone_utils.addPortalMessage(statusMsg)
            return self.Newsletter_sendForm(errors=errors)
        else:
            return errors

    security.declarePublic("getSendStatus")
    def getSendStatus(self):
        """returns the newsletter sent status"""
        status = getattr(self, "sent_status", False)
        return status and "OK" or "NO"

    ###############
    ## Utilities ##
    ###############

    security.declarePublic('getObjects')
    def getObjects(self):
        """
        """
        hasPermission = nobody.has_permission
        objects = [object for object in self.objectValues(('Section','NewsletterTopic', 'NewsletterReference', 'NewsletterRichReference')) if hasPermission('View', object)]
        objects.sort(lambda a,b:cmp(self.getObjectPosition(a.getId()), self.getObjectPosition(b.getId())))
        return objects

    security.declareProtected(View, 'renderedDynamicContent')
    def renderedDynamicContent(self, force=False):
        if force:
            return None
        else:
            return self._dynamic_content

    ##################
    ## Related item ##
    ##################

    def getRelatedItem(self):
        """ """
        return getattr(self, 'relatedItem', '')

    def hasExternalRelation(self):
        """ check if newsletter has an external reference """
        return self.getRelatedItem()

    def getRelatedObject(self):
        """ returns the related object """
        related = None
        cat = getToolByName(self, 'uid_catalog')
        res = cat.searchResults(UID = self.getRelatedItem())
        for obj in res: related = obj.getObject()
        return related

    def checkRelated(self):
        """ check if the related object still exist """
        cat = getToolByName(self, 'uid_catalog')
        res = cat.searchResults(UID = self.getRelatedItem())
        return len(res)

    def __setstate__(self,state):
        """Updates"""
        Newsletter.inheritedAttribute("__setstate__") (self, state)
        if not hasattr(self, 'utm_campaign'):
            self.utm_campaign = ''
        if not hasattr(self, 'utm_term'):
            self.utm_term = ''
        if not hasattr(self, 'utm_content'):
            self.utm_content = ''


# Class instanciation
InitializeClass(Newsletter)


def make_verp(to, newsletter_id, prefix):
    """Creates a unique VERP return path for an email address"""

    to = to.replace("@", "=")
    return u"%s-%s-%s" % (prefix, newsletter_id, to)

