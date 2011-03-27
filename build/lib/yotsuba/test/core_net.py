from yotsuba.core import net

def test_http_with_urllib2():
    r = net.Http.get('http://www.shiroyuki.com/')
    assert r.code() == 200
    assert len(r.headers()) > 0
    assert len(r.content().strip()) > 0