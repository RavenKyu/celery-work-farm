import logging
import redis

from celery_work_farm import app

logger = logging.getLogger(__name__)


@app.task(name='system.event.action.redis.messageq.publish',
          serializer='json', time_limit=20)
def action_redis_message_queue_publish(d):
    """
    :param d: ('smart-door', [{"ch":1}, ... ])
    :return:
    """
    try:
        if not d:
            return
        r = redis.Redis(host='redis', port=6379, db=0)
        key, values = d
        for v in values:
            r.publish(key, v)
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(str(e))
        return False
