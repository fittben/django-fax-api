# Python 3 compatible ESL wrapper
import _ESL

# Python 3 compatibility - replace apply() with function calls
def apply(func, args):
    return func(*args)

class ESLevent:
    def __init__(self, *args):
        self.this = _ESL.new_ESLevent(*args)
        
    def __del__(self):
        if hasattr(self, 'this'):
            _ESL.delete_ESLevent(self.this)
    
    def serialize(self, *args):
        return _ESL.ESLevent_serialize(self.this, *args)
    
    def setPriority(self, *args):
        return _ESL.ESLevent_setPriority(self.this, *args)
    
    def getHeader(self, *args):
        result = _ESL.ESLevent_getHeader(self.this, *args)
        if result and hasattr(result, 'decode'):
            return result.decode('utf-8')
        return result if result else ""
    
    def getBody(self, *args):
        result = _ESL.ESLevent_getBody(self.this, *args)
        if result and hasattr(result, 'decode'):
            return result.decode('utf-8')
        return result if result else ""
    
    def getType(self, *args):
        return _ESL.ESLevent_getType(self.this, *args)
    
    def addBody(self, *args):
        return _ESL.ESLevent_addBody(self.this, *args)
    
    def addHeader(self, *args):
        return _ESL.ESLevent_addHeader(self.this, *args)
    
    def delHeader(self, *args):
        return _ESL.ESLevent_delHeader(self.this, *args)


class ESLconnection:
    def __init__(self, *args):
        self.this = _ESL.new_ESLconnection(*args)
    
    def __del__(self):
        if hasattr(self, 'this'):
            _ESL.delete_ESLconnection(self.this)
    
    def socketDescriptor(self, *args):
        return _ESL.ESLconnection_socketDescriptor(self.this, *args)
    
    def connected(self, *args):
        return _ESL.ESLconnection_connected(self.this, *args)
    
    def getInfo(self, *args):
        return _ESL.ESLconnection_getInfo(self.this, *args)
    
    def send(self, *args):
        return _ESL.ESLconnection_send(self.this, *args)
    
    def sendRecv(self, *args):
        return _ESL.ESLconnection_sendRecv(self.this, *args)
    
    def api(self, *args):
        result = _ESL.ESLconnection_api(self.this, *args)
        if result:
            event = ESLevent.__new__(ESLevent)
            event.this = result
            return event
        return None
    
    def bgapi(self, *args):
        result = _ESL.ESLconnection_bgapi(self.this, *args)
        if result:
            event = ESLevent.__new__(ESLevent)
            event.this = result
            return event
        return None
    
    def sendEvent(self, *args):
        return _ESL.ESLconnection_sendEvent(self.this, *args)
    
    def sendMSG(self, *args):
        return _ESL.ESLconnection_sendMSG(self.this, *args)
    
    def recvEvent(self, *args):
        return _ESL.ESLconnection_recvEvent(self.this, *args)
    
    def recvEventTimed(self, *args):
        return _ESL.ESLconnection_recvEventTimed(self.this, *args)
    
    def filter(self, *args):
        return _ESL.ESLconnection_filter(self.this, *args)
    
    def events(self, *args):
        return _ESL.ESLconnection_events(self.this, *args)
    
    def execute(self, *args):
        return _ESL.ESLconnection_execute(self.this, *args)
    
    def executeAsync(self, *args):
        return _ESL.ESLconnection_executeAsync(self.this, *args)
    
    def setAsyncExecute(self, *args):
        return _ESL.ESLconnection_setAsyncExecute(self.this, *args)
    
    def setEventLock(self, *args):
        return _ESL.ESLconnection_setEventLock(self.this, *args)
    
    def disconnect(self, *args):
        return _ESL.ESLconnection_disconnect(self.this, *args)