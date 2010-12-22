## Controller Python Script "validate_newslettertheme_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=title='', testEmail='',authorEmail='', replyto='', activationMailSubject='', activationMailTemplate='', subscriber_folder_id=''
##parameters=title='', testEmail='',authorEmail='', replyto='', activationMailSubject='', activationMailTemplate='', subscriber_folder_id='', unsubscribeMailSubject='', unsubscribeMailTemplate='', confirmMailSubject='', confirmMailTemplate=''
##title=Validates a Newsletter Theme edit_form contents
##

translate = context.translate
required = translate('Input is required but no input given', domain='plonegazette')
not_valid_email = translate('This is not a valid mail address', domain='plonegazette')

if not title:
    state.setError('title', required)

if not testEmail:
    state.setError('testEmail', required)
else:
    if not context.checkMailAddress(testEmail.strip()):
        state.setError('testEmail', not_valid_email)

if not authorEmail:
    state.setError('authorEmail', required)
#else:
#    if not context.checkMailAddress(authorEmail.strip()):
#        state.setError('authorEmail', not_valid_email)

if replyto and not context.checkMailAddress(replyto.strip()):
    state.setError('replyto', not_valid_email)

if not activationMailSubject:
    state.setError('activationMailSubject', required)

if not activationMailTemplate:
    state.setError('activationMailTemplate', required)
else:
    errMsg = "This template must contain <b>%(url)s</b> and <b>%(email)s</b><br />"
    errMsg += " These key are needed to be replaced by the subscriber's preferences URL"
    errMsg += " and his e-mail address in the activation mail"
    template = activationMailTemplate
    if template.find('%(url)s') == -1 or template.find('%(email)') == -1:
        errMsg = translate(errMsg, domain='plonegazette')
        state.setError('activationMailTemplate', errMsg)

if not confirmMailSubject:
    state.setError('confirmMailSubject', required)

if not confirmMailTemplate:
    state.setError('confirmMailTemplate', required)
else:
    errMsg = "This template must contain <b>%(email)s</b> and <b>%(url)s</b><br />"
    errMsg += " The keys are needed to be replaced by the subscriber's"
    errMsg += " e-mail address nd the unsubscibe link in the confirm unsubscribe mail"
    template = confirmMailTemplate
    if template.find('%(email)') == -1:
        errMsg = translate(errMsg, domain='plonegazette')
        state.setError('confirmMailTemplate', errMsg)

if not unsubscribeMailSubject:
    state.setError('unsubscribeMailSubject', required)

if not unsubscribeMailTemplate:
    state.setError('unsubscribeMailTemplate', required)
else:
    errMsg = "This template must contain <b>%(email)s</b><br />"
    errMsg += " The key is needed to be replaced by the subscriber's"
    errMsg += " e-mail address in the unsubscribe mail"
    template = unsubscribeMailTemplate
    if template.find('%(email)') == -1:
        errMsg = translate(errMsg, domain='plonegazette')
        state.setError('unsubscribeMailTemplate', errMsg)

talExpressions = [(name, context.REQUEST[name].strip()) for name in ('renderTemplate', 'extraRecipients')]

context.checkTalExpressions(talExpressions, state=state)

if subscriber_folder_id and subscriber_folder_id not in context.objectIds('NewsletterBTree'):
    state.setError('subscriber_folder_id', translate('You must first create a large plone folder', domain='plonegazette'))

if state.getErrors():
    msg=context.safePortalMessage(translate('Please correct the indicated errors.', domain='plonegazette'))
    return state.set(status='failure', portal_status_message=msg)
else:
    return state
