""" Tests setup
"""
from Products.PloneTestCase import PloneTestCase
from Products.PloneTestCase.layer import onsetup
from Products.Five import zcml
from Products.Five import fiveconfigure

PRODUCTS = ['FiveSite', 'Products.PloneGazette']

@onsetup
def setup_plonegazette():
    """ Setup
    """
    fiveconfigure.debug_mode = True
    import Products.Five
    import Products.FiveSite
    import Products.PloneGazette
    zcml.load_config('meta.zcml', Products.Five)
    zcml.load_config('configure.zcml', Products.Five)
    zcml.load_config('configure.zcml', Products.FiveSite)
    zcml.load_config('configure.zcml', Products.PloneGazette)
    fiveconfigure.debug_mode = False

    PloneTestCase.installProduct('Five')
    for i in PRODUCTS:
        PloneTestCase.installProduct(i)

setup_plonegazette()
PloneTestCase.setupPloneSite(products=PRODUCTS)


class PloneGazetteFunctionalTestCase(PloneTestCase.FunctionalTestCase):
    """ Functional test case
    """
