from lark import Lark, Transformer
import re

from sympy import true

from aspmc.parsing.lark_parser import Atom

class NormalRule(object):
    """A class for normal rules.

    If a rule has more than one atom in the head, the head must be an annotated disjunction.
    Then each of the atoms must have a weight.

    Implements a custom `__str__` method.

    Args:        
        head (:obj:`list`): The list of head atoms. May be empty.
        body (:obj:`list`): The list of body atoms. May be empty.
        choice (bool): Whether the rule is a choice rule.

    Attributes:
        head (:obj:`list`): The list of head atoms. May be empty.
        body (:obj:`list`): The list of body atoms. May be empty.
        choice (bool): Whether the rule is a choice rule.
    """
    def __init__(self, head, body, choice):
        self.head = head
        self.body = body if body is not None else []
        self.choice = choice

    def __str__(self):
        res = ""
        if self.head is not None:
            if self.choice:
                res += f"{{{str(self.head[0])}}}"
            else:
                res += f"{str(self.head[0])}"
        if len(self.body) > 0:
            res +=f":-{','.join([str(x) for x in self.body])}."
        else:
            res += "."
        return res

    def __repr__(self):
        return str(self)
    
    def asp_string(self):
        """Generates an ASP representation of the rule.

        Implements a custom `__str__` method.
        
        Returns:
            :obj:`string`: The representation of this rule as an ASP rule.
        """
        return str(self)
    
class WeakConstraint(object):
    """A class for weak constraints.
    
    Weak constraints are constraints whose satisfaction is (un)desirable. 
    This means they have a weight and an empty head.
    Furthermore, every weak constraint may have a list of terms associated with it. 
    The penalty `weight` will be triggered exactly once if any weak constraint with this list of terms
    is not satisfied.

    Implements a custom `__str__` method.

    Args:        
        body (:obj:`list`): The list of body atoms. May be empty.
        weight (int): Whether the rule is a choice rule.
        terms (:obj:`list`): The list of terms that associated with this constraint. May be empty.

    Attributes:
        body (:obj:`list`): The list of body atoms. May be empty.
        weight (int): Whether the rule is a choice rule.
        terms (:obj:`list`): The list of terms that associated with this constraint. May be empty.
    """
    def __init__(self, body, weight, terms):
        self.body = body
        self.weight = weight
        self.terms = terms if terms is not None else []

    def __str__(self):
        res = ":~"
        if len(self.body) > 0:
            res +=f"{','.join([str(x) for x in self.body])}."
        else:
            res += "."
        res += f"[{self.weight}{'' if len(self.terms) == 0 else ','}{','.join([str(x) for x in self.terms])}]"
        return res

    def __repr__(self):
        return str(self)
    
    def asp_string(self):
        """Generates an ASP representation of the rule.

        Implements a custom `__str__` method.
        
        Returns:
            :obj:`string`: The representation of this rule as an ASP rule.
        """
        return str(self)


class Atom(object):
    """A class for atoms.

    Implements a custom `__str__` method.
    
    Args:
        predicate (:obj:`string`): The predicate of the atom.
        inputs (:obj:`list`, optional): The inputs of the atom. 
        These may be strings or other atoms. 
        Defaults to `None`.
        negated (:obj:`bool`, optional): Whether the atom is negated.
        Defaults to `False`.

    Attributes:
        predicate (:obj:`string`): The predicate of the atom.
        inputs (:obj:`list`, optional): The inputs of the atom. 
        These may be strings or other atoms. 
        negated (:obj:`bool`, optional): Whether the atom is negated.
    """
    def __init__(self, predicate, inputs = None, negated=False):
        self.predicate = predicate
        self.inputs = inputs if inputs is not None else []
        def replace_quotes(term):
            if type(term) != Atom:
                return term.replace("'", '"')
            return term
        self.inputs = [ replace_quotes(term) for term in self.inputs ]
        self.negated = negated

    def __str__(self):
        res = ""
        if self.negated:
            res += "not "
        res += f"{self.predicate}"
        if len(self.inputs) > 0:
            res += f"({','.join([ str(term) for term in self.inputs ])})"
        return res

    def __repr__(self):
        return str(self)

    def get_variables(self):
        """Rcursively finds all the variables used in the atom.

        Returns:
            :obj:`list`: The list of variables as strings.
        """
        vars = set()
        for term in self.inputs:
            if type(term) == Atom:
                vars.update(term.get_variables())
            elif re.match(r"[A-Z][a-zA-Z0-9]*", term):
                vars.add(term)
        return vars


class OptProgramTransformer(Transformer):
    """The corresponding OptProgram semantics class for the OPTGRAMMAR grammar.
    
    See the lark documentation for how this works.
    """
    def program(self, ast):  # noqa
        return ast # sort out the comments

    def rule(self, ast):  # noqa
        return ast[0]

    def fact(self, ast): #noqa
        ast = ast[0]
        return NormalRule([ast['atom']], [], ast['choice'])

    def normal_rule(self, ast):  # noqa
        return NormalRule([ast[0]['atom']], ast[1], ast[0]['choice'])
    
    def constraint(self, ast): #noqa
        return NormalRule(None, ast[0], False)
    
    def weakconstraint(self, ast): #noqa
        return WeakConstraint(ast[0], ast[1], ast[2])
    
    def head(self, ast):
        if len(ast) == 3:
            return { 'atom' : ast[1], 'choice' : True }
        else:
            return { 'atom' : ast[0], 'choice' : False }
    
    def body(self, ast):  # noqa
        if len(ast) == 1 and ast[0] == None:
            return None
        return ast

    def atom(self, ast):  # noqa
        negated = str(ast[0]) == 'not'
        if len(ast) == 3:
            return Atom(str(ast[1]), inputs = ast[2], negated = negated)
        else:
            return Atom(str(ast[1]), negated = negated)

    def input(self, ast):  # noqa
        return ast

    def term(self, ast):  # noqa
        ast = ast[0]
        if type(ast) == Atom:
            return ast
    
        if "." in ast and (ast[0] != '"' or ast[-1] != '"'):
            return '"' + ast + '"'
        return str(ast)

    def variable(self, ast): # noqa
        return str(ast[0])

    def weight(self, ast):  # noqa
        return str(ast[0])


GRAMMAR = r'''
    program : rule*

    rule : normal_rule | fact | constraint | weakconstraint

    fact : head "."

    normal_rule : head ":-" body  "."

    constraint : ":-" body  "."
    
    weakconstraint : ":~" body  "." "[" weight ["," input] "]"

    head : ( atom | (OPEN_ANGLE atom CLOSED_ANGLE) )

    body : [ atom ( "," atom )* ]

    OPEN_ANGLE : "{"
    
    CLOSED_ANGLE : "}"
    
    NEGATION : "not"

    atom : [NEGATION] ( /[a-z]([a-zA-Z0-9_])*/ [ "(" input ")" ]  |  "(" /[a-z]([a-zA-Z0-9_])*/ [ "(" input ")" ] ")" )

    input : term ( "," term )*

    term : atom | /[0-9_\/<>=+"-]([a-zA-Z0-9_\/<>=+".-]*)/ | variable 

    variable : /[A-Z][a-zA-Z0-9]*/

    weight :  /[+-]?[1-9]+[0-9]*/ | variable

    COMMENT : "%" /[^\n]+/
    %ignore COMMENT
    %import common.WS
    %ignore WS
    
'''


if __name__ == '__main__':
    import sys
    parser = Lark(GRAMMAR, start='program', parser='lalr', transformer=OptProgramTransformer())

    with open(sys.argv[1]) as infile:
        tree = parser.parse(infile.read())
        for r in tree:
            print(r)