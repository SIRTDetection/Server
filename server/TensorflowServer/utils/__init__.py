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
