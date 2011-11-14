## Script (Python) "NewsletterCentral_google"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters= utm_source='', utm_medium = ''
##title=Edit Google Analytics settings
##

translate = context.translate

context.edit_google(utm_source=utm_source,
		    utm_medium=utm_medium)

msg = context.safePortalMessage(translate('Newsletter Theme changes saved.', domain='plonegazette'))
return state.set(context=context, portal_status_message=msg)