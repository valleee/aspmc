import unittest

import logging
logging.disable(level=logging.CRITICAL)

import aspmc.config as config
config.config["decos"] = "flow-cutter"
config.config["decot"] = "-1"
config.config["knowledge_compiler"] = "sharpsat-td"

from aspmc.programs.optprogram import OptProgram


class TestOptProgram(unittest.TestCase):

    def test_small_tpUnfold(self):
        program = OptProgram("", ["./test/test_small_opt.lp"])
        program.tpUnfold()
        program.td_guided_both_clark_completion()
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(len(results), 1)
        expected = 3
        self.assertAlmostEqual(results[0].value, expected)
        
        
    def test_small_binary(self):
        program = OptProgram("", ["./test/test_small_opt.lp"])
        program.binary_cycle_breaking(local = False)
        program.td_guided_both_clark_completion()
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(len(results), 1)
        expected = 3
        self.assertAlmostEqual(results[0].value, expected)
        program = OptProgram("", ["./test/test_small_opt.lp"])
        program.binary_cycle_breaking(local = True)
        program.td_guided_both_clark_completion()
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(len(results), 1)
        expected = 3
        self.assertAlmostEqual(results[0].value, expected)

    def test_small_lt(self):
        program = OptProgram("", ["./test/test_small_opt.lp"])
        program.less_than_cycle_breaking(opt = False)
        program.td_guided_both_clark_completion()
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(len(results), 1)
        expected = 3
        self.assertAlmostEqual(results[0].value, expected)
        program = OptProgram("", ["./test/test_small_opt.lp"])
        program.less_than_cycle_breaking(opt = True)
        program.td_guided_both_clark_completion()
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(len(results), 1)
        expected = 3
        self.assertAlmostEqual(results[0].value, expected)

if __name__ == '__main__':
    unittest.main(buffer=True)
