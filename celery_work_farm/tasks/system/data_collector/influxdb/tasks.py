import logging
from functools import wraps
from influxdb import InfluxDBClient
from celery_work_farm import app
from celery_work_farm.utils import GlobalValue

logger = logging.getLogger(__name__)

GLOBAL_VALUE = dict()


###############################################################################
class InfluxDBHandler:
    def __init__(self, host='influxdb', port=8086, database='test', *args, **kwargs):
        logger.info('influxdb-handler starts')
        self.client = InfluxDBClient(host=host, port=port, database=database)
        self.database = database
        if not self.client.ping():
            raise ConnectionError('Failed to connect to the InfluxDB.')

    # =========================================================================
    def __del__(self):
        if not hasattr(self, 'client'):
            return
        if self.client:
            self.client.close()

    # ==========================================================================
    def is_database_exists(self):
        try:
            next(d for d in self.client.get_list_database() if
                 # d['name'] == self.env['INFLUX_DB_DATABASE'])
                 d['name'] == self.database)
            return True
        except StopIteration:
            return False

    # =========================================================================
    def create_a_retention_policy(self):
        pass

    # =========================================================================
    def create_a_continuous_query(self, filed, name, database,
                                  target_rp_measurement, source_rp_measurement,
                                  _time, tags):

        """
        select_clause = 'SELECT mean(temperature) ' \
                                'INTO rp52w.temperature_mean_10m ' \
                                'FROM autogen.temperature ' \
                                'GROUP BY time(10m), sensorId'
        :param filed: temperature
        :param name: temperature_mean_10m
        :param database: dcim
        :param target_rp_measurement: rp52w.temperature_mean_10m
        :param source_rp_measurement: autogen.temperature
        :param _time: 10m
        :param tags: ["sensorId", ]
        :return:
        """
        select_clause = f'SELECT mean({filed}) AS {filed} ' \
                        f'INTO {target_rp_measurement} ' \
                        f'FROM {source_rp_measurement} ' \
                        f'GROUP BY time({_time}), {", ".join(tags)}'

        self.client.create_continuous_query(
            name=name,
            select=select_clause,
            database=database)

    # =========================================================================
    def create_db(self):
        @wraps(self)
        def func(*args, **kwargs):
            this = args[0]
            if not this.is_database_exists():
                this.client.create_database(this.database)
            self(*args, **kwargs)

        return func

    # =========================================================================
    @create_db
    def insert(self, d, *args, **kwargs):
        logger.debug(f'insert data into influxdb: {d}')
        self.client.write_points(d, )
        return True


###############################################################################
def make_template_data(d, template):
    dt = d['datetime']
    data = d['data']
    lst = list()
    for key in template:
        value = data[key]['value']
        if value is None:
            # self.logger.warning(
            #     f"No value for {key}. "
            #     f"It might not collect data from the sensor yet.")
            continue
        t = template[key]
        d = dict()

        fields = dict()
        fields[t['fields']] = value
        d['measurement'] = t['measurement']
        d['tags'] = dict()
        if not t['tags']:
            t['tags'] = []
        for tag in t['tags']:
            d['tags'].update(tag)
        d['fields'] = fields
        d['time'] = dt
        lst.append(d)
    logger.debug(f'converted value: {d}')
    return lst


###############################################################################
@app.task(name='db.influxdb.insert', serializer='json', time_limit=20)
def influxdb_insert(d, host, port, database, template):
    try:
        c = InfluxDBHandler(host=host, port=port, database=database)
        d = make_template_data(d, template)
        c.insert(d)
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(str(e))
    return


###############################################################################
def remove_time(d):
    last = list()
    for x in d:
        y = dict()
        for k, v in x.items():
            if k == 'time':
                continue
            y[k] = v
        last.append(y)
    return last


###############################################################################
def shared_keyvals(dict1, dict2):
    return dict( (key, dict1[key])
                 for key in (set(dict1) - set(dict2))
                 if dict1[key] == dict2[key])


###############################################################################
@app.task(name='db.influxdb.insert_only_changed_value_case',
          serializer='json', time_limit=20)
def influxdb_insert_insert_only_changed_value_case(
        d, host, port, database,  gv_name, template):
    """
    이전 데이터와 비교하여 변경된 데이터만 찾아서 삽입
    :param d:
    :param host:
    :param port:
    :param database:
    :param gv_name:
    :param template:
    :return:
    """
    try:
        g = GlobalValue('redis', 6379, 0, 'changed_value_case', gv_name)
        c = InfluxDBHandler(host=host, port=port, database=database)
        d = make_template_data(d, template)

        # if this is the first time or celery restarted,
        # no last data to compare with current one.
        if b'data' not in g.keys():
            # g.set_value('data', last)
            c.insert(d)
            d = remove_time(d)
            g.set_value('data', d)
            return

        # It forces to update all of data for every set interval.
        data = list()
        global_value = g.get_value('data')

        if not d:
            logging.error('The received data is empty.')
            return

        if 'time' not in d[0]:
            logging.error('The key, `time` is not in the received data.')
            return

        dt = d[0]['time']
        current = remove_time(d)
        global_value = remove_time(global_value)
        for v in current:
            if v not in global_value:
                v['time'] = dt
                data.append(v)
        if not data:
            return

        c.insert(data)
        logging.info('Some of the status were changed.')
        g.set_value('data', current)

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(str(e))
    finally:
        del g
    return
