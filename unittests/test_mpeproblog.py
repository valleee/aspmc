import unittest

import logging
logging.disable(level=logging.CRITICAL)

import aspmc.config as config
config.config["decos"] = "flow-cutter"
config.config["decot"] = "-1"
config.config["knowledge_compiler"] = "sharpsat-td"

from aspmc.programs.mpeprogram import MPEProblogProgram


class TestMPEProblog(unittest.TestCase):

    def test_smokers_10_tpUnfold(self):
        program = MPEProblogProgram("", ["./test/test_evidence_10.lp"])
        program.tpUnfold()
        program.td_guided_both_clark_completion()
        cnf = program.get_cnf()
        results = cnf.compile()
        self.assertEqual(len(results), 1)
        expected = 0.00014718216123410307
        self.assertAlmostEqual(results[0].value, expected)
        
    def test_smokers_10_binary(self):
        program = MPEProblogProgram("", ["./test/test_evidence_10.lp"])
        program.binary_cycle_breaking(local=False)
        program.td_guided_both_clark_completion()
        cnf = program.get_cnf()
        results = cnf.compile()
        self.assertEqual(len(results), 1)
        expected = 0.00014718216123410307
        self.assertAlmostEqual(results[0].value, expected)
        program = MPEProblogProgram("", ["./test/test_evidence_10.lp"])
        program.binary_cycle_breaking(local=True)
        program.td_guided_both_clark_completion()
        cnf = program.get_cnf()
        results = cnf.compile()
        self.assertEqual(len(results), 1)
        expected = 0.00014718216123410307
        self.assertAlmostEqual(results[0].value, expected)


    def test_smokers_10_lt(self):
        program = MPEProblogProgram("", ["./test/test_evidence_10.lp"])
        program.less_than_cycle_breaking(opt=False)
        program.td_guided_both_clark_completion()
        cnf = program.get_cnf()
        results = cnf.compile()
        self.assertEqual(len(results), 1)
        expected = 0.00014718216123410307
        self.assertAlmostEqual(results[0].value, expected)
        program = MPEProblogProgram("", ["./test/test_evidence_10.lp"])
        program.less_than_cycle_breaking(opt=True)
        program.td_guided_both_clark_completion()
        cnf = program.get_cnf()
        results = cnf.compile()
        self.assertEqual(len(results), 1)
        expected = 0.00014718216123410307
        self.assertAlmostEqual(results[0].value, expected)

if __name__ == '__main__':
    unittest.main()
