import logging
import configparser
import os
import sys

def get_logger():
    config = configparser.ConfigParser()
    config.read(os.environ.get('ASYNC_CTS_CONFIG_PATH'))

    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)

    std_out_handler = logging.StreamHandler(sys.stdout)
    log.addHandler(std_out_handler)
    #TODO: setup SMTP handler if enabled

    return log

log = get_logger()