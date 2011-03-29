import os
from yotsuba.core import fs
from yotsuba.lib import boulevard as b

test_basepath = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../../tests')
test_db_location = "%s/test.db" % test_basepath
test_db = "sqlite:///%s" % test_db_location

class User(b.DataInterface):
    id          = b.DataColumn(b.Integer, primary_key=True)
    name        = b.DataColumn(b.String)
    password    = b.DataColumn(b.String)

def test_basic():
    ctrl = b.DataStore(test_db)
    ctrl.raise_DI_mapping_err = False
    ctrl.register(User)
    ctrl.connect()
    ctrl.save(
        User(name="shiroyuki", password="7c1"),
        User(name="kanata", password="8c1")
    )
    query = ctrl.find(User)
    users = query.all()
    assert query.count() > 0
    assert query.count() == len(users)
    assert users[0].name == 'shiroyuki' and users[0].password == "7c1"
    assert users[1].name == 'kanata' and users[1].password == "8c1"
    ctrl.disconnect()
    os.unlink(test_db_location)