from tornado import websocket
import time
import json
import sys
from globvars import *

from globvars import ws_clients, swfac
from log import *
from cls import CSessionCtrl
from game import CBoard, CRecord
from db import CDb

'''
import asyncio
import threading
class CWsPingThr(threading.Thread):
    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        import datetime
        while True:
            for key in ws_clients.keys():
                msg = str(datetime.datetime.now())
                ws_clients[key]['ins'].write_message(msg)
                print("write to client %s:%s" % (key, msg))
            time.sleep(1)

'''


class PData(websocket.WebSocketHandler):

    """
    Server-client communication Class
    """

    logger = CRootLog()

    cid = None
    uid = None
    sid = None
    b = None

    def open(self, *args, **kwargs):
        # WS open function
        self.set_nodelay(True)
        try:
            # decoding the cookies
            self.cid = self.get_secure_cookie('cid')
            self.uid = self.get_secure_cookie('u')
            self.sid = self.get_secure_cookie('sid')
            if (self.cid is not None) and (self.uid is not None) and (self.sid is not None):
                self.cid = str(self.cid, encoding='utf-8').strip()
                self.uid = str(self.uid, encoding='utf-8').strip()
                self.sid = str(self.sid, encoding='utf-8').strip()
            else:
                raise ValueError('Parameters cannot be empty')

            # check if the user is valid and is in a valid room.
            if self.checkComm():
                # save instance of ws into the dict for sending private message.

                user_faction = PData.uid2faction(self.uid, self.sid)
                ws_clients[self.uid] = {'ins': self, "cid": self.cid, "uid": self.uid, "sid": self.sid,
                                        'f': user_faction if user_faction is not False else self.close(1003, 'ErrorFaction')}

                if PData.getRoomStatus(self.sid) != "closed":
                    # when a user join a room, check both sides timeout.
                    self.joinTimeOutCheck()

                # let the opponent know
                self.sendToAll('Hello:'+self.uid)

                # send new records
                self.sendToAll("Rec::" + CRecord.getRecord(self.sid))

                # get map from db
                self.b = CBoard()
                # print(self.b)
                m = self.b.getBoard(self.sid)
                # print(m)
                if m is not False:
                    self.write_message(json.dumps(m))
                else:
                    self.write_message('Error: Failed to obtain data from the database.')

            else:
                self.logger.w('[FAIL] WS: Credential Check: uid:{0}, cid:{1}, sid:{2}'.format(
                    self.uid, self.cid, self.sid))
                self.close(1003, 'Credential or Room info Error.')
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            un = self.uid
            if un is not None:
                ulog = CUserLog(un)
                ulog.e(msg)

    def on_message(self, rmsg):
        # when receive a message
        try:
            print("Received a message from {0}: {1}".format(self.uid, rmsg))
            '''
            try:
                msg = json.loads(msg)
                print("Type {0}".format(msg[0][0]['pn']))
            except Exception as e:
                print(str(e))
            '''
            if rmsg == 'timeoutcheck':
                # passive timeout checking
                request_from = PData.uid2faction(self.uid, self.sid)
                if request_from == 'red':
                    # if black timeout, let red be the winner
                    if PData.checkTimeout(self.sid, 'black'):
                        pass
                elif request_from == 'black':
                    PData.checkTimeout(self.sid, 'red')
            else:
                self.b.map = self.b.getBoard(self.sid)
                suc, msg, opt = self.b.setBoard(rmsg, self.sid, self.uid)
                if suc:
                    prepared_rec = CRecord.parseRecord(self.uid, ws_clients[self.uid]['f'], rmsg)
                    CRecord.addRecord(self.sid, prepared_rec)
                    self.b.saveBoard(self.sid, self.uid)

                    # send new records
                    self.sendToAll("Rec::" + CRecord.getRecord(self.sid))

                    # send new map
                    self.sendToAll(self.b.map, json_enable=True)

                    # switch turn
                    self.sendToAll('SW:' + swfac[ws_clients[self.uid]['f']])

                    # if someone wins
                    if opt[0]:
                        print('winner found')
                        wsuc = CBoard.setWin(opt[1], self.sid)
                        if wsuc:
                            self.sendToAll('Winner:' + opt[1])
                else:
                    print('Error:' + msg)
                    self.write_message('Error:' + msg)
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            un = self.sid
            if un is not None:
                ulog = CUserLog(un)
                ulog.e(msg)

    def on_close(self):
        # when a client close the ws
        if self.uid in ws_clients:
            # store fanction info  before remove the user from the ws_clients.
            t_fac = ws_clients[self.uid]['f']
            del ws_clients[self.uid]

            # send notification to his opponent.
            if PData.getRoomStatus(self.sid) != "closed":
                # send and log timeout notification.
                self.sendToAll('Timeout:' + self.uid)
                self.logger.i('{0} disconnected from room a whose sid: {1}'.format(self.uid, self.sid))
                print(self.uid, 'closed')

                # update timeout timer in database.
                PData.updateTimeOut(11, self.sid, t_fac)

    def check_origin(self, origin):
        return True

    @staticmethod
    def getRoomStatus(sid):
        """
        Obtain the status of the room
        :param sid: room's sid
        :return: status or False when failed
        """
        db = CDb()
        try:
            s_sql = 'select status from Game where sid=?'
            s_suc, s_data = db.e(s_sql, (sid,))

            if s_suc:
                return s_data[0][0]
            else:
                raise RuntimeError('No such a room')

        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            return False

        finally:
            db.close()

    @staticmethod
    def checkTimeout(sid, faction):
        """
        Check if players are timeout
        :param sid: room id
        :param faction: faction
        :return: True/False
        """
        print('checking the timeout of opponent of ', faction)

        db = CDb()
        try:
            if faction == "red":
                s_sql = 'select red_timer, un1 from Game where sid=?'
            elif faction == "black":
                s_sql = 'select black_timer, un2 from Game where sid=?'
            else:
                print("error faction.")
                return True

            s_suc, s_data = db.e(s_sql, (sid, ))

            # Secured sql execution
            if s_suc:
                if s_data[0][0] is not None:
                    current_time = int(str(time.time()).split('.')[0])
                    if current_time - int(s_data[0][0]) > 300:
                        print(current_time, s_data[0][0])
                        return True
                    else:
                        return False
                else:
                    return None
            else:
                return True

        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            return None

        finally:
            db.close()

    @staticmethod
    def uid2faction(uid, sid):
        """
        Obtain a user's faction
        :param uid: username
        :param sid: room's sid
        :return: faction name or False when failed.
        """
        db = CDb()
        try:
            s_sql = 'select un1, un2 from Game where sid=?'
            s_suc, s_data = db.e(s_sql, (sid, ))

            if s_suc:
                if uid == s_data[0][0]:
                    return 'red'
                elif uid == s_data[0][1]:
                    return 'black'
                else:
                    return False
            else:
                raise RuntimeError('no such a room')

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

    def joinTimeOutCheck(self):
        """
        when a user join a room, check both sides timeout.
        :return: None
        """
        db = CDb()
        try:
            s_sql = 'select status, un2 from Game where sid=?'
            s_suc, s_data = db.e(s_sql, (self.sid,))  # Secured sql execution
            if s_suc and s_data[0][0].strip() != 'closed':
                timeout_red = PData.checkTimeout(self.sid, 'red')
                timeout_black = PData.checkTimeout(self.sid, 'black')

                if not (timeout_red is None and timeout_black is None):

                    if (timeout_red is None and timeout_black is True and s_data[0][1] is not None) or (timeout_black is True and timeout_red is False):
                        if CBoard.setWin('red', self.sid):
                            print('black player time out. game completed, room closed, sid: {0}'.format(self.sid))
                        else:
                            print('failed to set win')

                    # if red timeout when no second player join in the room
                    if (timeout_black is None and timeout_red is True and s_data[0][1] is None) or (timeout_black is True and timeout_red is True):
                        if CBoard.setWin('red', self.sid, draw=True):
                            print('all player time out. game completed, room closed, sid: {0}'.format(self.sid))
                        else:
                            print('failed to set win')

                    elif (timeout_black is None and timeout_red is True and s_data[0][1] is not None) or (timeout_black is False and timeout_red is True):
                        if CBoard.setWin('black', self.sid):
                            print('red player time out. game completed, room closed, sid: {0}'.format(self.sid))
                        else:
                            print('failed to set win')
                    else:
                        print('all players are not time out')
            else:
                raise RuntimeError('no such a room')

        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            un = self.uid
            if un is not None:
                ulog = CUserLog(un)
                ulog.e(msg)
        finally:
            db.close()

    @staticmethod
    def updateTimeOut(typ, sid, f):
        """
        Set Null when user back, set current timestamp when a user leaves.
        :param typ: 10: (when the user reconn, )clear the timer
                     11: (when the user disconn, )set the timer
        :param sid: room's sid
        :param f: faction
        :return: True/False
        """
        db = CDb()
        try:
            # when a user disconn
            i_sql = ""
            if f == "red":
                i_sql = 'update Game set red_timer=? where sid=?'
            elif f == "black":
                i_sql = 'update Game set black_timer=? where sid=?'
            else:
                raise RuntimeError("error faction.")

            t = 0
            if typ == 11:
                t = str(time.time()).split('.')[0]
            elif typ == 10:
                # set a larger value to let CurrentTime-TheValue=negative. Then we know the use is online.
                t = None  # str(time.time()).replace('.', '')
            else:
                print("error faction.")
                return False
            i_suc, i_data = db.e(i_sql, (t, sid))

            # Secured sql execution
            if i_suc:
                # self.logger.i('{0}\'s disconnection timer updated to sid {1}'.format(uid, sid))
                return True
            else:
                raise RuntimeError('update failed.')

        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            return False
        finally:
            db.close()

    def checkComm(self):
        """
        Verify if the ws connection is valid.
        :return:
        """
        # Varifying the cid
        v, v_msg = CSessionCtrl.varifyCid(self.cid, self.uid)
        if not v:
            return False, 'Credential error.'
        else:
            # if the cid is existent and valid, check if the room is exist and opened.
            # closed rooms do not need a ws
            if CSessionCtrl.varifySid(self.sid, self.uid):
                return True, ''
            else:
                return False, 'The room is closed or non-exist.'

    def sendToAll(self, msg, json_enable=False):
        """
        Send message to all active players who are in the same room as the messager sender, including sender itself,
        via the TLS-based WebSocket.
        :param msg: message that will be sent
        :param json_enable: if use json to encode the message
        :return: None
        """
        # group boardcasting.
        # print(msg)
        # print(ws_clients)
        try:
            for i in ws_clients.keys():
                if ws_clients[i]['sid'] == self.sid:
                    # print("Renewed board is sent to:", self.sid)
                    # print('sent2all: '+str(json.dumps(msg)))
                    if json_enable:
                        ws_clients[i]['ins'].write_message(json.dumps(msg))
                    else:
                        ws_clients[i]['ins'].write_message(msg)
        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            un = self.uid
            if un is not None:
                ulog = CUserLog(un)
                ulog.e(msg)

    def sidInClient(self):
        """
        A function to judge if sid is active
        :return: True/False
        """
        try:
            for i in ws_clients.keys():
                if ws_clients[i]['sid'] == self.sid:
                    return True
            return False

        except Exception as e:
            msg = 'Func: {0} Error on {1}, line {2}:{3}'.format(
                sys._getframe().f_code.co_name, __file__, sys._getframe().f_lineno, str(e))
            slog.e(msg)
            rlog.e(msg)
            un = self.uid
            if un is not None:
                ulog = CUserLog(un)
                ulog.e(msg)
            return None


