## Script (Python) "Newsletter_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=id='', title=None, description=None, text=None, dateEmitted=None, utm_campaign='', utm_term='', utm_content='', text_format=''
##title=Edit content and metadata
##
# 
if not id:
    id = context.getId()

new_context = context.portal_factory.doCreate(context, id)
new_context.edit(text_format=text_format,
                 text=text,
                 title=title,
                 dateEmitted=dateEmitted,
                 utm_campaign=utm_campaign,
                 utm_term=utm_term,
                 utm_content=utm_content)

new_context.plone_utils.contentEdit(new_context)

# contentEdit don't work for description as expected
new_context.setDescription(description)

# BBB PG 3.0. Replace with message factory and addPortalMessage
#statusMsg = _(u'Newsletter changes saved.')
#context.plone_utils.addPortalMessage(statusMsg, 'info')
translate = context.translate
statusMsg=context.safePortalMessage(translate('Newsletter changes saved.', domain='plonegazette'))
return state.set(context=new_context, portal_status_message=statusMsg)
