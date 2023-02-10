import unittest

import logging
logging.disable(level=logging.CRITICAL)

import aspmc.config as config
config.config["decos"] = "flow-cutter"
config.config["decot"] = "-1"

from aspmc.programs.algebraicprogram import AlgebraicProgram, UnsupportedException

import aspmc.semirings.probabilistic as probabilistic
import aspmc.semirings.maxplus as maxplus



def cb(program):
    program.tpUnfold()
    program.td_guided_both_clark_completion()

class TestAProblog(unittest.TestCase):

    def test_maxplus_both(self):
        config.config["knowledge_compiler"] = "c2d"
        program = AlgebraicProgram("", ["./test/test_maxplus_both.lp"], maxplus)
        cb(program)
        self.assertEqual(len(program.get_queries()), 0)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertAlmostEqual(results[0].value, 2)

    def test_maxplus_either(self):
        config.config["knowledge_compiler"] = "c2d"
        program = AlgebraicProgram("", ["./test/test_maxplus_either.lp"], maxplus)
        cb(program)
        self.assertEqual(len(program.get_queries()), 0)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertAlmostEqual(results[0].value, 2)

    
    def test_maxplus_annotated_disjunctions(self):
        config.config["knowledge_compiler"] = "c2d"
        program = AlgebraicProgram("0.5::a;0.2::b.", [], maxplus)
        cb(program)
        self.assertEqual(len(program.get_queries()), 0)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertAlmostEqual(results[0].value, 0.5)


if __name__ == '__main__':
    unittest.main(buffer=True)
