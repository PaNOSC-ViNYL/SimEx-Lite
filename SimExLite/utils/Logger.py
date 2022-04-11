import logging

def setLogger(logger_name):
    """Please set the logger_name = __name__"""
    # Logging setting
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    # Example:
    # 2022-04-07 16:06:34,572:module_name:INFO: My first message.
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s')
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger
