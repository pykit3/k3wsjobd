import doctest

import k3wsjobd


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(k3wsjobd))
    return tests
