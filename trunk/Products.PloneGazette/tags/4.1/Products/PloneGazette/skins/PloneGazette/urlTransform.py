## Script (Python) "urlTransform"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=text
##title=
# replace relative urls by absolute_urls inside newsletter email body

restrictedTraverse = context.restrictedTraverse

# Get links to replace
links = []
lst = text.split('href="')
if len(lst) > 1:
    for item in lst:
        url = item.split('"')
        if len(url) > 1:
            url = url[0]
            # keep only relative urls
            if url[:7] != 'http://':
                links.append(url)

# Get image links to replace
lst = text.split('src="')
if len(lst) > 1:
    for item in lst:
        url = item.split('"')
        if len(url) > 1:
            url = url[0]
            # keep only relative urls
            if url[:7] != 'http://':
                links.append(url)

# transform urls
new_text = text
for item in links:
    obj = restrictedTraverse(item, None)
    if obj:
        new_link = obj.absolute_url()
        new_text = new_text.replace('href="%s"' % item, 'href="%s"' % new_link)
        new_text = new_text.replace('src="%s"' % item, 'src="%s"' % new_link)

return new_text
                                                                                                                                                                




