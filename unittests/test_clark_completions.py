import unittest

import logging
logging.disable(level=logging.CRITICAL)

import aspmc.parsing.clingoparser.clingoext as clingoext

from aspmc.programs.program import Program, UnsupportedException
import aspmc.programs.grounder as grounder

from aspmc import config
config.config["decos"] = "flow-cutter"
config.config["decot"] = "-1"

def cb_none(program):
    program.tpUnfold()
    program.clark_completion()

def cb_ors(program):
    program.tpUnfold()
    program.td_guided_clark_completion()

def cb_both(program):
    program.tpUnfold()
    program.td_guided_both_clark_completion()
    
def cb_adaptive(program):
    program.tpUnfold()
    program.td_guided_both_clark_completion(adaptive = True, latest = True)

class TestClarkCompletions(unittest.TestCase):

    def test_none(self):
        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_2n.lp"])
        program = Program(control)
        cb_none(program)
        self.assertEqual(len(program.get_queries()), 0)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2**100)

        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_constraints.lp"])
        program = Program(control)
        cb_none(program)
        self.assertEqual(len(program.get_queries()), 0)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 1)

        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_cycle.lp"])
        program = Program(control)
        cb_none(program)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2)

        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_cycle2.lp"])
        program = Program(control)
        cb_none(program)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 4)

    
    def test_ors(self):
        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_2n.lp"])
        program = Program(control)
        cb_ors(program)
        self.assertEqual(len(program.get_queries()), 0)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2**100)

        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_constraints.lp"])
        program = Program(control)
        cb_ors(program)
        self.assertEqual(len(program.get_queries()), 0)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 1)

        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_cycle.lp"])
        program = Program(control)
        cb_ors(program)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2)

        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_cycle2.lp"])
        program = Program(control)
        cb_ors(program)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 4)

    
    def test_both(self):
        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_2n.lp"])
        program = Program(control)
        cb_both(program)
        self.assertEqual(len(program.get_queries()), 0)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2**100)

        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_constraints.lp"])
        program = Program(control)
        cb_both(program)
        self.assertEqual(len(program.get_queries()), 0)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 1)

        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_cycle.lp"])
        program = Program(control)
        cb_both(program)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2)

        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_cycle2.lp"])
        program = Program(control)
        cb_both(program)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 4)


    def test_adaptive(self):
        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_2n.lp"])
        program = Program(control)
        cb_adaptive(program)
        self.assertEqual(len(program.get_queries()), 0)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2**100)

        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_constraints.lp"])
        program = Program(control)
        cb_adaptive(program)
        self.assertEqual(len(program.get_queries()), 0)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 1)

        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_cycle.lp"])
        program = Program(control)
        cb_adaptive(program)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2)

        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_cycle2.lp"])
        program = Program(control)
        cb_adaptive(program)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 4)

    def test_recomplete_2n(self):
        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_2n.lp"])
        program = Program(control)
        program.tpUnfold()

        max_bef = program._max
        program.clark_completion()
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2**100)

        program.td_guided_clark_completion()
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2**100)

        program.td_guided_both_clark_completion()
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2**100)

        program.td_guided_both_clark_completion(adaptive = True, latest = True)
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2**100)

    def test_recomplete_constraints(self):
        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_constraints.lp"])
        program = Program(control)
        program.tpUnfold()

        max_bef = program._max
        program.clark_completion()
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 1)

        program.td_guided_clark_completion()
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 1)

        program.td_guided_both_clark_completion()
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 1)

        program.td_guided_both_clark_completion(adaptive = True, latest = True)
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 1)

    def test_recomplete_cycle(self):
        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_cycle.lp"])
        program = Program(control)
        program.tpUnfold()

        max_bef = program._max
        program.clark_completion()
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2)

        program.td_guided_clark_completion()
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2)

        program.td_guided_both_clark_completion()
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2)

        program.td_guided_both_clark_completion(adaptive = True, latest = True)
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 2)

    def test_recomplete_cycle2(self):
        control = clingoext.Control()
        grounder.ground(control, program_files= ["./test/test_cycle2.lp"])
        program = Program(control)
        program.tpUnfold()

        max_bef = program._max
        program.clark_completion()
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 4)

        program.td_guided_clark_completion()
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 4)

        program.td_guided_both_clark_completion()
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 4)

        program.td_guided_both_clark_completion(adaptive = True, latest = True)
        self.assertEqual(program._max, max_bef)
        cnf = program.get_cnf()
        results = cnf.evaluate()
        self.assertEqual(results[0], 4)



if __name__ == '__main__':
    unittest.main()
