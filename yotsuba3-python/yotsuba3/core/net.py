try:
    from httplib2 import Http
except:
    raise Exception("Required module httplib2 not found")

LOAD_GAE = False

try:
    from google.appengine.api import urlfetch
    LOAD_GAE = True
except:
    pass

from yotsuba3.core import base

class http(object):
    DEFAULT_QUERYSTRING = u''
    
    @staticmethod
    def get(url, data = None, headers = None, cacheLocation = None):
        
        # Set the optional parameters
        data = data is None and {} or data
        headers = headers is None and {} or headers
        
        # Prepare the data
        url = base.convertToUnicode(url)
        queryString = http.buildData(data)
        
        # Merge data
        url = url + queryString
        
        # Make a call
        raw_response = None
        response = None
        if LOAD_GAE:
            raw_response = urlfetch.fetch(url)
            response = raw_response.content
        else:
            req = Http()
            response = req.request(url)[1]
            
            # free memory
            del req
        
        # free memory
        del queryString
        del url
        del raw_response
        
        return response
    
    @staticmethod
    def buildData(data):
        queryString = http.DEFAULT_QUERYSTRING
        if data is dict:
            for k, v in data.iteritems():
                if queryString == http.DEFAULT_QUERYSTRING:
                    queryString += u"?"
                else:
                    queryString += u"&"
                k = base.convertToUnicode(k)
                v = base.convertToUnicode(v)
                queryString = k + u"=" + v
        return queryString