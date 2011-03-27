from yotsuba.lib import tegami
from yotsuba.lib import kotoba

def test_TegamiBasic():
    class TegamiBasic(tegami.Tegami):
        def __init__(self, x, y, z):
            self.w = kotoba.Kotoba()
            self.x = x
            self.y = y
            self.z = z
    
    tb = TegamiBasic(1, 2, 'a')
    print tb.to_json()
    print tb.to_xml()