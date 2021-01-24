import sys

logs = []

def log (message):
    global logs
    logs.insert(0, {"msg": str(message), "severity": "LOG"})
    logs = logs[0:99]

    print(message)

def elog (message):
    global logs
    logs.insert(0, {"msg": str(message), "severity": "ERROR"})
    logs = logs[0:99]
    print(message, file=sys.stderr)

def slog (message):
    global logs
    logs.insert(0, {"msg": str(message), "severity": "SUCCESS"})
    logs = logs[0:99]
    print(message)

def wlog (message):
    global logs
    logs.insert(0, {"msg": str(message), "severity": "WARNING"})
    logs = logs[0:99]
    print(message)
