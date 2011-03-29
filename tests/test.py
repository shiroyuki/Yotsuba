import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../'))

import testHelpers as h

print """
Test modules for Yotsuba 3 by Juti Noppornpitak

Each test will be repeated twice where the first one is a cold-start test."""

from yotsuba.test import core_net as net
from yotsuba.test import lib_kotoba as kotoba
from yotsuba.test import lib_tegami as tegami
from yotsuba.test import lib_boulevard as boulevard

def test_networking():
    h.doTests(
        "Yotsuba 3 / Core / Networking", 2,
        net.test_http_with_urllib2
    )

def test_tagemi():
    h.doTests(
        "Yotsuba 3 / Libraries / Tegami", 2,
        tegami.test_TegamiBasic
    )

def test_kotoba():
    h.doTests(
        "Yotsuba 3 / Libraries / Kotoba", 2,
        kotoba.test_DOMTreeCreationAuto,
        kotoba.test_DOMTreeCreationManual,
        kotoba.test_queryEngine,
        kotoba.test_queryEngineLegacy,
        kotoba.test_selectingCombinationParserSingle,
        kotoba.test_selectingCombinationParserMultiple,
        kotoba.test_selectingCombinationParserFailureDetection,
        #kotoba.test_construct_xml_doc,
        kotoba.test_custom_pseudo_class
    )

def test_boulevard():
    h.doTests(
        "Yotsuba 4 / Libraries / Boulevard", 2,
        boulevard.test_basic
    )

#test_kotoba()
test_boulevard()

h.textBlock("Finish all tests in %.3f sec" % h.totalUsageTime)
