import unittest

import logging
logging.disable(level=logging.CRITICAL)

import aspmc.config as config
config.config["decos"] = "flow-cutter"
config.config["decot"] = "-1"

from aspmc.programs.meuprogram import MEUProblogProgram



def cb(program):
    program.tpUnfold()
    program.td_guided_both_clark_completion()

class TestMEUProblog(unittest.TestCase):
    
    def test_meu_semantics(self):
        config.config["knowledge_compiler"] = "c2d"
        config.config["constrained"] = "XD"
        program = MEUProblogProgram("", ["./test/test_meu_simple.lp"])
        cb(program)
        self.assertEqual(len(program.get_queries()), 0)
        cnf = program.get_cnf()
        results = cnf.compile()
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0].value, 6.0)
        self.assertEqual(results[0].decisions, 3)


if __name__ == '__main__':
    unittest.main()
