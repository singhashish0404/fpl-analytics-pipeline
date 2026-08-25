#instead of every python file creating logger we can have one single logger
#later pipeline logs will have consistent format

import logging

def get_logger(name: str= "fpl_pipeline") -> logging.logger:
    logger =logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger