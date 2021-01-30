import unittest
import db_test
import handler_test

appTestSuite = unittest.TestSuite()
appTestSuite.addTest(unittest.makeSuite(db_test.TestModels))
appTestSuite.addTest(unittest.makeSuite(handler_test.HandlerTest))

runner = unittest.TextTestRunner(verbosity=2)
runner.run(appTestSuite)