from unconstrained.prelude.tlist import to_untyped_list
from ..prelude import to_list, enumerate1
from typing import List, Set, Union, Literal
from textwrap import indent, dedent

TypeInst = Union[Literal['var'], Literal['par']]

TAB = "\t"
NEWLINE = "\n"
VAR = 'var'
PAR = 'par'


def mz_bracket(expr, newline=False, comment=""):
    start = "(\n" if newline else "("
    end = "\n)" if newline else ")"
    result = start + str(expr) + end

    if comment:
        result = f"% {comment}\n" + result
    return result


def mz_let(bindings, body, bracket=True):
    s = "let\n{\n"
    s += indent(bindings, TAB)
    s += "\n}\nin\n"
    if bracket:
        s += mz_bracket(body, newline=True)
    else:
        s += body
    return s


def mz_and(*exprs, **kwargs):
    """
    Create an AND expression

    mz_and('1>2', 'x = y')

    "(1 > 2) /\\ (x = y)"
    """
    return mz_join(*exprs, separator="/\\", **kwargs)


def mz_or(*exprs, **kwargs):
    """
    Create an OR expression

    mz_or('1>2', 'x = y')

    "(1 > 2) \\/ (x = y)"
    """
    return mz_join(*exprs, separator="\\/", **kwargs)


def mz_sum(*exprs, **kwargs):
    """
    Create a SUM expression

    sum('array','xs[1]', '34')
    yields
    "(array + xs[1] + 34)"
    """
    return mz_join(*exprs, separator="+", **kwargs)


def mz_join(*exprs, separator=",", bracket=True, newline=True):
    """
    Join the given expressions with a seperator

    seperator:
        the seperator to use
    bracket:
        should we bracket each subexpression?
    newline:
        split each item by a newline?
    tab:
        indent subexpressions?

    """
    if bracket:
        list = to_list(*exprs).map(mz_bracket)
    else:
        list = to_list(*exprs)
    
    if not list:
        return None

    if newline:
        separator = NEWLINE + separator + NEWLINE

    body = separator.join(list) + NEWLINE
    return body


def mz_value(x):
    """
    Convert the given argument to a minizinc value
    """    
    
    if hasattr(x, "mz_var"):
        return mz_value(x.mz_var)

    elif isinstance(x, bool):
        return "true" if x else "false"

    elif isinstance(x, int):
        return str(x)

    elif isinstance(x, str):
        return x

    raise ValueError(f"cannot format {x} as a MiniZinc value")


def mz_array(*exprs, comments=None, index=None, newline=False, pad=10):
    """
    Create an ARRAY out of the given expressions

    array(1, 2, 3, newline=True, comments=['a','b','c'], index='N')

    array1d(N, [
        1, # a
        2, # b
        3, # c
    ])

    exprs:
        the expressions that make up the set
    index:
        the index set of the array
    comments:
        an array of comments which will be written next to each member
    newline:
        add a newline after each member?
    """

    list = to_untyped_list(*exprs).map(mz_value, str)
    members = []
    for i, item in enumerate(list):
        string = str(item)
        if comments:
            comment = comments[i]
            string = string.ljust(pad)
            string += f"% {comment}"

        members.append(string)

    if newline or comments:
        open, close, sep = "[\n", "\n]", "\n, "
    else:
        open, close, sep = "[", "]", ", "

    if index:
        open = f"array1d({index}," + open
        close = close + ")"

    expr = open + sep.join(members) + close
    return expr


def mz_range(start = 1, end=1):
    start_ = mz_value(start)
    end_   = mz_value(end)
    range  = f"{start_}..{end_}"
    return range


def mz_set(*exprs, comments=None, newline=False, pad=10):
    """
    Create a SET out of the given expressions
        
    set(1, 2, 3, newline=True, comments=['a','b','c'])

    {
        1, # a
        2, # b
        3, # c
    }

    exprs:
        the expressions that make up the set
    comments:
        an array of comments which will be written next to each member
    newline:
        add a newline after each member?
    """

    list = to_list(*exprs).map(mz_value)
    members = []
    for i, item in enumerate(list):
        string = str(item)
        if comments:
            comment = comments[i]
            string = string.ljust(pad) + f"% {comment}"

        members.append(string)

    if newline or comments:
        open, close, sep = "{\n", "\n}", "\n, "
    else:
        open, close, sep = "{", "}", ", "

    expr = open + sep.join(members) + close
    return expr


def mz_array2d(arr: List[List], x: str = "int", y: str = "int", comments=None):
    """
    Create a 2D ARRAY out of the given expressions

    array2d([[1,2,3],[2,3,4],[3,4,5]])

    "array2d(int, int, [1,2,3,2,3,4,3,4,5])"

    arr:
        the 2D array to convert
    x:
        the first array dimension
    y:
        the second array dimension

    comments (optional):
        an array that gives comments for each row of the array

    """

    array = f"array2d({x}, {y}, [\n"
    n = len(arr)

    def lines(comments=comments):
        for i, row in enumerate1(arr):

            if isinstance(comments, list):
                comment = comments[i - 1]
                yield f"\t%{comment}"

            line = ",".join(map(mz_value, row))
            if i < n:
                line += ","
            yield "\t" + line

    array += "\n".join(list(lines()))
    array += "\n])"
    return array

def mz_array3d(x):
    return x

def mz_constraint(x):
    text = f"constraint {x}"
    return text


def mz_op(left, right, op):
    return f"{mz_value(left)} {op} {mz_value(right)}"


def mz_eq(left, right):
    return mz_op(left, right, "=")


def mz_leq(left, right):
    return mz_op(left, right, "<=")


def mz_geq(left, right):
    return mz_op(left, right, ">=")


def mz_in(left, right):
    return mz_op(left, right, "in")


def mz_implies(left, right):
    return mz_op(left, right, "->")


def mz_implied_by(left, right):
    return mz_op(left, right, "<-")


def mz_iff(left, right):
    return mz_op(left, right, "<->")


def mz_text(x):
    return str(x) + NEWLINE
    

def mz_comment(text):
    return mz_text(f"% {text}")


def mz_call(keyword, name, body, **kwargs):
    args = ",".join(f"{k}:{v}" for k, v in kwargs.items())
    expr = f"{keyword} {name}({args}) = "
    expr += NEWLINE
    expr += indent(body, TAB)
    return expr


def mz_function(name, body, **kwargs):
    return mz_call("function", name, body, **kwargs)


def mz_predicate(name, body, **kwargs):
    return mz_call("predicate", name, body, **kwargs)


class MiniZincModelBuilder:
    """
    Builder for MiniZinc '.mzn' models
    """

    __WIDTH__ = 80


    def __init__(self, text=""):
        self.string = str(text)


    def add_binop(self, name, left, right, op, **kwargs):
        return self.add_constraint(
            name, 
            f"{mz_value(left)} {op} {mz_value(right)}",
            **kwargs
        )


    def add_eq(self, name, left, right, **kwargs):
        return self.add_binop(name, left, right, "=", **kwargs)
        

    def add_leq(self, name, left, right, **kwargs):
        return self.add_binop(name, left, right, "<=", **kwargs)


    def add_geq(self, name, left, right, **kwargs):
        return self.add_binop(name, left, right, ">=", **kwargs)


    def add_in(self, name, left, right, **kwargs):
        return self.add_binop(name, left, right, "in", **kwargs)


    def add_false(self, name, x, **kwargs):
        self.add_eq(x, name, False, **kwargs)


    def add_true(self, name, x, **kwargs):
        self.add_eq(x, name, True, **kwargs)


    def add_multiline_comment(self, x):
        if not x:
            return
        self.add_text(dedent(f"/*\n{x}\n*/"))


    def add_text(self, text):
        self.string += text
        self.string += NEWLINE


    def add_expression(self, text, comment="", pad=20):
        expr = f"{text};"
        
        if comment:
            expr = f"% {comment}\n{expr}"

        self.add_text(expr)
        return expr


    def add_var(self, type, name, value=None, comment="", inline=True):
        """
        Add a decision variable to the model

        type: str
            the type of var to instantiate
            eg: int, bool, set of int, ROAD
        name: str
            the name of the var
        value: optional[any]:
            value to set the variable as
        inline: bool
            if a value was given, should it be assigned inline?
        return: str
            the variable name
        """
                        
        if value is None:
            self.add_expression(f"var {type}: {name}", comment=comment)
        elif inline:
            self.add_expression(f"var {type}: {name} = {mz_value(value)}", comment=comment)
        else:
            self.add_expression(f"var {type}: {name}", comment=comment)
            self.add_eq(name, value)

        return name


    def add_enum(self, name, value=None, comment=""):
        """
        Add an Enumeration to the model
        """
                
        if value is None:
            self.add_expression(f"enum {name}", comment=comment)
        elif isinstance(value, str):
            self.add_expression(f"enum {name} = {value}", comment=comment)
        else:
            self.add_expression(f"enum {name} = {mz_set(value)}", comment=comment)

        return name


    def add_par(self, type, name, value=None, comment=""):
        """
        Add a parameter to the model
        
        type: str
            the type of par to instantiate
        name: str
            the name of the par
        value: optional[any]:
            initiate the par with a value
        return: str
            the variable name
        """
                        
        if value is None:
            self.add_expression(f"{type}: {name}", comment=comment)
        else:
            self.add_expression(f"{type}: {name} = {mz_value(value)}", comment=comment)

        return name


    def add_array(self, *, index:str, name:str, index2:str='', index3:str='', inst : TypeInst = 'par', type:str, value=None, comment="", inline=True, verbose = False):
        """
        Add an Array to the model
        
        name: str
            the name of the array
        type: str
            type of the values
        index: str
            type of the first index
        index2: str
            type of the second index
        index3: str
            type of the third index
        value: optional[any]:
            initiate the array with a value
        inst: [VAR|PAR]:
            var or par?
        
        return: str
            the variable name
        """
                
        if index3:
            atype = f'array3d({index}, {index2}, {index3}'
            array = f'array[{index}, {index2}, {index3}]'
        elif index2:
            array = f'array[{index}, {index2}]'
            atype = f'array2d({index}, {index2}'
        else:
            array = f'array[{index}]'
            atype = f'array(index'
            
        root = f'{array} of {inst} {type}: {name}'
        stem = value
                
        if (value is not None) and not isinstance(value, str):
            stem = mz_array(value)
            if verbose:
                stem = atype + ',' + stem + ')'
        
        if stem is None:
            self.add_expression(root, comment=comment)
        elif not inline:
            self.add_expression(root, comment=comment)
            self.add_eq('', name, stem)
        else:
            self.add_expression(f'{root} = {stem}', comment=comment)

        return name


    def add_global(self, *names):
        """
        Add the the global constraints of the
        given names to the model via 'include'
        statements
        """
        
        for name in names:
            self.add_expression(f'include "{name}.mzn"')


    def add_set(self, *, inst : TypeInst = 'par', name:str, type:str, value=None, min=1, max=None, comment=""):
        """
        Add a Set to the model
                
        type: str
            type of the values
        name: str
            the name of the array
        value: optional[any]:
            initiate the array with a value
        variable : bool:
            var or par?
        return: str
            the variable name
        """
                        
        expr_type = f'{inst} set of {type!s}'

        if max is not None:
            self.add_expression(f"{expr_type}: {name} = {mz_range(min, max)}", comment=comment)
        elif value is None:
            self.add_expression(f"{expr_type}: {name}", comment=comment)
        elif isinstance(value, str):
            self.add_expression(f"{expr_type}: {name} = {value}", comment=comment)
        else:
            self.add_expression(f"{expr_type}: {name} = {mz_set(value)}", comment=comment)

        return name
        

    def add_constraint(self, name, expr, /, *, comment=True, pad=20, enabled=True, disabled=False):

        if not expr:
            return

        if disabled:
            return
        
        if not enabled:
            return

        self.add_expression(
            f"constraint {expr}",
            comment=name if comment else '',
            pad=pad
        )

        return expr


    def add_assign(self, **kwargs):
        """
        Add assignment statements
        """
        for left, right in kwargs.items():
            self.add_expression(f"{left} = {mz_value(right)}")


    def add_implies(self, left, right, comment=""):
        op = mz_implies(left, right)
        self.add_constraint(op, comment=comment)


    def add_comment(self, text):
        self.add_text(f"% {text}")


    def add_newline(self, x = True):
        if x:
            self.string += NEWLINE


    def add_section(self, title):
        chars = len(str(title))
        right = self.__WIDTH__ - chars - 6
        s = ("=" * 4) + " " + str(title) + " " + ("=" * right)
        self.add_newline()
        self.add_comment(s)
        self.add_newline()


    def __str__(self):
        return self.string


    def __repr__(self):
        return "<MiniZinc Model>"
