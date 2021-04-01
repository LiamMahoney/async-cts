import configparser
import os

def parse_tuple(input):
    """
    Parses the config value into a tuple.
    :param string input: value from config
    :returns tuple
    """
    return tuple(k.strip() for k in input[1:-1].split(','))

config = configparser.ConfigParser(converters={'tuple': parse_tuple})
config.read(os.environ.get('ASYNC_CTS_CONFIG_PATH'))