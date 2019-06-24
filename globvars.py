from log import CRootLog, CStreamLog
DEBUG = True
DisableCAPTCHA = False
MAXROOMNUM = 30  # no more than 60 players.
REDIRECT_TIME = 5

# put the variable in to app.py leads to import loop
ws_clients = dict()

# switching faction
swfac = {'red': 'black', 'black': 'red'}

settings = {
    'debug': DEBUG,
    'static_path': 'pages',
    'template_path': 'pages/templates',
    'login_url': '/login',
    'cookie_secret': 'c0e99c609faf0ec28b02778f2',
    # cookie_secret: a fixed random value. For better security,
    # it could be generated individually and store the value to the database's the user's row.
    "xsrf_cookies": True,
}

ws_settings = {
    'ip': '127.0.0.1',
    'port': 23334,
    'page': 'data',
}


rlog = CRootLog()
slog = CStreamLog()

