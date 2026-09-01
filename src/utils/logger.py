#instead of every python file creating logger we can have one single logger
#later pipeline logs will have consistent format
# logging is essential for debugging and figuring out whats going wrong and right in the pipeline 

import logging       #1

def get_logger(name: str= "fpl_pipeline") -> logging.Logger:   #2 - defining function that can be used by all the code
    logger =logging.getLogger(name)                           #3

    if not logger.handlers:          #4 chceks wheather logger alredy has any handler - handler determines where the log message goes - so if not then create
        logger.setLevel(logging.INFO)     # 5) determines the minimum severity of messages the logger process

        handler = logging.StreamHandler()  # 6) handler determines where log is sent - stream handler send them to a strem normaly console/stderr
        formatter = logging.Formatter(          # 7) defines how log message looks - time stamp , log severity ,logger name,message you write 
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        handler.setFormatter(formatter)  # connects the 2 object handleer and formatter we created - so when handler outputs log message format like this - without this you get python logg format
        logger.addHandler(handler)        # connects the handler to logger

    return logger                 # returns the configured logger 


'''
1) logger framwork provides 
 logger.info()
 logger.warning()
 logger.error()
 logger.exception()
 logger.debug()

2) another file can use logger = get_logger()  and then logger.info("starting extraction")
 name :str is a type hint - tells that name is expected to be a string 
 name = "fpl_pipeline" just means the  argument is optional 
 -> logging.Logger is another type hint - it says the function will return logging.logger - doesn't change how the function works

3) logging.getLogger(name) - its crating and retrieving a logging channel - Python's logging system maintains named loggers.
 getLogger() doesn't necessarily create a brand-new logger every time.
 If a logger with that name already exists, Python returns that existing logger.
 That's important for the next part.
 
4) logger.handler - without it if we call get_logger()we will add another handler - one log message could come multiple times
5) python logging has several standard levels DEBUG INFO WARNING ERROR CRITICAL 
 DEBUG       ← very detailed
 INFO        ← normal operational information  - we are setting info because we want normall message
 WARNING     ← something unusual
 ERROR       ← something failed
 CRITICAL    ← serious failure
6) later we could add file logging 

7) for exmaple in another file 
 logger = get_logger("extract")
 logger.info("API request")
    timestamp from terminal | INFO |extract (by default fpl_pipeline) | API request'''

