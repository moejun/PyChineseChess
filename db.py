import sqlite3
import os
import sys
from globvars import *


class CDb:
    def __init__(self):
        if os.path.exists("db/data"):
            self.conn = sqlite3.connect("db/data")
            self.cur = self.conn.cursor()
        else:
            self.conn = None

    # sql: statment like    'select * from test where tid=?'
    #                       "update test set c = ? where tid=?"
    #                       'insert into User (un, pw, pw_salt, cid, cid_salt, cid_stime) ' \
    #                                     'values (?, ?, ?, ?, ?, ?)',
    #                                     ('aaaaaa','hhhhhh', 'ssss', 'cccc', 'cscscscsc', 'ctctct')
    # params: turple (52,)
    def e(self, sql, params):
        """
        secured sql execute wrapper.
        :param sql: sql statement
        :param params: params
        :return: execution result, msg
        """
        sql = sql.strip()
        # print(sql)
        if self.conn is not None:
            try:
                self.cur.execute(sql, params)
                if 'select' not in sql.lower()[:10]:
                    self.conn.commit()
                    return True, 'operation complete.'
                else:
                    re = self.cur.fetchall()
                    return (True, re) if len(re) > 0 else (False, 'No data fetched.')
            except Exception as e:
                msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                    sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
                slog.e(msg)
                rlog.e(msg)
                return False, msg if DEBUG else ""

        else:
            return False, "db file does not exist" if DEBUG else ''

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    db = CDb()
    qsuc, data = db.e('insert into User (un, pw, pw_salt, cid, cid_salt, cid_stime) '
                      'values (?, ?, ?, ?, ?, ?)', ('aaaaaa', 'hhhhhh', 'ssss', 'cccc', 'cscscscsc', 'ctctct'))
    if qsuc:
        print('true')
        print(data)
    else:
        print('false')
        print(data)
    db.close()
