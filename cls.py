import time
import os
import json
import sys
from tornado import web
from hashlib import sha256, md5
from urllib.parse import urlencode
from urllib.request import urlopen, Request
# from urllib.request import URLError

# User modules
from db import *
from log import CUserLog


class BaseCls(web.RequestHandler):

    '''
    def prepare(self):
        if self.request.protocol == 'http':
            self.redirect('https://' + self.request.host + ":23333", permanent=False)
    '''

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Credentials', 'true')
        self.set_header('Access-Control-Allow-Origin', 'https://www.google.com;{0}'.format(
            self.request.headers.get('Origin')))
        self.set_header('Access-Control-Allow-Headers', 'x-requested-with')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def get_current_user(self):
        return self.get_secure_cookie("cid")


class CTools:
    @staticmethod
    def parseLog(ip, msg, file='', func='', line=''):
        return ':: IP: {0}=> on File {1}, Func {2}, line {3}:{4}'.format(
               ip, file, func, line, msg)

    @staticmethod
    def jumpJsGen(url, second):
        return "<meta http-equiv=\"refresh\" content=\"{0};url={1}\">".format(str(second), url)

    @staticmethod
    def genSalt():
        rnd = str(os.urandom(128))
        return md5(rnd.encode()).hexdigest()[::2]  # pick 16 bytes from the output of MD5


class CPwCtrl:
    @staticmethod
    def pwHash(pw, salt):
        seed = "{0} {1}".format(pw, salt)
        return sha256(seed.encode()).hexdigest()

    @staticmethod
    def pwVerify(dbhash, pw, salt):
        h = CPwCtrl.pwHash(pw, salt)
        return True if h == dbhash else False


class CSessionCtrl:

    @staticmethod
    def genCid(un, ti, salt):
        seed = "{0}{1}{2}".format(un, str(ti), salt)
        return sha256(seed.encode()).hexdigest()

    @staticmethod
    def genSid():
        #  tested
        seed = "{0}{1}".format(str(time.time()), str(os.urandom(128)))
        sid = sha256(seed.encode()).hexdigest()
        return sid

    @staticmethod
    def varifyCid(cid, un):
        # tested
        db = CDb()
        expire_day2sec = 3600*24
        qsuc, data = db.e('select cid_salt, cid_stime from User where cid=?', (cid,))
        data = data[0]  # using the first matched record. cid in the db is unique.
        db.close()
        if qsuc:
            # Checking if the cid expired
            time_now = str(time.time()).split('.')[0]
            time_cid = data[1].split('.')[0]
            time_dif = int(time_now) - int(time_cid)
            if 0 < time_dif <= expire_day2sec:
                # [del]I do not need to compare the cids, computed cid = stored cid.[/del]
                # Checking the hash
                # use username to ensure they cannot brute-force enumerate cid with single known username
                # I dont need to compare the given name and the name in db,
                # because if the given name is incorrect, the cid will be different

                rcid = CSessionCtrl.genCid(un, data[1], data[0])
                # print(rcid, cid, un, data[1], data[0])
                if rcid == cid:
                    return True, 'The credential is valid'
                else:
                    return False, 'The credential is invalid'
            else:
                return False, 'The credential was expired'
        else:
            return False, str(data)

    @staticmethod
    def varifySid(sid, un):
        db = CDb()
        try:
            s_sql = 'select un1, un2 from Game where sid=? and status<>?'
            s_suc, s_data = db.e(s_sql, (sid, 'closed'))  # Secured sql execution
            if s_suc:
                if un in [s_data[0][0], s_data[0][1]]:
                    return True, ''
                else:
                    return False, 'You are not a player of the room.'
            else:
                return False, 'You are entering a non-existent room.'
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            if un is not None:
                ulog = CUserLog(un)
                ulog.e(msg)
            return False, msg if DEBUG else ''
        finally:
            db.close()


class CRecaptcha:
    public_key = "6Lc_Yp8UAAAAAKYWryrMOL6garOlNgUW_zmuQRqN"

    @staticmethod
    def gen():
        re = dict()

        re['h'] = '<script type="text/javascript"> ' \
                  'var onloadCallback = function() {' \
                  'grecaptcha.render(\'html_element\', ' \
                  '{\'sitekey\' : \'' + CRecaptcha.public_key + '\',\'data-size\' : \'compact \'});};</script>'
        re['c'] = '<script type="application/javascript">function check_reCaptcha() {' \
                  'if(grecaptcha.getResponse() == ""){' \
                  'alert("Please do reCaptcha verification first.");' \
                  'return false;' \
                  '}else{' \
                  'return true;}}</script>'
        re['b'] = '<script ' \
                  'src="https://www.google.com/recaptcha/api.js?onload=onloadCallback&render=explicit"' \
                  ' async defer></script>'

        re['i'] = '<div id="html_element"></div>'
        return re

    @staticmethod
    def verify(response):
        private_key = '6Lc_Yp8UAAAAAPv1bZqsFA0tMBxROhDxUHHvbjrp'

        '''
        errmsg = {"missing-input-secret": "The secret parameter is missing.",
                  "invalid-input-secret": "The secret parameter is invalid or malformed.",
                  "missing-input-response": "The response parameter is missing.",
                  "invalid-input-response": "The response parameter is invalid or malformed.",
                  "bad-request": "The request is invalid or malformed.",
                  "timeout-or-duplicate": "The response is no longer valid: too old or been used previously."
                  }
        '''
        url = 'https://www.google.com/recaptcha/api/siteverify'

        if response is not None:
            params = {
                'secret': private_key,
                'response': response.strip()
            }
            headers = {
                'Content-type': 'application/x-www-form-urlencoded'
            }
            socket = None

            # Temporary resolution for CVE-2019-9947
            try:
                data = urlencode(params).encode('ascii')  # CVE-2019-9636 fixed: UTF-8 -> ascii
                url_req = Request(url, data, headers)
                socket = urlopen(url_req)
                raw_json = socket.read().decode('ascii')
                resp = json.loads(raw_json)
                if resp['success'] is True:
                    return True, resp
                else:
                    return False, resp

            except Exception as e:
                msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                    sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
                slog.e(msg)
                rlog.e(msg)
                return False, msg if DEBUG else ''

            finally:
                if socket is not None:
                    socket.close()

        else:
            return False, 'reCAPTCHA response is empty'


'''
class CCaptcha:
    @staticmethod
    def gen():
        c = RecaptchaClient('6Lc_Yp8UAAAAAPv1bZqsFA0tMBxROhDxUHHvbjrp',
                        '6Lc_Yp8UAAAAAKYWryrMOL6garOlNgUW_zmuQRqN',
                        verification_timeout=300)
        return c.get_challenge_markup(use_ssl=True)

'''

if __name__ == "__main__":
    rcid = CSessionCtrl.genCid('test', '1556326809.62534', '8f49cd6738e1462d')
    print(rcid)
