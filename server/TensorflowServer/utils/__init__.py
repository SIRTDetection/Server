import logging


def setup_logging(logger_name: str, log_file: str, level=logging.DEBUG,
                  formatter: str = "%(asctime)s | [%(levelname)s]: %(message)s"):
    cleanupOldLogs(log_file)
    new_logging = logging.getLogger(logger_name)
    logging_formatter = logging.Formatter(formatter)
    logging_file_handler = logging.FileHandler(log_file, mode="w")

    logging_file_handler.setFormatter(logging_formatter)

    new_logging.setLevel(level)
    new_logging.addHandler(logging_file_handler)


def setup_console_logging(logger_name: str, stream, level=logging.DEBUG,
                          formatter: str = "%(asctime)s | [%(levelname)s]: %(message)s"):
    new_logging = logging.getLogger(logger_name)
    logging_formatter = logging.Formatter(formatter)
    if stream is not None:
        logging_handler = logging.StreamHandler(stream)

        logging_handler.setFormatter(logging_formatter)

        new_logging.setLevel(level)
        new_logging.addHandler(logging_handler)


def cleanupOldLogs(log_file: str):
    import tarfile
    import os

    tar_log_filename = log_file + "tar.gz"

    if os.path.exists(log_file):
        if os.path.exists(tar_log_filename):
            os.remove(tar_log_filename)
        with tarfile.open(tar_log_filename, "w:gz") as tar:
            tar.add(log_file, arcname=os.path.basename(log_file))
            tar.close()
            os.remove(log_file)


class LoggingHandler(object):
    class __LoggingHandler(object):
        def __init__(self, logs: list):
            self.__logs = logs

        def debug(self, msg, *args, **kwargs):
            for log in self.__logs:
                log.debug(msg, args, kwargs)

        def info(self, msg, *args, **kwargs):
            for log in self.__logs:
                log.info(msg, args, kwargs)

        def error(self, msg, *args, **kwargs):
            for log in self.__logs:
                log.error(msg, args, kwargs)

        def warning(self, msg, *args, **kwargs):
            for log in self.__logs:
                log.warning(msg, args, kwargs)

        def critical(self, msg, *args, **kwargs):
            for log in self.__logs:
                log.critical(msg, args, kwargs)

        def exception(self, msg, *args, exc_info: bool = True, **kwargs):
            for log in self.__logs:
                log.exception(msg, args, exc_info, kwargs)

    __instance = None

    def __new__(cls, *args, **kwargs):
        if not LoggingHandler.__instance:
            logs = kwargs.get("logs")
            if not logs or len(logs) == 0:
                raise AttributeError("At least kwarg \"log\" (a list of the loggers) must be provided")
            LoggingHandler.__instance = LoggingHandler.__LoggingHandler(logs)
        return LoggingHandler.__instance

    def __getattr__(self, item):
        return getattr(self.__instance, item)

    def __setattr__(self, key, value):
        return setattr(self.__instance, key, value)

    def debug(self, msg, *args, **kwargs):
        self.__instance.debug(msg, args, kwargs)

    def info(self, msg, *args, **kwargs):
        self.__instance.info(msg, args, kwargs)

    def error(self, msg, *args, **kwargs):
        self.__instance.error(msg, args, kwargs)

    def warning(self, msg, *args, **kwargs):
        self.__instance.warning(msg, args, kwargs)

    def critical(self, msg, *args, **kwargs):
        self.__instance.critical(msg, args, kwargs)

    def exception(self, msg, *args, exc_info: bool = True, **kwargs):
        self.__instance.exception(msg, args, exc_info, kwargs)
