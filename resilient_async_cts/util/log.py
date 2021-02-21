import logging
import configparser

def get_logger():
    config = configparser.ConfigParser()
    config.read(os.environ.get('ASYNC_CTS_CONFIG_PATH'))

    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)

    #TODO: setup SMTP handler if enabled

    return log

log = get_logger()