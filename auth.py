import re

from cls import *


class PAuth(BaseCls):
    '''
        def get(self, *args, **kwargs):
            if self.hasLoggedin():
                un = self.get_secure_cookie('u')
                self.write('Welcome, {0}'.format(str(un, encoding="utf-8")))
            else:
                self.render('auth.html', color="rgba(255,0,0,0.2)", jump=CTools.jumpJsGen('/login', REDIRECT_TIME),
                            msg="You have not logged in yet. <br> "
                                "You will be redirected to the login page in {0} seconds.".format(
                                str(REDIRECT_TIME)))
    '''

    def hasLoggedin(self):
        """
        Check if the user has already logged in
        :return: True/False
        """
        cid = self.get_secure_cookie('cid')
        un = self.get_secure_cookie('u')
        if (un is not None) and (cid is not None):
            cid = str(cid, encoding="utf-8")
            un = str(un, encoding="utf-8")

            v, v_msg = CSessionCtrl.varifyCid(cid, un)
            # print(cid, un, v, v_msg)
            if v:
                # if the cid is existent and valid
                return True
            else:
                return False
        else:
            return False

    def post(self, *args, **kwargs):
        """
        Handler of auth page. the page cannot be accessed by GET
        :param args:
        :param kwargs:
        :return:
        """
        un = None
        try:
            rlog.i('auth page request - post. from {0}'.format(self.request.remote_ip))
            data = dict()
            tmp = self.get_argument('a', None).strip()

            if tmp is None:
                action = 0
                # print(self.request.uri)
                # self.redirect(self.request.uri)
            else:
                action = int(tmp)  # SEC

            data['un'] = self.get_argument('un', None).strip()
            un = data['un']
            data['pw'] = self.get_argument('pw', None).strip()
            data['cap'] = self.get_argument('g-recaptcha-response', None)
            type2msg = {20: 'Sign Up', 21: 'Log In', 22: 'Game Lobby'}
            type2page = {20: '/reg', 21: '/login', 22: '/game'}

            # collecting executing state, storing log/success/fail/ feedback info.
            flag = [False, []]
            # Counter of page redirection
            redirect_ctr = REDIRECT_TIME

            # checking before using the received un
            if re.match(r'^[a-zA-Z0-9]{4,20}$', data['un']) is None:
                self.render('auth.html', color="rgba(255,0,0,0.2)",
                            jump=CTools.jumpJsGen(type2page[action], redirect_ctr),
                            msg="{0} failed! Reason(s) are:<br>{1}<br> "
                                "You will be redirected to previous page in {2} seconds.".format(
                                'Auth failed', 'The username contains illegal char.', str(redirect_ctr)
                            ))
            else:
                if self.hasLoggedin():
                    # if the cid is existent and valid
                    self.render('auth.html',
                                color="rgba(255,0,0,0.2)",
                                jump=CTools.jumpJsGen(type2page[22], redirect_ctr),
                                msg="You have logged in. <br>You will be redirected to {0} page in {1} seconds.".format(
                                    type2msg[22], str(redirect_ctr)
                                ))
                else:
                    if action == 20:  # SignUp
                        # flag here will be directly changed in the function
                        self.signupCheck(flag, data)

                    elif action == 21:  # Login
                        # flag here will be directly changed in the function
                        self.loginCheck(flag, data)
                    else:
                        flag[0] = False
                        flag[1].append([flag[1], "[FAIL] Action Check"])

                    if flag[0] is True:
                        # All success auth will be redirect to the game lobby.
                        self.render('auth.html', color="rgba(0,255,0,0.2)",
                                    jump=CTools.jumpJsGen(type2page[22], redirect_ctr),
                                    msg="{0} succeeded!<br> You will be redirected to {1} page in "
                                        "<span id=\"timec\">{2}</span> seconds.".format(
                                        type2msg[action], type2msg[22], str(redirect_ctr)
                                    ))
                    else:
                        # join for logging
                        flag_log = '<br> -> '.join(flag[1])
                        # All failed auth will be redirect to the page that has done the action.
                        self.render('auth.html', color="rgba(255,0,0,0.2)",
                                    jump=CTools.jumpJsGen(type2page[action], redirect_ctr),
                                    msg="{0} failed! Reason(s) are:<br>{1}<br> You will be "
                                        "redirected to previous page in <span id=\"timec\">{2}</span> seconds.".format(
                                        type2msg[action], flag_log if DEBUG else flag[1][-1], str(redirect_ctr)
                                    ))
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
            rlog.i('Auth page request. ip:{0}, username:{1}'.format(
                self.request.remote_ip, 'None' if un is None else un))

    def signupCheck(self, flag, data):
        """
        Handler of a series of validation checks
        :param flag: check result
        :param data: inputs
        :return: None
        """
        # if the response wrong then the verification will failed
        captcha_flag, msg = CRecaptcha.verify(data['cap'])

        if (captcha_flag is True) or DisableCAPTCHA:
            # logging
            flag[0] = True
            flag[1].append('[PASS] reCAPTCHA Check')
            c_re = CAuth.paramsCheck(5, flag, data)
            if c_re:
                flag[0] = True
                flag[1].append('[PASS] Params Check')
                # store to database
                db = CDb()
                un = data['un']
                try:
                    cid_salt = CTools.genSalt()
                    cid_time = str(time.time())
                    cid = CSessionCtrl.genCid(data['un'], cid_time, cid_salt)
                    # print(cid, cid_time, cid_salt)
                    pw_salt = CTools.genSalt()
                    pw = CPwCtrl.pwHash(data['pw'], pw_salt)
                    # store c to database
                    s_sql = 'insert into User (un, pw, pw_salt, cid, cid_salt, cid_stime) ' \
                            'values (?, ?, ?, ?, ?, ?)'
                    qsuc, qdata = db.e(s_sql,
                                       (data['un'], pw, pw_salt, cid, cid_salt, cid_time))  # Secured sql execution
                    if qsuc:
                        self.set_secure_cookie('cid', cid, expires_days=1,
                                               secure=True)  # send cookies via SSL only.
                        self.set_secure_cookie('u', data['un'], expires_days=1,
                                               secure=True)  # send cookies via SSL only.
                        flag[0] = True
                        flag[1].append('[PASS] Adding user to db and setting cid for the user')
                    else:
                        flag[0] = False
                        flag[1].append(
                            '[FAIL] Storing cid to db and setting cid for the user' +
                            (': ' + qdata) if DEBUG else '')  # qdata contains sensitive info

                except Exception as e:
                    msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                        sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
                    slog.e(msg)
                    rlog.e(msg)
                    if un is not None:
                        ulog = CUserLog(un)
                        ulog.e(msg)

                    flag[0] = False
                    flag[1].append('[FAIL] Params Check unexpected error' +
                                   (': ' + str(e)) if DEBUG else '')   # e contains sensitive info
                finally:
                    db.close()
            else:
                flag[0] = False
        else:
            flag[0] = False
            flag[1].append('[FAIL] reCAPTCHA Check: [' + ', '.join(msg['error-codes']) + ']')
            # resp['challenge_ts'], resp['hostname'], resp['error-codes']

    def loginCheck(self, flag, data):
        """
        handler of a series of login validations
        :param flag: check result
        :param data: input
        :return: None
        """
        captcha_flag, msg = CRecaptcha.verify(data['cap'])
        if (captcha_flag is True) or DisableCAPTCHA:
            # logging
            flag[0] = True
            flag[1].append('[PASS] reCAPTCHA Check')
            l_re = CAuth.paramsCheck(6, flag, data)
            if l_re is False:
                flag[0] = False
            else:
                db = CDb()
                un = data['un']
                try:
                    # query user info
                    l_sql = 'select * from User where un=?'
                    qsuc, qdata = db.e(l_sql, (data['un'],))  # Secured sql execution
                    qdata = qdata[0]
                    if qsuc:
                        # verify user.
                        rcvd_pwhash = CPwCtrl.pwHash(data['pw'], qdata[3])  # received password hash
                        if qdata[2] == rcvd_pwhash:
                            flag[0] = True
                            flag[1].append('[PASS] Username and password are valid')
                            # recover saved sid
                            self.set_secure_cookie('sid', qdata[7], expires_days=1,
                                                   secure=True)  # send cookies via SSL only.

                            # setting new cid
                            cid_salt = CTools.genSalt()
                            cid_time = str(time.time())
                            cid = CSessionCtrl.genCid(data['un'], cid_time, cid_salt)

                            # print(cid_salt, cid_time, cid)
                            s_sql = 'update User set cid=?, cid_salt=?, cid_stime=? ' \
                                    'where uid=?'
                            qcsuc, qcdata = db.e(s_sql, (cid, cid_salt, cid_time, qdata[0]))
                            if qcsuc:
                                self.set_secure_cookie('cid', cid, expires_days=1,
                                                       secure=True)  # send cookies via SSL only.
                                self.set_secure_cookie('u', data['un'], expires_days=1,
                                                       secure=True)  # send cookies via SSL only.
                                flag[0] = True
                                flag[1].append('[PASS] Storing cid to db and setting cid for the user')
                            else:
                                flag[0] = False
                                flag[1].append('[FAIL] Storing cid to db and setting cid for the user'
                                               + (': '+qcdata) if DEBUG else '')
                        else:
                            flag[0] = False
                            flag[1].append('[FAIL] Username or Password is incorrect')
                    else:
                        flag[0] = False
                        flag[1].append('[FAIL] Username or Password is incorrect')

                except Exception as e:
                    msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                        sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
                    slog.e(msg)
                    rlog.e(msg)
                    if un is not None:
                        ulog = CUserLog(un)
                        ulog.e(msg)

                    flag[0] = False
                    flag[1].append('[FAIL] Params Check unexpected error' + (': '+str(e)) if DEBUG else '')
                finally:
                    db.close()
        else:
            flag[0] = False
            flag[1].append('[FAIL] reCAPTCHA Check: [' + ', '.join(msg['error-codes']) + ']')


class CAuth:

    @staticmethod
    def paramsCheck(typ, flag, d):
        """
        username and password check.
        :param typ: check type
        :param flag: result
        :param d: input
        :return: result
        """
        # tested
        # username: len:4-20, charset: a-z, A-Z, 0-9. start with a-z or A-Z
        # password: len:8-30, charset: a-z, A-Z, _-#@!, 0-9. one or more special chars are required.
        un = d['un']
        pw = d['pw']
        lchars = [chr(a) for a in range(ord('a'), ord('z'))]
        uchars = [chr(a) for a in range(ord('A'), ord('Z'))]
        nchars = [str(a) for a in range(0, 10)]
        schars = ['_', '-', '#', '@', '!']
        flag[1].append('[Param Check Start]')
        # signup params check
        if typ == 5:
            # Length check
            if (len(un) < 4) or (len(un) > 20) or (len(pw) < 8) or (len(pw) > 30):
                flag[1].append('[FAIL] username and password length check')
                return False
            else:
                flag[1].append('[PASS] username and password length check')

                # Username format check
                if re.match(r'^[a-zA-Z][a-zA-Z0-9]{3,19}$', un) is None:
                    flag[1].append('[FAIL] username format check')
                    return False
                else:
                    flag[1].append('[PASS] username format check')

                    # Username existence check
                    db = CDb()
                    qre, qdata = db.e('select uid from User where un=?', (un,))
                    db.close()
                    if qre is True:
                        flag[1].append('[FAIL] username existence check')
                        return False
                    else:
                        flag[1].append('[PASS] username existence check')

                        # Password check
                        have_schr = False
                        have_lchr = False
                        have_uchr = False
                        have_nchr = False
                        for p in pw:
                            if p in lchars:
                                have_lchr = True
                            elif p in uchars:
                                have_uchr = True
                            elif p in nchars:
                                have_nchr = True
                            elif p in schars:
                                have_schr = True
                            else:
                                flag[1].append('[FAIL] Password contain invalid char')
                                return False

                        """
                        print("have_schr:{0}, have_lchr:{1}, have_uchr:{2}, have_nchr:{3}".format(
                            have_schr, have_lchr,have_uchr, have_nchr))
                        """

                        if have_schr & have_lchr & have_uchr & have_nchr:
                            flag[1].append('[PASS] password char variability check')
                            flag[1].append('[PASS] Param Check')
                            return True
                        else:
                            flag[1].append('[FAIL] password char variability check')
                            return False

        # login params check
        elif typ == 6:
            c_un = False if re.match(r'^[a-zA-Z0-9]{4,20}$', un) is None else True
            c_pw = False if re.match(r'^[a-zA-Z0-9_\-#@!]{8,30}$', pw) is None else True
            if c_un & c_pw:
                flag[1].append('[PASS] Login param check')
                flag[1].append('[PASS] Param Check')
                return True
            else:
                flag[1].append('[FAIL] Username or Password is incorrect.')
                return False
