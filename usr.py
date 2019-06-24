
# User modules
from auth import *  # classes: cls
from globvars import *
from log import CUserLog

# reCAPHCHA has origin protection, be sure the hostname is 127.0.0.1 or localhost
# and enable cookies and the cross site script


class PLogin(PAuth):
    """ login page handler"""
    def get(self, *args, **kwargs):
        un = None
        try:
            if self.hasLoggedin():
                self.render('auth.html', color="rgba(255,0,0,0.2)", jump=CTools.jumpJsGen('/game', REDIRECT_TIME),
                            msg="You have logged in. <br> You will be redirected to Game Lobby page in {0} seconds.".format(
                                str(REDIRECT_TIME)
                            ))
            else:
                if DisableCAPTCHA:
                    s = dict({'h': '', 'i': '', 'b': '', 'c': ''})
                else:
                    s = CRecaptcha.gen()

                self.render('login.html',
                            header_script=s['h'],
                            inline_script=s['i'],
                            bottom_script=s['b'],
                            precheck_script=s['c'])
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            if un is not None:
                ulog = CUserLog(un)
                ulog.e(msg)
            self.send_error()
        finally:
            rlog.i('Login page request. ip:{0}, username:{1}'.format(
                self.request.remote_ip, 'None' if un is None else un))


class PSignUp(PAuth):
    """ reg page handler"""
    def get(self, *args, **kwargs):
        un = None
        try:
            if self.hasLoggedin():
                self.render('auth.html', color="rgba(255,0,0,0.2)", jump=CTools.jumpJsGen('/game', REDIRECT_TIME),
                            msg="You have logged in. <br> You will be redirected to Game Lobby page in {0} seconds.".format(
                                str(REDIRECT_TIME)
                            ))
            else:
                if DisableCAPTCHA:
                    s = dict({'h': '', 'i': '', 'b': '', 'c': ''})
                else:
                    s = CRecaptcha.gen()
                self.render('reg.html',
                            header_script=s['h'],
                            inline_script=s['i'],
                            bottom_script=s['b'],
                            precheck_script=s['c'])
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            if un is not None:
                ulog = CUserLog(un)
                ulog.e(msg)
            self.send_error()
        finally:
            rlog.i('Reg page request. ip:{0}, username:{1}'.format(
                self.request.remote_ip, 'None' if un is None else un))


if __name__ == "__main__":
    d = dict()
    d['un'] = 'fffff'
    d['pw'] = 'abv1K123_abc'
