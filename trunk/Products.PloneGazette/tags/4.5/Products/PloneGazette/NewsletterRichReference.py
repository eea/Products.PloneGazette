from AccessControl import ClassSecurityInfo
from OFS.PropertyManager import PropertyManager
from Products.ATReferenceBrowserWidget.ATReferenceBrowserWidget import ReferenceBrowserWidget
from Products.Archetypes.public import AttributeStorage
from Products.Archetypes.public import BaseContent
from Products.Archetypes.public import BaseSchema, Schema
from Products.Archetypes.public import ImageField, ImageWidget
from Products.Archetypes.public import ReferenceField
from Products.Archetypes.public import RichWidget
from Products.Archetypes.public import TextField
from Products.Archetypes.public import registerType
from Products.CMFCore.permissions import View
from Products.PloneGazette.config import PROJECTNAME


class NewsletterRichReference(BaseContent, PropertyManager):

    portal_type = meta_type = 'NewsletterRichReference'
    archetype_name = 'Newsletter RichReference'   #this name appears in the 'add' box

    security = ClassSecurityInfo()

    schema=BaseSchema  + Schema((
    TextField('text',
              default='',
              searchable=1,
              required=1,
              default_output_type = 'text/x-html-safe',
              widget=RichWidget(label='Text',
                                description='',
                                label_msgid='label_text',
                                description_msgid='help_text',
                                i18n_domain="plone")
                  ),
                                  
    ImageField(
        name='image',
        widget=ImageWidget(
            label_msgid="label_preview_image",
            description="This image is used as preview for the referenced objects.",
            description_msgid="help_image",
            label='Preview image',
            i18n_domain='plonegazette',
        ),
        storage=AttributeStorage(),
        sizes={'normal' :  (200, 130), }
    ),
                                                                    
    ReferenceField('references',
                    languageIndependent=1,
                    required=0,
                    allowed_types=(),
                    multiValued=1,
                    relationship='references',
                    widget=ReferenceBrowserWidget(label='References',
                                                  description='Select one or more remote objects',
                                                  label_msgid='label_references',
                                                  description_msgid='help_references',
                                                  i18n_domain='plonegazette',
                                                  allow_search=1,
                                                  allow_browse=1,
                                                  show_indexes=0,
                                                  ),
                ),
    ))

    # Make sure we get title-to-id generation when an object is created
    _at_rename_after_creation = True

    security.declarePublic('getObjects')
    def getObjects(self):
        """
        """
        return self.getReferences()


    security.declareProtected(View, 'imagetag')
    def imagetag(self, **kwargs):
        """Generate image tag using the api of the ImageField
        
        this method is needed because one must not access
        ImageField.tag in pagetemplates
        """
        if 'title' not in kwargs:
            kwargs['title'] = self.Title()
        return self.getField('image').tag(self, **kwargs)
    
    
    # uncommant lines below when you need
    factory_type_information={
        'allowed_content_types':[],
        'global_allow' : 0,
        'content_icon':'NewsletterReference.gif',
        'immediate_view':'newsletterreference_view',
        'filter_content_types' : 0
        }

    actions=({
        'id' : 'view',
        'name' : 'View',
        'category' : 'object',
        'action' : 'string:${object_url}/NewsletterRichReference_view',
        'permissions' : ('View',)
        },)

registerType(NewsletterRichReference, PROJECTNAME)
