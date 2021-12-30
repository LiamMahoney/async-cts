import logging, logging.handlers
import os
import sys
import json
from .config import config

def create_smtp_handler():
    """
    Creates an SMTP handler from values supplied in the app.config
    :returns SMTPHandler
    """
    validate_smtp_handler_config()

    mailhost = config['email_exception_handler'].gettuple('smtp_log_mailhost')
    fromaddr = config['email_exception_handler'].get('smtp_log_fromaddr')
    toaddrs = json.loads(config['email_exception_handler'].get('smtp_log_to_addrs'))
    subject = config['email_exception_handler'].get('smtp_log_subject')
    # only using the following values if the placeholder is not used
    credentials = config['email_exception_handler'].gettuple('smtp_log_credentials') if config['email_exception_handler'].get('smtp_log_credentials') != "('user','pass')" else None
    secure = config['email_exception_handler'].gettuple('smtp_log_secure') if config['email_exception_handler'].get('smtp_log_secure') != "('/path/to/cert.cer')" else None

    return logging.handlers.SMTPHandler(mailhost=mailhost, fromaddr=fromaddr, toaddrs=toaddrs, subject=subject, credentials=credentials, secure=secure)

def validate_smtp_handler_config():
    """
    Validates that all of the required information is filled in for teh SMTP 
    handler in the app.config file.
    :raises ValueError when a required value is missing
    """
    missing_fields = []

    if (not config['email_exception_handler'].get('smtp_log_mailhost') or config['email_exception_handler'].get('smtp_log_mailhost') == "('mailserver', 'port')"):
        missing_fields.append('smtp_log_mailhost')
    
    if (not config['email_exception_handler'].get('smtp_log_fromaddr')):
        # default from addr of {{ name }}_cts@{{ name }}_cts.com may be acceptable
        missing_fields.append('smtp_log_fromaddr')

    if (not config['email_exception_handler'].get('smtp_log_to_addrs') or config['email_exception_handler'].get('smtp_log_to_addrs') == "['email@gmail.com']"):
        missing_fields.append('smtp_log_to_addrs')

    if (not config['email_exception_handler'].get('smtp_log_subject')):
        # default from addr of '{{ name }} CTS Error' may be acceptable
        missing_fields.append('smtp_log_subject')

    if (missing_fields):
        raise ValueError(f"Missing required app.config values(s) to use the SMTP log handler: {', '.join(missing_fields)}")

def get_logger():
    """
    Gets the logger instance and makes it available for the rest of the library.

    :returns Logger
    """
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)

    std_out_handler = logging.StreamHandler(sys.stdout)
    log.addHandler(std_out_handler)

    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s", "%m-%d-%Y %H:%M:%S%z")
    std_out_handler.setFormatter(formatter)
    
    if (config['email_exception_handler'].getboolean('smtp_log_enabled')):
        smtp_handler = create_smtp_handler()
        smtp_handler.setLevel(config['email_exception_handler'].get('smtp_log_level'))
        log.addHandler(smtp_handler)

    return log

log = get_logger()