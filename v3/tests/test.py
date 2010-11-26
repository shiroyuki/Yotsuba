import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../'))

import testHelpers as h

print """
Test modules for Yotsuba 3 by Juti Noppornpitak

Each test will be repeated twice where the first one is a cold-start test."""

from yotsuba.test import lib_kotoba as kotoba
from yotsuba.test import core_net as net

h.doTests(
    "Yotsuba 3 / Core / Networking",
    net.test_http_with_urllib2
)
h.doTests(
    "Yotsuba 3 / Libraries / Kotoba",
    kotoba.test_DOMTreeCreationAuto,
    kotoba.test_DOMTreeCreationManual,
    kotoba.test_queryEngine,
    kotoba.test_queryEngineLegacy,
    kotoba.test_selectingCombinationParserSingle,
    kotoba.test_selectingCombinationParserMultiple,
    kotoba.test_selectingCombinationParserFailureDetection
)

h.textBlock("Finish all tests in %.3f sec" % h.totalUsageTime)
