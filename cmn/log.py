import logging
import os


def get_logger(modname: str, is_debug=False) -> logging.Logger:
    logger = logging.getLogger(modname)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(stream_handler)
    os.makedirs('logs', exist_ok=True)
    file_handler = logging.FileHandler(f'./logs/{modname}.log', mode='a')
    logger.addHandler(file_handler)
    if is_debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger
