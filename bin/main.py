"""
Main module providing the application logic.
"""

import matplotlib.pyplot as plt
import sys
# from textwrap import dedent
from collections import OrderedDict
import clingo
#import clingoext
from pprint import pprint
import networkx as nx
#import lib.htd_validate
#from groundprogram import ClingoRule
import os
import inspect
import logging
import subprocess
import math
from itertools import product

# set library path

# TODO: fixme
src_path = os.path.abspath(os.path.realpath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, os.path.realpath(os.path.join(src_path, '../..')))

src_path = os.path.realpath(os.path.join(src_path, '../../lib'))

libs = ['htd_validate', 'clingoparser', 'nesthdb', 'htd']

if src_path not in sys.path:
    for lib in libs:
        sys.path.insert(0, os.path.join(src_path, lib))


logger = logging.getLogger("asp2sat")
logging.basicConfig(format='[%(levelname)s] %(name)s: %(message)s', level="INFO")

from htd_validate.utils import hypergraph, graph

import clingoext
from clingoext import ClingoRule
#from htd_validate.decompositions import *
from dpdb import reader
from dpdb import treedecomp
from dpdb.problems.sat_util import *
from dpdb.writer import StreamWriter

import wfParse

class AppConfig(object):
    """
    Class for application specific options.
    """

    def __init__(self):
        self.eclingo_verbose = 0


class Application(object):
    """
    Application class that can be used with `clingo.clingo_main` to solve CSP
    problems.
    """

    def __init__(self):
        self.program_name = "clingoext"
        self.version = "0.0.1"
        self.config = AppConfig()
        # store the weights of literals here
        self._weights = {}
        # store the clauses here
        self._clauses = []
        # store the projected variables
        self._projected = set()
        # remember one variable for x <_t x' regardless of t
        self._lessThan = {}
        self._done = {}

    def _read(self, path):
        if path == "-":
            return sys.stdin.read()
        with open(path) as file_:
            return file_.read()

    def primalGraph(self):
        return self._graph

    def var2idx(self, var):
        sym = clingo.parse_term(var)
        if sym in self.control.symbolic_atoms:
            lit = self.control.symbolic_atoms[sym].literal
            return self._atomToVertex[lit]
        return 0

    def new_var(self, name):
        self._max += 1
        self._nameMap[self._max] = name
        return self._max

    def remove_tautologies(self):
        tmp = []
        for o in self.control.ground_program.objects:
            if isinstance(o, ClingoRule) and set(o.head).intersection(set(o.body)) == set():
                tmp.append(o)
        self.control.ground_program.objects = tmp

    def _generatePrimalGraph(self):
        self.remove_tautologies()
        self._graph = hypergraph.Hypergraph()
        self._program = []
        self._atomToVertex = {} # htd wants succinct numbering of vertices / no holes
        self._vertexToAtom = {} # inverse mapping of _atomToVertex 
        self._max = 0
        self._nameMap = {}
        unary = []
        for o in self.control.ground_program.objects:
            if isinstance(o, ClingoRule):
                o.atoms = set(o.head)
                o.atoms.update(tuple(map(abs, o.body)))
                self._program.append(o)
                if len(o.atoms) > 1:
                    for a in o.atoms.difference(self._atomToVertex):	# add mapping for atom not yet mapped
                        self._atomToVertex[a] = self.new_var(str(a))
                        self._vertexToAtom[self._max] = a
                    self._graph.add_hyperedge(tuple(map(lambda x: self._atomToVertex[x], o.atoms)))
                else:
                    unary.append(o)
        for o in unary:
            for a in o.atoms.difference(self._atomToVertex):	# add mapping for atom not yet mapped
                self._atomToVertex[a] = self.new_var(str(a))
                self._vertexToAtom[self._max] = a

        #for sym in self.control.symbolic_atoms:
        #    print(self._atomToVertex[sym.literal], sym.symbol)
        #    print(sym.literal, sym.symbol)


    # write a single clause
    # connective == 0 -> and, == 1 -> or, == 2 -> impl, == 3 -> iff, == 4 -> *, == 5 -> +
    def clause_writer(self, p, c1 = 0, c2 = 0, connective = 0):
        if c1 == 0:
            c1 = self.new_var(f"{p}'sc[0]")
        if c2 == 0:
            c2 = self.new_var(f"{p}'sc[1]")
        if connective == 0:
            self._clauses.append([-p, c1])
            self._clauses.append([-p, c2])
            self._clauses.append([p, -c1, -c2])
        if connective == 1:
            self._clauses.append([p, -c1])
            self._clauses.append([p, -c2])
            self._clauses.append([-p, c1, c2])
        if connective == 2:
            self._clauses.append([p, c1])
            self._clauses.append([p, -c2])
            self._clauses.append([-p, -c1, c2])
        if connective == 3:
            c = self.clause_writer(p, c1 = self.new_var(f"{c1}->{c2}"), c2 = self.new_var(f"{c2}->{c1}"))
            self.clause_writer(c[0], c1 = c1, c2 = c2, connective = 2)
            self.clause_writer(c[1], c1 = c2, c2 = c1, connective = 2)
        if connective == 4:
            self._clauses.append([-p, c1])
            self._clauses.append([-p, c2])
            self._clauses.append([p, -c1])
            self._clauses.append([p, -c2])
        if connective == 5:
            self._clauses.append([p, -c1])
            self._clauses.append([p, -c2])
            self._clauses.append([-p, c1, c2])
            self._clauses.append([-p, -c1, -c2])
        return (c1, c2)

    def _tdguidedReduction(self, local = False):
        # temporary copy of the program, will be empty after the first pass
        program = list(self._program)
        #take care of the rules
        for r in program:
            if not r.choice: 
                self._clauses.append(list(map(lambda x: self._atomToVertex[abs(x)]*(-1 if x < 0 else 1), r.head + [-x for x in r.body])))
            else: 
                self._projected.add(self._atomToVertex[r.head[0]])

    # function for debugging
    def model_to_names(self):
        f = open("model.out")
        f.readline()
        for i in range(668):
            vs = [int(x) for x in f.readline().split() if abs(int(x)) < 25 and int(x) != 0]
            def getName(v):
                for sym in self.control.symbolic_atoms:
                    if sym.literal == v:
                        return str(sym.symbol)
            #with open("out.cnf", "a") as file_out:
            #    file_out.write(" ".join([str(-v) for v in vs]) + " 0\n")
            #for v in vs:
            #    print(("-" if v < 0 else "")+getName(self._vertexToAtom[abs(v)]))
            print(":-" + ", ".join([("not " if v > 0 else "") + getName(self._vertexToAtom[abs(v)]) for v in vs]) + ".")

    def write_dimacs(self, stream):
        stream.write(f"p cnf {self._max} {len(self._clauses)}\n".encode())
        stream.write(("pv " + " ".join([str(v) for v in self._projected]) + " 0\n" ).encode())
        #f = open("named.cnf", "w")
        for c in self._clauses:
            stream.write((" ".join([str(v) for v in c]) + " 0\n" ).encode())
            #f.write(" ".join([self._nameMap[v] if v > 0 else f"-{self._nameMap[abs(v)]}" for v in c]) + "\n")
        #for (a, w) in self._weights.items():
        #    stream.write(f"w {a} {w}\n".encode())

    def print_prog(self, rules):
        def getName(v):
            for sym in self.control.symbolic_atoms:
                if sym.literal == v:
                    return str(sym.symbol)
        def printrule(r):
            res = ""
            res += ";".join([getName(v) for v in r.head])
            res += ":-"
            res += ",".join([("not " if v < 0 else "") + getName(abs(v)) for v in r.body])
            return res
        for t in self._td.nodes:
            print(t)
            for r in rules[t]:
                print(printrule(r))
                

    def encoding_stats(self):
        num_vars, edges= cnf2primal(self._max, self._clauses)
        p = subprocess.Popen([os.path.join(src_path, "htd/bin/htd_main"), "--seed", "12342134", "--input", "hgr"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        logger.debug("Running htd")
        StreamWriter(p.stdin).write_gr(num_vars, edges)
        p.stdin.close()
        tdr = reader.TdReader.from_stream(p.stdout)
        p.wait()
        logger.debug("Parsing tree decomposition")
        td = treedecomp.TreeDecomp(tdr.num_bags, tdr.tree_width, tdr.num_orig_vertices, tdr.root, tdr.bags, tdr.adjacency_list, None)
        logger.info(f"Tree decomposition #bags: {td.num_bags} tree_width: {td.tree_width} #vertices: {td.num_orig_vertices} #leafs: {len(td.leafs)} #edges: {len(td.edges)}")
            
        
    def main(self, clingo_control, files):
        """
        Entry point of the application registering the propagator and
        implementing the standard ground and solve functionality.
        """
        if not files:
            files = ["-"]

        self.control = clingoext.Control()

        for path in files:
            self.control.add("base", [], self._read(path))

        self.control.ground()

        logger.info("------------------------------------------------------------")
        logger.info("   Grounded Program")
        logger.info("------------------------------------------------------------")
        #pprint(self.control.ground_program.objects)
        logger.info("------------------------------------------------------------")
        logger.info(self.control.ground_program)
        logger.info("------------------------------------------------------------")

        self._generatePrimalGraph()
        
        self._tdguidedReduction(local = False)
        #parser = wfParse.WeightedFormulaParser()
        #sem = wfParse.WeightedFormulaSemantics(self)
        #wf = "#(1)*(pToS(1)*#(0.3) + npToS(1)*#(0.7))*(pToS(2)*#(0.3) + npToS(2)*#(0.7))*(pToS(3)*#(0.3) + npToS(3)*#(0.7))*(fToI(1,2)*#(0.8215579576173441) + nfToI(1,2)*#(0.17844204238265593))*(fToI(2,1)*#(0.2711032358362575) + nfToI(2,1)*#(0.7288967641637425))*(fToI(2,3)*#(0.6241213691538402) + nfToI(2,3)*#(0.3758786308461598))*(fToI(3,1)*#(0.028975606030084644) + nfToI(3,1)*#(0.9710243939699154))*(fToI(3,2)*#(0.41783665133679737) + nfToI(3,2)*#(0.5821633486632026))"
        #parser.parse(wf, semantics = sem)
        with open('out.cnf', mode='wb') as file_out:
            self.write_dimacs(file_out)
        self.encoding_stats()

if __name__ == "__main__":
    sys.exit(int(clingoext.clingo_main(Application(), sys.argv[1:])))
