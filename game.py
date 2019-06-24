from tornado import gen

# User modules
from usr import *
from db import CDb
from log import CUserLog


class PGame(PAuth):
    @web.authenticated
    def get(self, *args, **kwargs):
        """
        Game page handler
        :param args:
        :param kwargs:
        :return:
        """
        rlog.i('Game lobby page request. from {0}'.format(self.request.remote_ip))
        un = None
        try:
            #  web.authenticated cannot determine if the cid is valid, it can only know if cid was set.
            if self.hasLoggedin():
                un = str(self.get_secure_cookie('u'), encoding="utf-8")
                # self.write('Welcome, {0}<br>'.format(un))
                self.showRooms(un)
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
            rlog.i('Game page request. ip:{0}, username:{1}'.format(
                self.request.remote_ip, 'None' if un is None else un))

    def showRooms(self, un):
        """
        show the list of rooms
        :param un: username
        :return: None
        """
        db = CDb()
        result = None
        try:
            # query user info
            sql = 'select * from Game where status=? or status=? or un1=? or un2=?'
            # room status:
            #   opened: anyone can join.
            #   waiting: waiting for game start.
            #   gaming: the game has been started.
            #   closed: the game is over.
            qsuc, qdata = db.e(sql, ('opened', 'closed', un, un))  # Secured sql execution

            if qsuc:
                gen_room_html = ''
                num_of_rooms = len(qdata)
                stat2txt = {'opened': 'Join', 'waiting': 'Resume', 'gaming': 'Resume', 'closed': 'Review'}

                for i in range(0, num_of_rooms):
                    btntxt = stat2txt[qdata[i][2]]
                    winner = 'None' if qdata[i][8] is None else qdata[i][8]
                    if (qdata[i][2] == 'opened') and (un in [qdata[i][3], qdata[i][4]]):
                        btntxt = 'Resume'
                    gen_room_html += '<li>No: {0}, Room ID: {4}, status: {1}, user1: {2}, user2: {3}, winner: {6} -> ' \
                                     '<a href="/room?r={4}&a=9"> [{5}]</a></li>'.format(i+1, qdata[i][2],
                                                                                        qdata[i][3], qdata[i][4],
                                                                                        qdata[i][0], btntxt,
                                                                                        winner)

                self.render('game.html', color="rgba(0,0,0,0.2)", jump='',
                            msg=gen_room_html, usrname=un,
                            tt='Game Lobby(<a href="/stats" style="font-size: 15px; color: #0066FF;'
                               'text-decoration: underline;"> Statistics </a>)', show_btn='block')

            else:
                self.send_error()
                raise RuntimeError('Failed to retrieve data.')

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
            rlog.i('Game page request. ip:{0}, username:{1}'.format(
                self.request.remote_ip, 'None' if un is None else un))


# 对局类
class PRoom(PAuth):

    # user logger
    ul = None

    @web.authenticated
    def get(self, *args, **kwargs):
        """
        Room page handler
        :param args:
        :param kwargs:
        :return:
        """
        rlog.i('Game room page request. from {0}'.format(self.request.remote_ip))
        if self.hasLoggedin():
            un = str(self.get_secure_cookie('u'), encoding="utf-8")
            rlog.i('Game page request. ip:{0}, username:{1}'.format(
                self.request.remote_ip, 'None' if un is None else un))
            #  check if the username in cookie .
            if re.match(r'^[a-zA-Z0-9]{4,20}$', un) is None:
                self.send_error(403)
                return ''

            self.ul = CUserLog(un)
            self.ul.i('The user visit the room page.')
            try:
                # check get params
                action = self.get_argument('a')
                if re.match(r'^\d+$', action):
                    action = int(action)

                    # create room handler
                    if action == 8:
                        suc, msg = self.createRoom(un)
                        if suc is True:
                            self.ul.i('Create game, room id: {0}.'.format(msg))
                            self.render('auth.html', color="rgba(0,255,0,0.2)",
                                        jump=CTools.jumpJsGen('/room?a=9&r={0}'.format(msg), 1),
                                        msg="Creating room succeeded. <br> "
                                            "You will be redirected to the room page in {0} seconds.".format(
                                            str(1)))
                        else:
                            self.ul.w('Create game failed, Reason: {0}.'.format(msg))

                    # join room handler
                    elif action == 9:
                        rid = int(self.get_argument('r'))

                        suc, msg = self.joinRoom(un, rid)

                        if suc is True:
                            self.ul.i('Join game, room sid: {0}.'.format(msg))
                            self.showRoom(rid, un, msg)
                        else:
                            self.ul.w('Join game failed, Reason: {0}.'.format(msg))
                            self.send_error()
                    else:
                        self.send_error()
                else:
                    self.send_error()
            except ValueError as e:
                msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                    sys._getframe().f_code.co_name, __file__,
                    sys._getframe().f_lineno, str(e)+': The user sent a invalid action code.')
                self.send_error()
                self.ul.e(msg)
            except Exception as e:
                msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                    sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
                slog.e(msg)
                rlog.e(msg)
                self.ul.e(msg)
                self.send_error()

        else:
            rlog.i('Room page request. ip:{0}, username:{1}'.format(
                self.request.remote_ip, 'None'))
            self.render('auth.html', color="rgba(255,0,0,0.2)", jump=CTools.jumpJsGen('/login', REDIRECT_TIME),
                        msg="You have not logged in yet. <br> "
                            "You will be redirected to the login page in {0} seconds.".format(
                            str(REDIRECT_TIME)))

    def closeRoom(self, sid, un):
        """
        close a room of a user
        :param sid: the room's id
        :param un: username
        :return: execution result
        """
        self.ul.i('The user\'s room is being closed, sid: '+sid)
        db = CDb()
        try:
            # query opponent's name
            s_sql = 'select un1, un2 from Game where sid=?'
            s_suc, s_data = db.e(s_sql, (sid, ))  # Secured sql execution
            if s_suc:
                u1 = s_data[0][0]
                u2 = s_data[0][1]

                # because the user is proven that he is in the room.
                winner = 'black' if u1 == un else 'red'

                # close room and let opponent win
                u_sql = 'update Game set status=?, winner=? where sid=?'
                u_suc, u_data = db.e(u_sql, ('closed', winner, sid))  # Secured sql execution
                if u_suc:
                    return True, ''
                else:
                    self.ul.w('Failed to close the room. sid:{0}'.format(sid))
                    raise RuntimeError('Failed to close the room.')
            else:
                raise RuntimeError('Failed to query the opponent\'s name.')

        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            self.ul.e(msg)
            return False, msg if DEBUG else ''
        finally:
            db.close()

    def createRoom(self, un):
        """
        Controller to deal with the create room action
        :param un: username
        :return: (bool,rid)
        """
        self.ul.i('The user tries to create a room.')
        db = CDb()
        try:
            # if the person has incompleted game, close the old games first.
            self.closeJoinedRooms(un)

            # check if generate a duplicated sid.
            while True:
                sid = CSessionCtrl.genSid()
                s_sql = 'select rid from Game where sid=?'
                s_suc, s_data = db.e(s_sql, (sid,))  # Secured sql execution
                if not s_suc:
                    break

            i_sql = 'insert into Game (status, un1, sid, action, action_timer) values (?, ?, ?, ?, ?)'
            i_suc, i_data = db.e(i_sql, ('opened', un, sid, 'red', 300,))  # Secured sql execution
            if i_suc:
                self.set_secure_cookie('sid', sid, expires_days=1,
                                       secure=True)  # send cookies via SSL only.
                self.ul.i('[PASS] Inserting new game info to database')
                slog.i(un + 'create room sid: ' + sid)
                s_sql = 'select rid from Game where sid=?'
                s_suc, s_data = db.e(s_sql, (sid,))  # Secured sql execution
                if s_suc:
                    self.ul.i('[PASS] Querying new game cid from database')
                    # saving sid to user for further play.
                    u_sql = 'update User set saved_sid=? where un=?'
                    u_suc, u_data = db.e(u_sql, (sid, un))
                    if u_suc:
                        self.ul.i('[PASS] Saving sid to user table')
                        return True, s_data[0][0]
                    else:
                        raise RuntimeError('[FAIL]  Saving sid to user table: ' + u_data)
                else:
                    raise RuntimeError('[FAIL] Querying new game cid from database: ' + s_data)
            else:
                raise RuntimeError('[FAIL] Inserting new game info to database: ' + i_data)
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            self.ul.e(msg)
            slog.e(msg)
            rlog.e(msg)

            return False, msg if DEBUG else ''
        finally:
            db.close()

    # if a user is in a room
    def inRoom(self, un, rid):
        """
        identify if the user in a room
        :param un: username
        :param rid: room id
        :return: if the user in the room: True/False
        """
        db = CDb()
        try:
            s_sql = 'select rid from Game where rid=? and (un1=? or un2=?)'
            s_suc, s_data = db.e(s_sql, (rid, un, un))  # Secured sql execution
            if s_suc:
                return True
            else:
                # no result or query error
                return False
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            self.ul.e(msg)
            return None
        finally:
            db.close()

    def inRooms(self, un):
        """
        Return a list of room that the user joined
        :param un: Username
        :return: room id and sid list
        """
        db = CDb()
        try:
            s_sql = 'select rid, sid from Game where un1=? or un2=?'
            s_suc, s_data = db.e(s_sql, (un, un))  # Secured sql execution
            if s_suc:
                return s_data
            else:
                return None
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            self.ul.e(msg)
            return None
        finally:
            db.close()

    def closeJoinedRooms(self, un):
        """
        function to close all the opened room of the user.
        :param un: user name
        :return: None
        """
        try:
            osid = self.get_secure_cookie('sid').decode()

            # get list of rooms the user joined.
            osid2 = self.inRooms(un)

            if osid is not None or osid2 is not None:
                self.closeRoom(osid, un)
                for i in osid2:
                    self.closeRoom(i[1], un)
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            if un is not None:
                ulog = CUserLog(un)
                ulog.e(msg)

    def joinRoom(self, un, rid):
        """
        Controller when a user tries to join a room.
        :param un: username
        :param rid: room id
        :return: (bool, sid)  joined room's sid
        """
        self.ul.i('The user tries to join room {0}.'.format(str(rid)))
        db = CDb()
        try:
            s_sql = 'select sid, status, un1, un2 from Game where rid=?'
            s_suc, s_data = db.e(s_sql, (rid,))  # Secured sql execution
            if s_suc:
                if s_data[0][1].strip() == 'opened':
                    is_in = self.inRoom(un, rid)

                    # if the user is creator and back to the room
                    if is_in is True:
                        self.ul.i('[The user reconnected.')

                        self.set_secure_cookie('sid', s_data[0][0], expires_days=1,
                                               secure=True)  # send cookies via SSL only.
                        slog.i('The user {0} reconnected a opened room {1} sid: {2}'.format(un, rid, s_data[0][0]))
                        from comm import PData
                        usr_f = PData.uid2faction(un, s_data[0][0])
                        PData.updateTimeOut(10, s_data[0][0], usr_f)
                        # check timeout done in the comm.py
                        return True, s_data[0][0]

                    # if the user is new player
                    elif is_in is False:
                        self.closeJoinedRooms(un)
                        self.ul.i('[PASS] Querying sid from db to join the room.')
                        self.set_secure_cookie('sid', s_data[0][0], expires_days=1,
                                               secure=True)  # send cookies via SSL only.

                        # updating room info
                        i_sql = 'update Game set status=?, un2=?, action_timer=? where rid=?'
                        i_suc, i_data = db.e(i_sql, ('gaming', un, 60*5, rid))
                        # Secured sql execution
                        if i_suc:
                            self.ul.i('[PASS] Updating new player info to the room')

                            # saving sid to user for further play.
                            u_sql = 'update User set saved_sid=? where un=?'
                            u_suc, u_data = db.e(u_sql, (s_data[0][0], un))
                            if u_suc:
                                self.ul.i('[PASS] Saving sid to user table')
                                return True, s_data[0][0]
                            else:
                                raise RuntimeError('[FAIL]  Saving sid to user table: ' + u_data)
                        else:
                            raise RuntimeError('[FAIL]  Updating new player info to the room: ' + i_data)
                    else:
                        self.send_error(500)
                        return False, 'exception occurred'
                elif s_data[0][1].strip() in ['waiting', 'gaming']:

                    # if a user back to the room.
                    if self.inRoom(un, rid):
                        self.ul.i('[The user reconnected.')
                        self.set_secure_cookie('sid', s_data[0][0], expires_days=1,
                                               secure=True)  # send cookies via SSL only.
                        slog.i('The user {0} reconnected a gaming room {1} sid: {2}'.format(un, rid, s_data[0][0]))
                        # resetTimer()
                        return True, s_data[0][0]
                    else:
                        self.send_error(404)
                        self.ul.w('The user tried to join a full or finished room. rid:{0}'.format(str(rid)))
                        return False, 'The room is unavailable.'
                else:
                    # closed room is opened for every authenticated user.
                    return True, ''
            else:
                self.ul.w('The user tried to join a non-exist room. rid:{0}'.format(str(rid)))
                return False, 'rid error.'

        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            self.ul.e(msg)
            return False, msg if DEBUG else ''

        finally:
            db.close()

    def showRoom(self, rid, uid, sid):
        """
        render the room page by given params
        :param rid: room id
        :param uid: username
        :param sid: room's sid
        :return: execution reuslt, msg
        """
        self.ul.i('The user tries to enter room {0}.'.format(str(rid)))
        db = CDb()
        try:
            s_sql = 'select un1, un2, status, action, action_timer, winner from Game where rid=?'
            s_suc, s_data = db.e(s_sql, (rid,))  # Secured sql execution
            if s_suc:
                from app import ws_settings
                # print('show room ssid:' + str(self.get_secure_cookie('sid'), encoding='utf-8'))
                # print('show room sid:'+self.get_cookie('sid'))
                wspara = 'c={0}&u={1}&s={2}'.format(self.get_cookie('cid'),
                                                    self.get_cookie('u'),
                                                    sid)

                p1 = s_data[0][0]
                p2 = s_data[0][1]
                # showing the user's faction.
                if p1 == uid:
                    p1 = '(YOU)' + p1
                elif p2 == uid:
                    p2 = '(YOU)' + p2

                # showing the page.
                self.render('room.html',
                            room_text="Room {0}".format(str(rid)), room_id=rid,
                            p1=p1, p2=p2, status=s_data[0][2],
                            turn=s_data[0][3], timer=s_data[0][4], winner=s_data[0][5],
                            iput='disabled="disabled"' if s_data[0][5] is not None else '',
                            wsip=ws_settings['ip'], wspt=ws_settings['port'], wspg=ws_settings['page'],
                            wspara='n',)  # send secured cookie only, even using ws via ssl.
            else:
                self.ul.w('The user tried to join a non-exist room. rid:{0}'.format(str(rid)))
                return False, 'rid error.'

        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            self.ul.e(msg)
            return False, msg if DEBUG else ""
        finally:
            db.close()


class CBoard:
    """
    class for board operations.
    """
    def __init__(self):
        self.map = list([[{"f": "black", "pid": "00", "pn": "车"}, {"f": "black", "pid": "01", "pn": "马"},
                   {"f": "black", "pid": "02", "pn": "象"}, {"f": "black", "pid": "03", "pn": "士"},
                   {"f": "black", "pid": "04", "pn": "将"}, {"f": "black", "pid": "05", "pn": "士"},
                   {"f": "black", "pid": "06", "pn": "象"}, {"f": "black", "pid": "07", "pn": "马"},
                   {"f": "black", "pid": "08", "pn": "车"}],
                  [{"f": "", "pid": "10", "pn": ""}, {"f": "", "pid": "11", "pn": ""}, {"f": "", "pid": "12", "pn": ""},
                   {"f": "", "pid": "13", "pn": ""}, {"f": "", "pid": "14", "pn": ""}, {"f": "", "pid": "15", "pn": ""},
                   {"f": "", "pid": "16", "pn": ""}, {"f": "", "pid": "17", "pn": ""},
                   {"f": "", "pid": "18", "pn": ""}],
                  [{"f": "", "pid": "20", "pn": ""}, {"f": "black", "pid": "21", "pn": "炮"},
                   {"f": "", "pid": "22", "pn": ""}, {"f": "", "pid": "23", "pn": ""},
                   {"f": "", "pid": "24", "pn": ""}, {"f": "", "pid": "25", "pn": ""},
                   {"f": "", "pid": "26", "pn": ""}, {"f": "black", "pid": "27", "pn": "炮"},
                   {"f": "", "pid": "28", "pn": ""}],
                  [{"f": "black", "pid": "30", "pn": "兵"}, {"f": "", "pid": "31", "pn": ""},
                   {"f": "black", "pid": "32", "pn": "兵"}, {"f": "", "pid": "33", "pn": ""},
                   {"f": "black", "pid": "34", "pn": "兵"}, {"f": "", "pid": "35", "pn": ""},
                   {"f": "black", "pid": "36", "pn": "兵"}, {"f": "", "pid": "37", "pn": ""},
                   {"f": "black", "pid": "38", "pn": "兵"}],
                  [{"f": "", "pid": "40", "pn": ""}, {"f": "", "pid": "41", "pn": ""}, {"f": "", "pid": "42", "pn": ""},
                   {"f": "", "pid": "43", "pn": ""}, {"f": "", "pid": "44", "pn": ""}, {"f": "", "pid": "45", "pn": ""},
                   {"f": "", "pid": "46", "pn": ""}, {"f": "", "pid": "47", "pn": ""},
                   {"f": "", "pid": "48", "pn": ""}],
                  [{"f": "", "pid": "50", "pn": ""}, {"f": "", "pid": "51", "pn": ""}, {"f": "", "pid": "52", "pn": ""},
                   {"f": "", "pid": "53", "pn": ""}, {"f": "", "pid": "54", "pn": ""}, {"f": "", "pid": "55", "pn": ""},
                   {"f": "", "pid": "56", "pn": ""}, {"f": "", "pid": "57", "pn": ""},
                   {"f": "", "pid": "58", "pn": ""}],
                  [{"f": "red", "pid": "60", "pn": "兵"}, {"f": "", "pid": "61", "pn": ""},
                   {"f": "red", "pid": "62", "pn": "兵"},
                   {"f": "", "pid": "63", "pn": ""}, {"f": "red", "pid": "64", "pn": "兵"},
                   {"f": "", "pid": "65", "pn": ""},
                   {"f": "red", "pid": "66", "pn": "兵"}, {"f": "", "pid": "67", "pn": ""},
                   {"f": "red", "pid": "68", "pn": "兵"}],
                  [{"f": "", "pid": "70", "pn": ""}, {"f": "red", "pid": "71", "pn": "炮"},
                   {"f": "", "pid": "72", "pn": ""},
                   {"f": "", "pid": "73", "pn": ""}, {"f": "", "pid": "74", "pn": ""}, {"f": "", "pid": "75", "pn": ""},
                   {"f": "", "pid": "76", "pn": ""}, {"f": "red", "pid": "77", "pn": "炮"},
                   {"f": "", "pid": "78", "pn": ""}],
                  [{"f": "", "pid": "80", "pn": ""}, {"f": "", "pid": "81", "pn": ""}, {"f": "", "pid": "82", "pn": ""},
                   {"f": "", "pid": "83", "pn": ""},
                   {"f": "", "pid": "84", "pn": ""}, {"f": "", "pid": "85", "pn": ""}, {"f": "", "pid": "86", "pn": ""},
                   {"f": "", "pid": "87", "pn": ""},
                   {"f": "", "pid": "88", "pn": ""}],
                  [{"f": "red", "pid": "90", "pn": "车"}, {"f": "red", "pid": "91", "pn": "马"},
                   {"f": "red", "pid": "92", "pn": "象"},
                   {"f": "red", "pid": "93", "pn": "士"}, {"f": "red", "pid": "94", "pn": "将"},
                   {"f": "red", "pid": "95", "pn": "士"},
                   {"f": "red", "pid": "96", "pn": "象"}, {"f": "red", "pid": "97", "pn": "马"},
                   {"f": "red", "pid": "98", "pn": "车"}]])

        self.cn2en = {
            '车': 'chaRiot',
            '炮': 'Cannon',
            '马': 'Horses',
            '兵': 'Pawn',
            '将': 'King',
            '士': 'Adviser',
            '象': 'Elephant',
        }

    def saveBoard(self, sid, uid):
        """
        save the board data to database
        :param sid: room's sid
        :param uid: username
        :return: execution result
        """
        # there are three ways to save the board: trade-off between time and memory. No a case for modern computer.
        # 1. every step should be saved to db, each time obtain a map from db.
        # 2. every step should be saved to db and shared global variable indexed by sid,
        #    each time obtain a map from the memory.
        # 3. every step should be saved to db and their ws_clients variables, each time obtain a map from the memory.
        import json
        db = CDb()
        try:
            m = json.dumps(self.map)
            s_sql = 'update Game set data=?, action=? where sid=?'
            # print(uid, ws_clients[uid]['f'], swfac[ws_clients[uid]['f']])
            s_suc, s_data = db.e(s_sql, (m, swfac[ws_clients[uid]['f']], sid))  # Secured sql execution
            if s_suc:
                return True
            else:
                raise RuntimeError('update failed.')
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            if uid is not None:
                ulog = CUserLog(uid)
                ulog.e(msg)
            return False
        finally:
            db.close()

    def checkFaction(self, s, sid, uid):
        """
        Check if the user's faction allows him to do such a movement.
        :param s: user input
        :param sid: room's sid
        :param uid: username
        :return: valid: True/False, msg
        """
        # 吃子 设置pn=""
        sx = int(s[0])
        sy = int(s[1])
        if self.map[sx][sy]['f'] != '':
            db = CDb()
            try:
                s_sql = 'select un1, un2, action, status from Game where sid=?'
                s_suc, s_data = db.e(s_sql, (sid,))  # Secured sql execution
                s_data = s_data[0]
                if s_suc:
                    if s_data[3] == "gaming":
                        if uid == s_data[0]:
                            if self.map[sx][sy]['f'] == 'red':
                                if s_data[2] == 'red':
                                    return True, ''
                                else:
                                    return False, 'This is not your turn.'
                            else:
                                return False, 'You cannot move a piece that is not your faction.'
                        elif uid == s_data[1]:
                            if self.map[sx][sy]['f'] == 'black':
                                if s_data[2] == 'black':
                                    return True, ''
                                else:
                                    return False, 'This is not your turn.'
                            else:
                                return False, 'You cannot move a piece that is not your faction.'
                        else:
                            return False, 'The user is not in the match.'
                    else:
                        return False, 'The game is completed or not started yet'
                else:
                    return False, 'The match is not existent.'

            except Exception as e:
                msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                    sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
                slog.e(msg)
                rlog.e(msg)
                if uid is not None:
                    ulog = CUserLog(uid)
                    ulog.e(msg)
                return False, msg if DEBUG else ''
            finally:
                db.close()
        else:
            return False, 'Your cannot move a non-existent piece.'

    def setBoard(self, s, sid, uid):
        """
        Controller of various verifications and operations
        :param s: user input
        :param sid: room's sid
        :param uid: username
        :return: if the action success: True/False, if someone win: True/False, Winner's faction.
        """
        try:
            # print(type(s), s)
            if re.match(r'^\d[0-8]\d[0-8]$', s) is not None:
                cf_suc, cf_msg = self.checkFaction(s, sid, uid)
                # True: ''. False, reason.
                if cf_suc:
                    suc, msg = self.checkSteps(s)
                    # if True: return True. if False, return reason.
                    if suc:
                        w = self.checkWin()
                        return True, msg, w
                    else:
                        return False, msg, (False, '')
                else:
                    return False, cf_msg, (False, '')
            else:
                return False, 'Format of the decision is incorrect.', (False, '')
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            if uid is not None:
                ulog = CUserLog(uid)
                ulog.e(msg)
            return False, msg if DEBUG else ''

    def setSteps(self, s, can_destory=True):
        """
        Take action and update the board data
        :param s:
        :param can_destory: reserved
        :return: True/False
        """
        try:
            # 吃子 设置pn=""
            sx = int(s[0])
            sy = int(s[1])
            dx = int(s[2])
            dy = int(s[3])

            # destroy the opponent piece on destination.
            self.map[dx][dy]['pn'] = ""
            self.map[dx][dy]['f'] = ""

            tmp = self.map[sx][sy]
            self.map[sx][sy] = self.map[dx][dy]
            self.map[dx][dy] = tmp

            return True
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            return False

    def getBoard(self, sid):
        """
        Retrieve board data from database
        :param sid: room's sid
        :return: board data object.
        """
        import json
        db = CDb()
        try:
            s_sql = 'select data from Game where sid=?'
            s_suc, s_data = db.e(s_sql, (sid,))  # Secured sql execution
            if s_suc:
                # if previous map data exists, recover the map. else, use initialized map.
                if s_data[0][0] is not None:
                    # print('find data')
                    self.map = json.loads(s_data[0][0])
                return self.map
            else:
                return False

        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            return False
        finally:
            db.close()

    def checkWin(self):
        """
        Check if somebody wins the game after the received movement
        :return: True/False, winner's faction
        """
        try:
            # print('checkWin')
            # find which faction's king is dead.
            # if one of the kings is dead, the faction whose king is alive will win.
            king = '将'
            red_alive = []
            black_alive = []
            i_len = len(self.map)
            for i in range(0, i_len):
                j_len = len(self.map[i])
                for j in range(0, j_len):
                    if self.map[i][j]['pn'] != "":
                        if self.map[i][j]['f'] == 'red':
                            red_alive.append(self.map[i][j]['pn'])
                        elif self.map[i][j]['f'] == 'black':
                            black_alive.append(self.map[i][j]['pn'])

            if (king not in red_alive) and (king in black_alive):
                # black faction wins
                return True, 'black'
            elif (king not in black_alive) and (king in red_alive):
                # red faction wins
                return True, 'red'
            else:
                # no body wins yet
                return False, ''
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            return False, ''

    @staticmethod
    def setWin(winner, sid, draw=False):
        """
        update database's winner field.
        :param winner: winner's faction
        :param sid: sid of the room
        :param draw: if the game has no winner
        :return: sql result.
        """
        # draw： all timeout or exceed the max steps.
        if draw:
            winner = 'Draw'
        db = CDb()
        # print('setwin')
        # faction name to index of queried data.
        try:
            u_sql = 'update Game set winner=?, status=? where sid=?'
            u_suc, u_data = db.e(u_sql, (winner, 'closed', sid, ))
            if u_suc:
                return True
            else:
                raise RuntimeError("update failed.")

        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            return False
        finally:
            db.close()

    def checkSteps(self, s):
        """
        Check if the user's move follows the rule of the game
        :param s: user input
        :return: True/False, result of setSteps.
        """
        try:
            sx = int(s[0])
            sy = int(s[1])
            dx = int(s[2])
            dy = int(s[3])
            # Overall rules
            if (sx == dx) and (sy == dy):
                return False, 'Your destination position cannot be the same as your source position.'
            elif self.map[sx][sy]['pn'] == "":
                return False, 'Your cannot move a non-existent piece.'
            elif (self.map[dx][dy]['pn'] != "") and (self.map[sx][sy]['f'] == self.map[dx][dy]['f']):
                return False, 'You cannot destroy the piece of your faction.'
            elif self.map[sx][sy]['f'] not in ['red', 'black']:
                return False, 'Faction Error'
            else:
                # Piece rules
                if self.map[sx][sy]['pn'] == "车":
                    # '车''chaRiot' Rules
                    if sx == dx:
                        if abs(sy-dy) == 1:
                            return True, self.setSteps(s)
                        else:
                            for i in range(min(sy, dy)+1, max(sy, dy)):
                                if self.map[sx][i]['pn'] != "":
                                    return False, "chaRoit cannot move to a position " \
                                                  "which the positions between the source and destination " \
                                                  "are not empty."
                                else:
                                    return True, self.setSteps(s)
                    elif sy == dy:
                        if abs(sx-dx) == 1:
                            return True, self.setSteps(s)
                        else:
                            for i in range(min(sx, dx)+1, max(sx, dx)):
                                if self.map[i][sy]['pn'] != "":
                                    return False, "chaRoit cannot move to a position " \
                                                  "which the positions between the source and destination " \
                                                  "are not empty."
                                else:
                                    return True, self.setSteps(s)
                    else:
                        return False, 'chaRoit can only move horizontally or vertically.'

                elif self.map[sx][sy]['pn'] == "炮":
                    # '炮''Cannon' Rules
                    c = 0

                    if sx == dx:
                        if abs(sx-dx) == 1:
                            return True, self.setSteps(s)
                        else:
                            for i in range(min(sy, dy)+1, max(sy, dy)):
                                if self.map[sx][i]['pn'] != "":
                                    c += 1
                            if c == 1 and self.map[dx][dy]['pn'] != "":
                                return True, self.setSteps(s)
                            elif c == 0 and self.map[dx][dy]['pn'] == "":
                                return True, self.setSteps(s, False)
                            else:
                                return False, "Cannon cannot move to a position " \
                                              "which the positions between the source and destination are not empty." \
                                              "Cannon can only destroy an enemy, " \
                                              "when there is exactly one piece between the canon and enemy."
                    elif sy == dy:
                        if abs(sx-dx) == 1:
                            return True, self.setSteps(s)
                        else:
                            for i in range(min(sx, dx)+1, max(sx, dx)):
                                if self.map[i][sy]['pn'] != "":
                                    c += 1
                            if c == 1 and self.map[dx][dy]['pn'] != "":
                                return True, self.setSteps(s)
                            elif c == 0 and self.map[dx][dy]['pn'] == "":
                                return True, self.setSteps(s, False)
                            else:
                                return False, "Cannon cannot move to a position " \
                                              "which the positions between the source and destination are not empty." \
                                              "Cannon can only destroy an enemy, " \
                                              "when there is exactly one piece between the canon and enemy."
                    else:
                        return False, 'Cannon can only move horizontally or vertically.'

                elif self.map[sx][sy]['pn'] == "马":
                    # '马''Horses' Rules

                    if (sx-dx == 2) and (abs(sy-dy) == 1):
                        # block top.
                        if self.map[sx-1][sy]['pn'] != "":
                            return False, 'The horse is blocked by the piece on its top.'
                        else:
                            return True, self.setSteps(s)
                    elif (dx-sx == 2) and (abs(sy-dy) == 1):
                        # block bottom.
                        if self.map[sx+1][sy]['pn'] != "":
                            return False, 'The horse is blocked by the piece under it.'
                        else:
                            return True, self.setSteps(s)
                    elif (dy-sy == 2) and (abs(sx-dx) == 1):
                        # block right.
                        if self.map[sx][sy+1]['pn'] != "":
                            return False, 'The horse is blocked by the piece on its right.'
                        else:
                            return True, self.setSteps(s)
                    elif (sy-dy == 2) and (abs(sx-dx) == 1):
                        # block left.
                        if self.map[sx][sy-1]['pn'] != "":
                            return False, 'The horse is blocked by the piece on its left.'
                        else:
                            return True, self.setSteps(s)
                    else:
                        return False, 'The horse cannot be moved to that position.'

                elif self.map[sx][sy]['pn'] == "兵":
                    # '兵''Pawn' Rules
                    if abs(sx - dx) + abs(sy - dy) != 1:
                        return False, 'Pawn can only move horizontally or vertically.'
                    else:
                        if self.map[sx][sy]['f'] == "red":
                            if sx < dx:
                                return False, 'Pawn cannot move back'
                            elif (sx > 4) and (sy != dy):
                                return False, 'Pawn cannot move horizontally before crossing the river.'
                            else:
                                return True, self.setSteps(s)
                        elif self.map[sx][sy]['f'] == "black":
                            if sx > dx:
                                return False, 'Pawn cannot move back'
                            elif (sx < 5) and (sy != dy):
                                return False, 'Pawn cannot move horizontally before crossing the river.'
                            else:
                                return True, self.setSteps(s)

                elif self.map[sx][sy]['pn'] == "将":
                    # '将''King' Rules
                    if abs(sx-dx)+abs(sy-dy) == 1:
                        if self.map[sx][sy]['f'] == "red":
                            if dx < 7 or dy < 3 or dy > 5:
                                return False, 'The King can not move out of the palace.'
                        elif self.map[sx][sy]['f'] == "black":
                            if dx > 2 or dy < 3 or dy > 5:
                                return False, 'The King can not move out of the palace.'

                        tmp = None  # position of the other king.
                        for i in range(0, 10):
                            if i == sx:
                                continue
                            if self.map[i][dy]['pn'] == "将":
                                tmp = i

                        if tmp is not None:
                            ctr = 0
                            for i in range(min(tmp, sx)+1, max(tmp, sx)):
                                if self.map[i][dy]['pn'] != "":
                                    ctr += 1
                            if ctr == 0:
                                return False, 'The King can not face to the other King.'
                            else:
                                return True, self.setSteps(s)
                        else:
                            return True, self.setSteps(s)
                    else:
                        return False, 'The King can only move horizontally or vertically.'

                elif self.map[sx][sy]['pn'] == "士":
                    # '士''Adviser' Rules
                    if (abs(sx-dx) == 1) and (abs(sy-dy) == 1):
                        if self.map[sx][sy]['f'] == "red":
                            if dx < 7 or dy < 3 or dy > 5:
                                return False, 'The adviser can not move out of the palace.'
                            else:
                                return True, self.setSteps(s)
                        elif self.map[sx][sy]['f'] == "black":
                            if dx > 2 or dy < 3 or dy > 5:
                                return False, 'The adviser can not move out of the palace.'
                            else:
                                return True, self.setSteps(s)
                    else:
                        return False, 'The adviser can only move one space diagonally.'

                elif self.map[sx][sy]['pn'] == "象":
                    # '象''Elephant' Rules
                    if (self.map[sx][sy]['f'] == "red") and (dx < 5):
                            return False, 'The elephant can not cross the river.'
                    elif (self.map[sx][sy]['f'] == "black") and (dx > 4):
                            return False, 'The elephant can not cross the river.'
                    else:
                        if (abs(sx - dx) == 2) and (abs(sy - dy) == 2):
                            # block top.
                            if self.map[int((sx+dx)/2)][int((sy+dy)/2)]['pn'] != "":
                                return False, 'The elephant is blocked by the piece on center.'
                            else:
                                return True, self.setSteps(s)
                        else:
                            return False, 'The elephant cannot be moved to that position.'
                else:
                    return False, 'Undefined Piece.'
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            return False, msg if DEBUG else ''


class CRecord:
    @staticmethod
    def parseRecord(un, fac, rec):
        """
        Parse inputs from user and ouput the returned value to save Record
        :param un: user's name
        :param fac: user's faction
        :param rec: user's input
        :return: value as saveRecord input.
        """
        return "{0}[{1}]: {2} -> {3}".format(fac, un, rec[:2], rec[2:])

    @staticmethod
    def addRecord(sid, rec):
        """
        Adding one record to database
        :param rec: record
        :param sid: room's sid
        :return: result: True/False
        """
        db = CDb()
        try:
            # get existent records.
            old_rec = CRecord.getRecord(sid)
            if old_rec is not False:
                m = old_rec + ';' + rec
                s_sql = 'update Game set record=? where sid=?'
                s_suc, s_data = db.e(s_sql, (m, sid))  # Secured sql execution
                if s_suc:
                    return True
                else:
                    raise RuntimeError('update failed.')
            else:
                return False
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            return False
        finally:
            db.close()

    @staticmethod
    def getRecord(sid):
        """
        Retrieving records from a database
        :param sid: room's sid
        :return: records
        """
        rec = ""
        db = CDb()
        try:
            s_sql = 'select record from Game where sid=?'
            s_suc, s_data = db.e(s_sql, (sid,))  # Secured sql execution
            if s_suc:
                # Appending the record to the existing records.
                if s_data[0][0] is not None:
                    rec = s_data[0][0]
                return rec
            else:
                return False
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            return False
        finally:
            db.close()


if __name__ == '__main__':
    pass
    # PGame.showRooms()
