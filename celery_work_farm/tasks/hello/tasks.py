import logging
from celery_work_farm import app

logger = logging.getLogger(__name__)


###############################################################################
@app.task(name='hello', serializer='json', time_limit=20)
def hello(a, b, c):
    logger.info('hello')
    return [a, b, c]


