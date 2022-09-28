"""
Program module providing the optimizing progam class.
"""

import re
import numpy as np
import logging

from aspmc.programs.program import Program, UnsupportedException

from aspmc.parsing.clingoparser.clingoext import ClingoRule, Control

from lark import Lark
from aspmc.parsing.lark_optparser import GRAMMAR, OptProgramTransformer, WeakConstraint
import aspmc.programs.grounder as grounder

import aspmc.semirings.minplus as semiring

from aspmc.util import *
from aspmc.programs.naming import *

logger = logging.getLogger("aspmc")

class OptProgram(Program):
    """A class for programs that state optimization problems. 

    Should be specified using only normal rules, choice rules and weak constraints.

    Grounding of these programs (and subclasses thereof) should follow the following strategy:

    * `_prepare_grounding(self, program)` should take the output of the parser 
        (i.e. a list of rules and special objects) and process all the rules and special objects
        transforming them either into other rules or into strings that can be given to the grounder.
    * the output of `_prepare_grounding(self, program)` is transformed to one program string via

            '\\n'.join([ str(r) for r in program ])
        
        This string will be given to the grounder, which produces a clingo control object.
    * `_process_grounding(self, clingo_control)` should take this clingo control object and process the
        grounding in an appropriate way (and draw some information from it optionally about weights, special objects).
        The resulting processed clingo_control object must only know about the 
        rules that should be seen in the base program class.

    Thus, subclasses can override `_prepare_grounding` and `_process_grounding` (and optionally call the superclass methods) 
    to handle their extras. See aspmc.programs.meuprogram or aspmc.programs.smprogram for examples.

    Args:
        program_str (:obj:`string`): A string containing a part of the program. 
        May be the empty string.
        program_files (:obj:`list`): A list of string that are paths to files which contain programs. May be an empty list.

    Attributes:
        semiring (:obj:`module`): The semiring module to be used. 
        weights (:obj:`dict`): The dictionary from atom names to their weight.
    """
    def __init__(self, program_str, program_files):
        self.semiring = semiring
        self.weights = {}
        for path in program_files:
            with open(path) as file_:
                program_str += file_.read()
        # parse
        my_grammar = GRAMMAR
        parser = Lark(my_grammar, start='program', parser='lalr', transformer=OptProgramTransformer())
        program = parser.parse(program_str)

        # ground
        clingo_control = Control()
        self._ground(clingo_control, program)

        # initialize the superclass
        Program.__init__(self, clingo_control = clingo_control)

    def _ground(self, clingo_control, program):
        # do the grounding in three steps:
        # 1. transform the parsed rules into asp rules
        program = self._prepare_grounding(program)
        # 2. give the asp rules to the grounder
        clingo_str = '\n'.join([ str(r) for r in program ])
        grounder.ground(clingo_control, program_str = clingo_str, program_files = [])
        # 3. take care of possible extras
        self._process_grounding(clingo_control)

    def _prepare_grounding(self, program):
        new_program = []
        for r in program:
            if isinstance(r, str):
                new_program.append(r)
            elif isinstance(r, WeakConstraint):
                new_program.append(f"{INTERNAL_PENALTY}({','.join([ str(term) for term in r.terms ])},{r.weight}):-{','.join([ str(atom) for atom in r.body ])}.")
            else:
                new_program.append(r)
        return new_program

    def _process_grounding(self, clingo_control):
        symbol_map = {}
        for sym in clingo_control.symbolic_atoms:
            symbol_map[sym.literal] = str(sym.symbol)
        for o in clingo_control.ground_program.objects:
            if isinstance(o, ClingoRule):
                head_name = "" if len(o.head) == 0 else symbol_map[abs(o.head[0])]
                # check if the rule corresponds to a weak constraint
                if head_name.startswith(INTERNAL_PENALTY):
                    # find out the penalty of this atom
                    idx = head_name.rfind(",")
                    penalty = semiring.MinPlusFloat(float(head_name[idx+1:-1]))
                    self.weights[head_name] = penalty
                

    def _prog_string(self, program):
        # TODO: return the weak constraint program again
        result = ""
        for v in self._guess:
            result += f"{{{self._external_name(v)}}}.\n"
        for r in program:
            result += ";".join([self._external_name(v) for v in r.head])
            if len(r.body) > 0:
                result += ":-"
                result += ",".join([("not " if v < 0 else "") + self._external_name(abs(v)) for v in r.body])
            result += ".\n"
        return result

    def _finalize_cnf(self):
        weight_list = self.get_weights()
        for v in range(self._max*2):
            self._cnf.weights[to_dimacs(v)] = weight_list[v]
        self._cnf.semirings = [ self.semiring ]
        self._cnf.quantified = [ list(range(1, self._max + 1)) ]

    def get_weights(self):
        query_cnt = 1
        varMap = { name : var for var, name in self._nameMap.items() }
        weight_list = [ np.full(query_cnt, self.semiring.one(), dtype=self.semiring.dtype) for _ in range(self._max*2) ]
        for name in self.weights:
            weight_list[to_pos(varMap[name])] = np.full(query_cnt, self.weights[name], dtype=self.semiring.dtype)
        return weight_list

    def get_queries(self):
        return []

    # def solve_clingo(self):
    #     import clingo
    #     control = clingo.Control()
    #     control.add("base", [], self._prog_string(self._program))
    #     control.ground([('base', [])])
