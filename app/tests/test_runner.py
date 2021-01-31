import unittest
import db_test
import handler_test

import seeder
import os
# TODO Remove seeder, data must be exists
cwd = os.getcwd()
nwd = cwd.replace('/tests', '')
os.chdir(nwd)
seeder.seed_all()
os.chdir(cwd)

appTestSuite = unittest.TestSuite()
appTestSuite.addTest(unittest.makeSuite(db_test.TestModels))
appTestSuite.addTest(unittest.makeSuite(handler_test.HandlerTest))

runner = unittest.TextTestRunner(verbosity=2)
runner.run(appTestSuite)