from auth import *
from globvars import *
from log import CUserLog


class PStat(PAuth):
    """ stat page Class"""

    @web.authenticated
    def get(self, *args, **kwargs):
        """
        Handler of stat page
        :param args:
        :param kwargs:
        :return:
        """
        un = None
        try:

            #  web.authenticated cannot determine if the cid is valid, it can only know if cid was set.
            if self.hasLoggedin():
                un = str(self.get_secure_cookie('u'), encoding="utf-8")
                # self.write('Welcome, {0}<br>'.format(un))
                self.showstats(un)

            else:
                self.render('auth.html', color="rgba(0,0,0,0.2)", jump=CTools.jumpJsGen('/login', REDIRECT_TIME),
                            msg="You have not logged in yet. <br> "
                                "You will be redirected to the login page in {0} seconds.".format(
                                str(REDIRECT_TIME)))

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
            rlog.i('Statistics page request. ip:{0}, username:{1}'.format(
                self.request.remote_ip, 'None' if un is None else un))

    def showstats(self, un):
        """
        obtain and organize statistical data
        :param un: username
        :return: result, msg
        """
        db = CDb()
        result = None
        try:
            # query user info
            sql = 'select rid, un1, un2, winner from Game where status=?'

            qsuc, qdata = db.e(sql, ('closed',))  # Secured sql execution

            if qsuc:
                gen_room_html = ''
                ulist = self.getAllUser(qdata)
                num_user = len(ulist)

                user_stat = self.getUsersStat(ulist, qdata)

                for i in range(0, num_user):
                    gen_room_html += '<li>Username: {0} -> win: {1}, lost: {2}, draw: {3}'.format(
                        ulist[i],
                        user_stat[ulist[i]][0],
                        user_stat[ulist[i]][1],
                        user_stat[ulist[i]][2])

                self.render('game.html', color="rgba(0,0,0,0.2)", jump='',
                            msg=gen_room_html, usrname=un,
                            tt='Game Statistics (<a href="/game" style="font-size: 15px; color: #0066FF; '
                               'text-decoration: underline;">Retern to lobby</a>)',
                            show_btn='none')
            else:
                self.render('game.html', color="rgba(0,0,0,0.2)", jump='',
                            msg='', usrname=un)
                raise RuntimeError('DB Error.')

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
            rlog.i('Statistics page request. ip:{0}, username:{1}'.format(
                self.request.remote_ip, 'None' if un is None else un))

    def getAllUser(self, data):
        """
        return a list including all user
        :param data: data from database
        :return: list of users
        """
        ulist = []
        len1 = len(data)
        for i in range(0, len1):
            ulist.append(data[i][1])
            ulist.append(data[i][2])

        return list(set(ulist))

    def getUsersStat(self, ulist, data):
        """
        Analyze retrieved data and count the number of win, lose, and, draw
        :param ulist: list of users
        :param data: db data
        :return: analyze result.
        """
        re_dic = {}
        dlen1 = len(data)
        ulen1 = len(ulist)
        for j in range(0, ulen1):
            win = 0
            lost = 0
            draw = 0
            for i in range(0, dlen1):
                if(data[i][3] == 'red' and data[i][1] == ulist[j]) or \
                        (data[i][3] == 'black' and data[i][2] == ulist[j]):
                    win += 1
                if(data[i][3] == 'red' and data[i][2] == ulist[j]) or \
                        (data[i][3] == 'black' and data[i][1] == ulist[j]):
                    lost += 1

                if data[i][3] == 'Draw' and (data[i][2] == ulist[j] or data[i][1] == ulist[j]):
                    draw += 1

            re_dic[ulist[j]] = [str(win), str(lost), str(draw)]

        return re_dic
