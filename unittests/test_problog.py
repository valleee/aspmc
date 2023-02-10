import unittest

import logging
logging.disable(level=logging.CRITICAL)

import aspmc.config as config
config.config["decos"] = "flow-cutter"
config.config["decot"] = "-1"

from aspmc.programs.problogprogram import ProblogProgram


def cb(program):
    program.tpUnfold()
    program.td_guided_both_clark_completion()

class TestProblog(unittest.TestCase):

    def test_double_declare(self):
        for kc in ["c2d", "miniC2D", "d4", "sharpsat-td", "sharpsat-td-live"]:
            config.config["knowledge_compiler"] = kc
            program = ProblogProgram("", ["./test/test_double_declare.lp"])
            cb(program)
            self.assertEqual(len(program.get_queries()), 1)
            cnf = program.get_cnf()
            results = cnf.evaluate()
            self.assertAlmostEqual(results[0], 0.75)

    def test_smokers_10_or_guide(self):
        for kc in ["c2d", "miniC2D", "d4", "sharpsat-td", "sharpsat-td-live"]:
            config.config["knowledge_compiler"] = kc
            program = ProblogProgram("", ["./test/test_smokers_10.lp"])
            cb(program)
            self.assertEqual(len(program.get_queries()), 10)
            cnf = program.get_cnf()
            results = cnf.evaluate()
            self.assertEqual(len(results), 10)
            expected = [ 
                0.845642576843858, 0.7061644677402408, 0.9080926252529147, 0.9060131023306259,
                0.8940463791307754, 0.6329668151001511, 0.5492261840660287, 0.9165727398797205,
                0.7925499302372165, 0.49999999999999994
            ]
            for i in range(10):
                self.assertAlmostEqual(results[i], expected[i])


    def test_smokers_10_no_guide(self):
        for kc in ["c2d", "miniC2D", "d4", "sharpsat-td", "sharpsat-td-live"]:
            config.config["knowledge_compiler"] = kc
            program = ProblogProgram("", ["./test/test_smokers_10.lp"])
            program.tpUnfold()
            program.clark_completion()
            self.assertEqual(len(program.get_queries()), 10)
            cnf = program.get_cnf()
            results = cnf.evaluate()
            self.assertEqual(len(results), 10)
            expected = [ 
                0.845642576843858, 0.7061644677402408, 0.9080926252529147, 0.9060131023306259,
                0.8940463791307754, 0.6329668151001511, 0.5492261840660287, 0.9165727398797205,
                0.7925499302372165, 0.49999999999999994
            ]
            for i in range(10):
                self.assertAlmostEqual(results[i], expected[i])

    def test_smokers_10_both_guide(self):
        for kc in ["c2d", "miniC2D", "d4", "sharpsat-td", "sharpsat-td-live"]:
            config.config["knowledge_compiler"] = kc
            program = ProblogProgram("", ["./test/test_smokers_10.lp"])
            program.tpUnfold()
            program.td_guided_both_clark_completion()
            self.assertEqual(len(program.get_queries()), 10)
            cnf = program.get_cnf()
            results = cnf.evaluate()
            self.assertEqual(len(results), 10)
            expected = [ 
                0.845642576843858, 0.7061644677402408, 0.9080926252529147, 0.9060131023306259,
                0.8940463791307754, 0.6329668151001511, 0.5492261840660287, 0.9165727398797205,
                0.7925499302372165, 0.49999999999999994
            ]
            for i in range(10):
                self.assertAlmostEqual(results[i], expected[i])

if __name__ == '__main__':
    unittest.main()
