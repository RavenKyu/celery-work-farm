import re
import json
from datetime import timedelta
from redis import StrictRedis



def convert_to_seconds(s):
    """
    # string time to
    >>> convert_to_seconds('1h')
    86400
    >>> convert_to_seconds('1m1s')
    601

    :param s:
    :return:
    """
    units = {
        's': 'seconds',
        'm': 'minutes',
        'h': 'hours',
        'd': 'days',
        'w': 'weeks',
    }
    return int(timedelta(**{
        units.get(m.group('unit').lower(), 'seconds'): int(m.group('val'))
        for m in re.finditer(r'(?P<val>\d+)(?P<unit>[smhdw]?)', s, flags=re.I)
    }).total_seconds())


class GlobalValue:
    def __init__(self, host: str, port: int, db: int,
                 func_name: str, gv_name: str):
        self.name = f'{__file__}:{func_name}:{gv_name}'
        self.c = StrictRedis(host=host, port=port, db=db)
        self.c.ping()

    def __del__(self):
        try:
            self.c.ping()
            self.c.close()
        except Exception:
            pass

    def get_value(self, key):
        value = self.c.hget(self.name, key)
        return json.loads(value)

    def set_value(self, key, value):
        value = json.dumps(value)
        self.c.hset(self.name, key, value)

    def keys(self):
        return self.c.hkeys(self.name)
