LOAD_GAE = False
USE_DEFAULT = False

import re

try:
    from google.appengine.api import urlfetch
    LOAD_GAE = True
except:
    pass

if not LOAD_GAE:
    import httplib
    import urllib
    import urllib2

from yotsuba.core import base

class Http(object):
    DEFAULT_QUERYSTRING = u''
    
    @staticmethod
    def do(method, url, data=None, headers=None, bypass_url_encoding=False):
        # Set the optional parameters
        data = data and data or {}
        headers = headers and headers or {}
        
        # Generate the parameters
        params = bypass_url_encoding and data or urllib.urlencode(data)
        
        # Verify the headers
        found_ctype = False
        for k, v in headers.iteritems():
            if k.lower() == "content-type":
                found_ctype = True
                break
        if method.lower() == "post" and not found_ctype:
            headers["Content-type"] = "application/x-www-form-urlencoded"
        
        is_secure = re.search("^https://", url, re.I)
        url = is_secure and url[8:] or url[7:]
        request_path = '/'
        temp = re.split('/', url, 1)
        url = temp[0]
        if len(temp) == 2:
            request_path = '/%s' % temp[1]
        del temp
        
        conn = is_secure and httplib.HTTPSConnection(url) or httplib.HTTPConnection(url)
        conn.request(method.upper(), request_path, params, headers)
        response = conn.getresponse()
        headers = {}
        for k, v in response.getheaders():
            headers[k] = v
        content = response.read()
        conn.close()
        returnee = Response(response.status, headers, content, response.reason)
        
        return returnee
    
    @staticmethod
    def post(url, data=None, headers=None, bypass_url_encoding=False):
        return Http.do("post", url, data, headers, bypass_url_encoding)
    
    @staticmethod
    def get(url, data = None, headers = None, bypass_url_encoding=False):
        response = None
        if LOAD_GAE: # Use Google API
            # Set the optional parameters
            data = data and data or {}
            headers = headers and headers or {}
            
            # Prepare the data
            url = base.convertToUnicode(url)
            query_string = Http.build_data(data)
            
            # Merge data
            url = url + query_string
            
            # Make a call
            raw_response = None
            raw_response = urlfetch.fetch(url)
            if raw_response.status_code < 400:
                response = Response(raw_response.status_code, raw_response.headers, raw_response.content)
            
            # free memory
            del query_string
            del url
            del raw_response
        else:
            response = Http.do("get", url, data, headers, bypass_url_encoding)
        
        return response
    
    @staticmethod
    def build_data(data):
        query_string = Http.DEFAULT_QUERYSTRING
        if data is dict:
            for k, v in data.iteritems():
                if query_string == Http.DEFAULT_QUERYSTRING:
                    query_string += u"?"
                else:
                    query_string += u"&"
                k = base.convertToUnicode(k)
                v = base.convertToUnicode(v)
                query_string = k + u"=" + v
        return query_string

class Response(object):
    def __init__(self, code, headers, content, reason=None):
        '''
        Data Structure for Generic HTTP Responses
        '''
        self.__code = code
        self.__reason = reason
        self.__headers = headers
        self.__content = content
    
    def code(self):
        return self.__code
    
    def reason(self):
        return self.__reason
    
    def headers(self):
        return self.__headers
    
    def content(self):
        return self.__content