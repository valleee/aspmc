"""
Program module providing the algebraic progam class.
"""

import re
import numpy as np
import logging
import math

from aspmc.parsing.clingoparser.clingoext import ClingoRule, Control

from aspmc.programs.algebraicprogram import AlgebraicProgram

import aspmc.semirings.probabilistic as probabilistic
import aspmc.semirings.maxtimes as maxtimes


from aspmc.util import *

logger = logging.getLogger("aspmc")

class MPEProblogProgram(AlgebraicProgram):
    """A class for programs with weights over semirings. 

    Should be specified in ProbLog syntax, but allows negations and negative cycles.

    Annotated disjunctions are theoretically supported over any semiring but the results are likely to 
    be wrong over semirings that differ from the probabilistic semiring.

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
        program_str (:obj:`string`): A string containing a part of the program in ProbLog syntax. 
        May be the empty string.
        program_files (:obj:`list`): A list of string that are paths to files which contain programs in 
        ProbLog syntax that should be included. May be an empty list.
        semiring (:obj:`module`): The semiring module to be used. See aspmc.semiring for how they should look.

    Attributes:
        semiring (:obj:`module`): The semiring module to be used. 
        weights (:obj:`dict`): The dictionary from atom names to their weight.
        queries (:obj:`list`): The list of atoms to be queries in their string representation.
    """
    def __init__(self, program_str, program_files):
        self.evidence = {}
        AlgebraicProgram.__init__(self, program_str, program_files, probabilistic)
        self.semiring = maxtimes
        self.original_weights = self.weights
        self.weights = { name : maxtimes.MaxTimesFloat(weight) for name, weight in self.weights.items() }

    def _prepare_grounding(self, program):
        new_program = []
        for r in program:
            if isinstance(r, str):
                new_program.append(r)
            elif r.head is not None and r.head[0].predicate == "evidence":
                atom = r.head[0].inputs[0]
                new_program.append(f":-{'' if atom.negated else 'not'} {str(atom)[4:] if atom.negated else str(atom)}.")
                phase = atom.negated
                atom.negated = False
                self.evidence[str(atom)] = phase
            else:
                new_program.append(r)
        return super()._prepare_grounding(new_program)

    def _prog_string(self, program):
        program = [ r for r in program if len(r.head) > 0 ]
        result = AlgebraicProgram._prog_string(self, program)
        for name in self.evidence:
            result += "evidence("
            if self.evidence[name]:
                result += "\\+"
            result += f"{name}).\n"
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
        for (name, phase) in self.weights:
            if phase:
                weight_list[to_pos(varMap[name])] = np.full(query_cnt, self.weights[(name, phase)], dtype=self.semiring.dtype)
            else:
                weight_list[neg(to_pos(varMap[name]))] = np.full(query_cnt, self.weights[(name, phase)], dtype=self.semiring.dtype)
        return weight_list

    def get_queries(self):
        return self.queries
