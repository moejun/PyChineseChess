import logging
import logging.handlers

# In production env, log file could be very large. Using TimedRotatingFileHandler to generate log file in terms of date.


class CRootLog:
    """
    Root logger Class: log to one file only.
    """
    fmt_string = '[%(asctime)s] ' \
                 '%(processName)s(%(process)d) > %(threadName)s(%(thread)d)	' \
                 '%(name)s <%(levelname)s> ' \
                 '%(message)s'

    def __init__(self):
        logging.basicConfig(filename="log/root.log", filemode="a", format=CRootLog.fmt_string,
                            datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG, )

    def d(self, msg):
        logging.debug(msg)

    def i(self, msg):
        logging.info(msg)

    def w(self, msg):
        logging.warning(msg)

    def e(self, msg):
        logging.error(msg)

    def c(self, msg):
        logging.critical(msg)


class CUserLog:
    """
    User logger Class: log to files only. file names are the users' names
    """
    def __init__(self, logger_name):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)

        hd_file_d_1 = logging.FileHandler(filename="log/Usr_{0}.ULOG".format(logger_name))
        hd_file_d_1.setLevel(logging.INFO)

        formatter = logging.Formatter(CRootLog.fmt_string)
        hd_file_d_1.setFormatter(formatter)

        self.logger.addHandler(hd_file_d_1)

    def d(self, msg):
        self.logger.debug(msg)

    def i(self, msg):
        self.logger.info(msg)

    def w(self, msg):
        self.logger.warning(msg)

    def e(self, msg):
        self.logger.error(msg)

    def c(self, msg):
        self.logger.critical(msg)


# use classmethod if i have time to do that.
class CStreamLog:
    """
    Debug logger: only log msg to terminals.
    """
    fmt_string = CRootLog.fmt_string

    def __init__(self):
        self.logger = logging.getLogger('debug_stream')

        self.hd_stream_d_1 = logging.StreamHandler()

        self.logger.setLevel(logging.DEBUG)
        self.hd_stream_d_1.setLevel(logging.DEBUG)

        self.formatter = logging.Formatter(self.fmt_string)
        self.hd_stream_d_1.setFormatter(self.formatter)

        self.logger.addHandler(self.hd_stream_d_1)

    def d(self, msg):
        self.logger.debug(msg)

    def i(self, msg):
        self.logger.info(msg)

    def w(self, msg):
        self.logger.warning(msg)

    def e(self, msg):
        self.logger.error(msg)

    def c(self, msg):
        self.logger.critical(msg)


if __name__ == "__main__":
    r_logger = CUserLog('test')
    r_logger.d('debug msg')
    r_logger.i('info msg')
    r_logger.w('warning msg')
    r_logger.e('error msg')
    r_logger.c('critical msg')
