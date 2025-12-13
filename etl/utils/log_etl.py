from datetime import datetime

#import logging
#logger = logging.getLogger(__name__)

def log_format(header, message):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"[{now}] [{header}] {message}"

def log_write(header, message):
    m = log_format(header, message)
    # write log file
    print(m)
