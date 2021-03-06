import pandas as pd
from datetime import date

from os import sys, path
root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    import config
    from Utiltity.common import *
    from Utiltity.time_utility import *
    from Collector.CollectorUtility import *
except Exception as e:
    sys.path.append(root_path)

    import config
    from Utiltity.common import *
    from Utiltity.time_utility import *
    from Collector.CollectorUtility import *
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_name': 'dummy_plugin_for_test',
        'plugin_version': '0.0.0.1',
        'tags': ['test', 'dummy', 'collector']
    }


def plugin_adapt(uri: str) -> bool:
    return uri.startswith('test.')


def plugin_capacities() -> list:
    return [
        'test.*',
    ]


# ----------------------------------------------------------------------------------------------------------------------

def __execute_test_entry1(**kwargs) -> pd.DataFrame:
    identify = kwargs.get('identify')
    time_serial = kwargs.get('datetime')

    since, until = normalize_time_serial(time_serial, days_ago(30), today())
    df = pd.DataFrame(columns=['datetime', 'field_01', 'field_02', 'field_03'])

    index = 0
    current = since
    while current < until:
        df = df.append({
            'datetime': date2text(current),
            'field_01': 10000.0 * index,
            'field_02': -100 * index,
            'field_03': 'column' + str(index)
        }, ignore_index=True)
        index += 1
        current += datetime.timedelta(days=1)
    return df.assign(identify=identify)


def __execute_test_entry2(**kwargs):
    pass


# ----------------------------------------------------------------------------------------------------------------------

def query(**kwargs) -> pd.DataFrame or None:
    uri = kwargs.get('uri')
    if uri == 'test.entry1':
        return __execute_test_entry1(**kwargs)
    elif uri == 'test.entry2':
        return __execute_test_entry2(**kwargs)
    else:
        return None


def validate(**kwargs) -> bool:
    nop(kwargs)
    return True


def fields() -> dict:
    return {

    }

