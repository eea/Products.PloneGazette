from Acquisition import aq_inner
from Acquisition import aq_parent
from DateTime import DateTime
from Products.Five import BrowserView
import logging
import transaction

logger = logging.getLogger('PloneGazette')


class ManageInactiveSubscribers(BrowserView):
    """Page to delete Inactive Subscribers older than 7 days"""

    def __call__(self,):
        logger.info('Start subscribers cleanup')
        context = aq_inner(self.context)
        days = self.request.form.get('days', 7)
        days = int(days) * 24 * 3600

        # We need a deepcopy list of subscribers
        subscribers = list(context.getSubscribers())
        counter = 0
        now = int(DateTime())

        for subs in subscribers:
            age = now - int(subs.modified)
            if (age > days) and (not subs.active):
                subscriber = subs.getObject()
                counter += 1
                parent = aq_parent(subscriber)
                parent.manage_delObjects([subscriber.id])
                if (counter % 100) == 0:
                    logger.info("... deleted %s subscribers" % counter)
                    transaction.commit()

        msg = "Deleted %s inactive email subscribers" % counter
        logger.info(msg)

        return msg
