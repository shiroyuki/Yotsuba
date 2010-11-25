import os.path
import os
from yotsuba.lib import kotoba

test_basepath = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../../tests')
test_files = [test_basepath + '/test-yotsuba3.xml', test_basepath + '/test-legacy.xml']

def test_DOMTreeCreationAuto():
    '''DOM Tree Creation (auto instantiation)'''
    xmldoc = kotoba.Kotoba(test_files[0])
    rootElement = xmldoc.get_root()
    assert rootElement.name == "statuses"
    assert rootElement.attrs['type'] == "array"
    assert len(rootElement.children()) == 9
    assert rootElement.children()[0].name == "elem_a"
    assert rootElement.children()[2].name == "elem_x"

def test_DOMTreeCreationManual():
    '''DOM Tree Creation (manual instantiation)'''
    xmldoc = kotoba.Kotoba()
    xmldoc.read(test_files[0])
    rootElement = xmldoc.get_root()

def test_queryEngine():
    '''Test Querying Engine'''
    xmldoc = kotoba.Kotoba(test_files[0])
    testcases = [
        ('*', 16),
        ('* *', 15),
        ('statuses *', 15),
        ('status', 3),
        ('* status', 3),
        ('statuses status', 3),
        ('statuses > status', 3),
        ('created_at', 4),
        ('* created_at', 4),
        ('statuses * created_at', 4),
        ('statuses * > created_at', 4),
        ('status created_at', 4),
        ('statuses status created_at', 4),
        ('statuses status > created_at', 2),
        ('statuses > created_at', 0),
        ('status > created_at', 2),
        ('elem_a + elem_x', 2),
        ('elem_a ~ elem_x', 3),
        ('statuses elem_a + elem_x', 2),
        ('[tz]', 1),
        ('created_at[tz]', 1)
    ]
    for testcase in testcases:
        test_query, expected_result = testcase
        targets = xmldoc.get(test_query)
        try:
            assert len(targets) == expected_result
        except:
            raise Exception("Failed on querying: %s (number of result: %d/%d)" % (test_query, len(targets), expected_result))
    targets = xmldoc.get('statuses')
    assert len(targets) == 1                # check if it gets the root element (1)
    assert targets[0] == xmldoc.get_root()   # check if it gets the root element (2)

def test_queryEngineLegacy():
    '''Test Querying Engine with the legacy test cases'''
    xmldoc = kotoba.Kotoba(test_files[1])
    testcases = {
        'c': 1,
        'common': 4,
        'common[id]': 0,
        'common[name]': 2,
        'common[id=c]': 0,
        'common[name=c]': 1,
        'common[name|=utf]': 1,
        'common[name~=of]': 1,
        'common[name~=f]': 0,
        'common[name^=utf-8\']': 1,
        'common[name^=utf]': 1,
        'common[name$=buddha]': 1,
        'common[name$=dha]': 1,
        'common[name*=am]': 1,
        '[name=c]': 1,
        'root l1 > l2b > l3b': 1,
        'root l1 > l2b > l3c': 1,
        'l1 l2b > l3c > l4c': 1,
        'root > c > c2': 1,
        'root > c c2': 1,
        'root > * > * > common': 2,
        'root common': 4,
        'root common, root common, root common': 4,
        'root * common': 4,
        'root *': 33,
        'root:root': 1,
        'root:root:empty': 0,
        'c:root': 0,
        'b:empty': 1,
        'c:empty': 0,
        '*': 34,
        'c common': 1,
        'c + d': 1,
        'c ~ e': 2,
        'e common': 3,
        'e > common': 1,
        'e > e1 common': 1,
        'd common': 0,
        'c c1, e e11': 2,
    }
    #testcases = {'common[name~=f]': 0}
    #testcases = {'c:root': 0}
    #testcases = {'common[name~=of]': 1}
    #testcases = {'l1 l2b > l3c > l4c':1}
    for test_query, expected_result in testcases.iteritems():
        targets = xmldoc.get(test_query)
        try:
            assert len(targets) == expected_result
        except:
            raise Exception("Failed on querying: %s (number of result: %d/%d)" % (test_query, len(targets), expected_result))

def test_selectingCombinationParserSingle():
    '''Selecting Combination Parser with Single Combinator'''
    
    # Normal cases
    combinators = None
    combinators = kotoba.Combinators("settings > options[type] option:first")
    assert len(combinators) == 1
    assert len(combinators[0]) == 3
    assert ':' not in combinators[0][0].name
    assert '[' not in combinators[0][0].name
    assert ']' not in combinators[0][0].name
    assert 'type' in combinators[0][1].attributes
    assert len(combinators[0][2].pseudo_classes) == 1
    assert combinators[0][0].combo_method == kotoba.Selector.look_for_children
    assert combinators[0][1].combo_method == kotoba.Selector.look_for_descendants

def test_selectingCombinationParserFailureDetection():
    '''Selecting Combination Parser with Possible Failures'''
    
    # Failed cases
    try:
        kotoba.Combinators("")
        raise
    except kotoba.KotobaInvalidSelectionException:
        assert "Detected empty selector (1)"
    try:
        kotoba.Combinators(",")
        raise
    except kotoba.KotobaInvalidSelectionException:
        assert "Detected empty selector (2)"
    try:
        kotoba.Combinators("> abc")
        raise
    except kotoba.KotobaInvalidSelectionException:
        assert "Detected invalid combiners (leading)"
    try:
        kotoba.Combinators("abc $")
        raise
    except kotoba.KotobaInvalidSelectionException:
        assert "Detected invalid combiners (tailing)"
    try:
        kotoba.Combinators("> $")
        raise
    except kotoba.KotobaInvalidSelectionException:
        assert "Detected invalid combiners (next to each other)"

def test_selectingCombinationParserMultiple():
    '''Selecting Combination Parser with Multiple Combinator'''
    
    # Normal cases
    combinators = None
    combinators = kotoba.Combinators("settings > options[type], error[attr=val]:pseudo, error[attr1][attr2]:p1:p2, :p1:p2[attr1][attr2]:p3, staticPath file:first")
    assert len(combinators) == 5
    assert len(combinators[0]) == 2
    assert ':' not in combinators[0][0].name
    assert '[' not in combinators[0][0].name
    assert ']' not in combinators[0][0].name
    assert 'type' in combinators[0][1].attributes
    assert combinators[0][0].combo_method == kotoba.Selector.look_for_children
    assert combinators[3][0].name == None