"""
Program module providing the algebraic progam class.
"""

import re
import numpy as np
import logging

from aspmc.programs.program import Program, UnsupportedException

from aspmc.parsing.clingoparser.clingoext import ClingoRule, Control

from lark import Lark
from aspmc.parsing.lark_parser import GRAMMAR, ProblogTransformer
import aspmc.programs.grounder as grounder

from aspmc.util import *

logger = logging.getLogger("aspmc")

class AlgebraicProgram(Program):
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
    def __init__(self, program_str, program_files, semiring):
        self.semiring = semiring
        self.weights = {}
        self.queries = []
        self.annotated_disjunctions = []
        for path in program_files:
            with open(path) as file_:
                program_str += file_.read()
        # parse
        my_grammar = GRAMMAR + f"%override weight : /{self.semiring.pattern}/ | variable\n"
        parser = Lark(my_grammar, start='program', parser='lalr', transformer=ProblogTransformer())
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
        guess_idx = 0
        new_program = []
        for r in program:
            if isinstance(r, str):
                new_program.append(r)
            elif r.head is not None and r.head[0].predicate == "query":
                atom = r.head[0].inputs[0]
                new_program.append(f"query_atom({atom}):-{atom}.")
            elif r.weights is not None:
                self.annotated_disjunctions.append({})
                variables = set()
                for atom in r.body:
                    variables.update(atom.get_variables())
                if len(variables) == 0:
                    variables.add("none")
                variables = f"set({','.join([ str(x) for x in variables ])})"
                # generate the head, which guesses at most one of the algebriac atoms
                # at the same time generate the rules, which use these atoms
                guess_atoms = []
                for i in range(len(r.weights)):
                    # the guess atom
                    guess_atom = f"algebraic_atom({(guess_idx, i)},{variables},{r.head[i]},"
                    if re.match(r"[A-Z][a-zA-Z0-9]*", str(r.weights[i])):
                        guess_atom += str(r.weights[i]) + ")"
                    else:
                        guess_atom += f"\"{r.weights[i]}\")"
                    guess_atoms.append(guess_atom)
                    # add the rule which uses this guess
                    use_rule = f"{r.head[i]}:-{','.join([str(x) for x in r.body]+[guess_atom])}."
                    new_program.append(use_rule)
                # finally add an atom for the case that none of the other atoms are true
                guess_atom = f"algebraic_atom({(guess_idx, i+1)},{variables},none,\"none\")"
                guess_atoms.append(guess_atom)
                # the rule that ensures that exactly one or none of the atoms are true
                guess_rule = f"{';'.join(guess_atoms)}:-{','.join([str(x) for x in r.body])}."
                new_program.append(guess_rule)
                self.annotated_disjunctions[guess_idx]
                guess_idx += 1
            else:
                new_program.append(r)
        return new_program

    def _process_grounding(self, clingo_control):
        new_objects = []
        symbol_map = {}
        conditioned = {}
        for sym in clingo_control.symbolic_atoms:
            symbol_map[sym.literal] = str(sym.symbol)
        for o in clingo_control.ground_program.objects:
            if isinstance(o, ClingoRule):
                if len(o.head) == 0:
                    head_name = ""
                else:
                    if abs(o.head[0]) in symbol_map:
                        head_name = symbol_map[abs(o.head[0])]
                    else:
                        head_name = ""
                # check if the rule corresponds to a query
                if head_name.startswith("query_atom"):
                    if len(o.body) > 0:
                        self.queries.append(symbol_map[abs(o.body[0])])
                    else:
                        atom = head_name[11:-1]
                        logger.warning(f"Query for atom {atom} was proven true during grounding.")
                        logger.warning(f"Including it has a negative impact on performance.")
                        self.queries.append(atom)
                elif head_name.startswith("algebraic_atom"):
                    # find out the index of the annotated disjunction
                    cur_idx = 16
                    next_idx = head_name.find(",", cur_idx)
                    guess_idx = int(head_name[cur_idx:next_idx])
                    cur_idx = next_idx + 1
                    next_idx = head_name.find(")", cur_idx)
                    # find out which terms were used for grounding
                    cur_idx = next_idx + 6 # == len("),set(")
                    end_idx = head_name.find(')', cur_idx)
                    # now cur_idx is the location of the closing bracket
                    variables = tuple(head_name[cur_idx: end_idx].split(","))
                    self.annotated_disjunctions[guess_idx][variables] = o
                # check if the rule has algebraic_atom in the body
                # these rules are handled later
                elif any([ a > 0 and a in symbol_map and symbol_map[a].startswith("algebraic_atom") for a in o.body ]):
                    for a in o.body:
                        if a > 0 and a in symbol_map and symbol_map[a].startswith("algebraic_atom"):
                            conditioned[a] = o
                else:
                    new_objects.append(o)

        for idx in range(len(self.annotated_disjunctions)):
            for variables in self.annotated_disjunctions[idx]:
                guess_rule = self.annotated_disjunctions[idx][variables]
                sum_all = self.semiring.zero()
                guess_rule.body = [] # make the guess unconditional
                new_objects.append(guess_rule)
                for atom in guess_rule.head:
                    # add all the rules that are conditioned on an algebraic atom
                    if atom in conditioned:
                        new_objects.append(conditioned[atom])
                    # find out the weights
                    head_name = symbol_map[atom]
                    start = len(head_name) - 3
                    while head_name[start] != "\"":
                        start -= 1
                    start += 1
                    if head_name[start:-2] == "none":
                        none_atom = atom
                        continue
                    weight = self.semiring.parse(head_name[start:-2])
                    self.weights[(head_name, True)] = weight
                    # no need to set the weight of the negation to one, since this is the standard
                    sum_all += weight
                # assign the atom that is true when none of the other atoms are true the negation of the sum of the weights
                head_name = symbol_map[none_atom]
                self.weights[(head_name, True)] = self.semiring.negate(sum_all)

        clingo_control.ground_program.objects = new_objects

    def _prog_string(self, program):
        result = ""
        for r in self._exactlyOneOf:
            result += ";".join([ f"{self.weights[(self._internal_name(v),True)]}::{self._external_name(v)}" for v in r ])
            result += ".\n"
        for r in program:
            result += ";".join([self._external_name(v) for v in r.head])
            result += ":-"
            result += ",".join([("not " if v < 0 else "") + self._external_name(abs(v)) for v in r.body])
            result += ".\n"
        for query in self.queries:
            result += f"query({query}).\n"
        return result

    def _finalize_cnf(self):
        weight_list = self.get_weights()
        for v in range(self._max*2):
            self._cnf.weights[to_dimacs(v)] = weight_list[v]
        self._cnf.semirings = [ self.semiring ]
        self._cnf.quantified = [ list(range(1, self._max + 1)) ]

    def get_weights(self):
        query_cnt = max(len(self.queries), 1)
        varMap = { name : var for var, name in self._nameMap.items() }
        weight_list = [ np.full(query_cnt, self.semiring.one(), dtype=self.semiring.dtype) for _ in range(self._max*2) ]
        for (name, phase) in self.weights:
            if phase:
                weight_list[to_pos(varMap[name])] = np.full(query_cnt, self.weights[(name, phase)], dtype=self.semiring.dtype)
            else:
                weight_list[neg(to_pos(varMap[name]))] = np.full(query_cnt, self.weights[(name, phase)], dtype=self.semiring.dtype)
        for i, query in enumerate(self.queries):
            weight_list[neg(to_pos(varMap[query]))][i] = self.semiring.zero()
        return weight_list

    def get_queries(self):
        return self.queries
