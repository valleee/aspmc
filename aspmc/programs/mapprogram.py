#!/usr/bin/env python3

"""
Maximum A Posteriori Program module specializing the TwoAlgebraicProgam class.
"""
import logging

from aspmc.parsing.clingoparser.clingoext import Control

from aspmc.programs.problogprogram import ProblogProgram
from aspmc.programs.twoalgebraicprogram import TwoAlgebraicProgram
from lark import Lark
from aspmc.parsing.lark_parser import GRAMMAR, ProblogTransformer
from aspmc.util import *

import aspmc.semirings.maxtimesdecisions as first_semiring
import aspmc.semirings.probabilistic as second_semiring

logger = logging.getLogger("aspmc")

class MAPProblogProgram(TwoAlgebraicProgram, ProblogProgram):
    """A class for Maximum A Posteriori programs. 

    The syntax for these programs is the same as for ProbLog in MAP mode. 
    This means that the probabilistic part is specified as usual,
    evidence atoms `a`, i.e. atoms that are true, must be given as `evidence(a).` and
    the MAP query atoms `q`, whose assignment should be maximized over should be given as `query(q).`.

    Note that these atoms can be any atom and need not be probabilistic facts.

    Subclasses `TwoAlgebraicProgram` since it is a second level problem.

    Overrides the `_prepare_grounding` method to deal with MAP query atoms and evidence.

    Args:
        program_str (:obj:`string`): A string containing a part of the program in MAP ProbLog syntax. 
        May be the empty string.
        program_files (:obj:`list`): A list of string that are paths to files which contain programs in 
        MAP ProbLog syntax that should be included. May be an empty list.
    """
    def __init__(self, program_str, program_files):
        self.semiring = second_semiring
        self.weights = {}
        self.evidence = {}
        self.map_variables = []
        self.queries = []
        self.annotated_disjunctions = []
        for path in program_files:
            with open(path) as file_:
                program_str += file_.read()
        # parse the program
        my_grammar = GRAMMAR + f"%override weight : /{self.semiring.pattern}/ | variable\n"
        parser = Lark(my_grammar, start='program', parser='lalr', transformer=ProblogTransformer())
        program = parser.parse(program_str)

        # ground the program
        clingo_control = Control()
        self._ground(clingo_control, program)

        self.map_variables = self.queries
        self.queries = []

        # set the weights
        first_weight_list = {}
        first_semiring.names = [ name for name in self.map_variables ]
        # weights for the maxtimes semiring
        for i, name in enumerate(self.map_variables):
            if name in self.weights:
                first_weight_list[(name, True)] = first_semiring.MaxTimesFloat(self.weights[name], 2**i)
                first_weight_list[(name, False)] = first_semiring.MaxTimesFloat(1.0 - self.weights[name], 0)
            else:
                first_weight_list[(name, True)] = first_semiring.MaxTimesFloat(1.0, 2**i)
                first_weight_list[(name, False)] = first_semiring.MaxTimesFloat(1.0, 0)
        # weights for the probability semiring
        second_weight_list = {}
        for name in self.weights:
            if name in self.map_variables:
                continue
            # # we only want the weights for those probabilistic atoms which are *not* map_variables
            # # get the original atom name
            # cur_idx = 16
            # next_idx = name.find(")", cur_idx)
            # cur_idx = next_idx + 6 # == len("),set(")
            # next_idx = name.find(')', cur_idx)
            # cur_idx = next_idx + 2 # == len("),")
            # start_idx = cur_idx
            # open_brackets = 0
            # open_quotes = False
            # while name[cur_idx] != ',' or open_brackets > 0 or open_quotes:
            #     if name[cur_idx] == '"':
            #         open_quotes = not open_quotes
            #     elif name[cur_idx] == '(':
            #         open_brackets += 1
            #     elif name[cur_idx] == ')':
            #         open_brackets -= 1
            #     cur_idx += 1
            # end_idx = cur_idx
            # if True or not name[start_idx:end_idx] in self.map_variables:
            second_weight_list[(name, True)] = self.weights[name]
            second_weight_list[(name, False)] = 1.0 - self.weights[name]
        TwoAlgebraicProgram.__init__(self, clingo_control, first_semiring, second_semiring, first_weight_list, second_weight_list, "lambda w : w", self.queries)

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
        result = ""
        for v in self._guess:
            result += f"{self.weights[self._internal_name(v)]}::{self._external_name(v)}.\n"
        for name in self.evidence:
            result += "evidence("
            if self.evidence[name]:
                result += "\\+"
            result += f"{name}).\n"
        for r in program:
            if not r.head:
                continue
            result += ";".join([self._external_name(v) for v in r.head])
            if len(r.body) > 0:
                result += ":-"
                result += ",".join([("\\+ " if v < 0 else "") + self._external_name(abs(v)) for v in r.body])
            result += ".\n"
        for query in self.map_variables:
            result += f"query({query}).\n"
        return result

    def to_pita(self):
        result = """:- use_module(library(pita)).
:- pita.
:- begin_lpad.
"""
        for v in self._guess:
            if self._external_name(v) in self.map_variables:
                result += "map_query "
            result += f"{self.weights[self._internal_name(v)]}::{self._external_name(v)}.\n"
        if self.evidence:
            result += "ev :- "
            result += ",".join([("\\+" if self.evidence[name] else "") + name for name in self.evidence ])
            result += ".\n"
        for r in self._program:
            if not r.head:
                continue
            result += ";".join([self._external_name(v) for v in r.head])
            if len(r.body) > 0:
                result += ":-"
                result += ",".join([("\\+ " if v < 0 else "") + self._external_name(abs(v)) for v in r.body])
            result += ".\n"
        result += ":- end_lpad."
        return result