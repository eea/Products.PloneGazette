Requirements for make it work under Plone 2.5
---------------------------------------------

Dependencies:

 - SecureMaildropHost ( http://svn.plone.org/svn/collective/SecureMaildropHost/tags/0.1 )
 - MaildropHost
 
 Due the fact emails are now generated as email.Message.Message instances and not strings
 is not working with SecureMailHost, you must/can use SecureMaildropHost.

 Don't forget to replace your ../plone-site/MailHost instance with a 'Secure Maildrop Host' one or just
 create a new 'Secure Maildrop Host' instance under your PloneGazette_ThemeCenter context.
 
 
Installation:

 Under "INSTANCE_HOME/etc" create "site.zcml" file:
 
 <configure xmlns="http://namespaces.zope.org/zope"
            xmlns:meta="http://namespaces.zope.org/meta"
	    xmlns:five="http://namespaces.zope.org/five">
                           
    <!-- Copy this file to your ``INSTANCE_HOME/etc`` directory -->

    <include package="Products.Five" />
    <meta:redefinePermission from="zope2.Public" to="zope.Public" />

    <include package="Products.GenericSetup" file="meta.zcml" />
    <include package="Products.PloneGazette" file="configure.zcml" />

    <five:loadProducts />
    <five:loadProductsOverrides />

 </configure>
 
If you have any questions contact Alec Ghica <alec.ghica@eaudeweb.ro> (alecghica on #eea or #edw).
