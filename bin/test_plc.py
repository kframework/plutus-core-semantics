#!/usr/bin/env python2

from __future__ import print_function
from subprocess import Popen, PIPE

import json
import os
import pytest
import string
import sys
import tempfile
import xml.dom.minidom

_base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
def base(*args):
    return os.path.join(_base, *args)
def bin(*args):
    return base('bin', *args)

class ExitCode_NotPublic    : pass
class ExitCode_DivByZero    : pass
class ExitCode_TakeFromEmpty: pass
class ExitCode_NonExhaustive: pass

def toIeleExitStatus(expected):
    # Exceptions from iele.md
    FUNC_NOT_FOUND      = hex(1)
    FUNC_WRONG_SIG      = hex(2)
    CONTRACT_NOT_FOUND  = hex(3)
    USER_ERROR          = hex(4)
    OUT_OF_GAS          = hex(5)
    ACCT_COLLISION      = hex(6)
    OUT_OF_FUNDS        = hex(7)
    CALL_STACK_OVERFLOW = hex(8)
    CONTRACT_INVALID    = hex(9)

    if   expected == ExitCode_NotPublic     : return FUNC_NOT_FOUND
    elif expected == ExitCode_DivByZero     : return USER_ERROR
    elif expected == ExitCode_TakeFromEmpty : return USER_ERROR
    elif expected == ExitCode_NonExhaustive : return USER_ERROR
    else                                    : return ""

def toPlutusExitCode(expected):
    if   expected == ExitCode_NotPublic     : return 1
    elif expected == ExitCode_DivByZero     : return 1
    elif expected == ExitCode_NonExhaustive : return 1
    elif expected == ExitCode_TakeFromEmpty : return 1
    else                                    : return 0

def toIeleReturn(expected):
    if type(expected) is int: return [hex(expected)]
    elif expected == False  : return ["0x0"]
    elif expected == True   : return ["0x1"]
    else                    : return []

def toPlutusReturn(expected):
    if type(expected) is int : return str(expected)
    if type(expected) is str : return '#' + expected
    if expected == False     : return "(con Prelude.False .ValList)"
    if expected == True      : return "(con Prelude.True .ValList)"
    return []

def toPlutusArg(arg):
    if type(arg) is int: return "#token(\""  + str(arg) + "\", \"Int\")"
    if type(arg) is str: return "#token(\"#" +      arg + "\", \"ByStr\")"

def toIeleArg(arg):
    if type(arg) is int: return hex(arg)
    if type(arg) is str: return arg

def generate_tests(type):
    passing = [
            ("arith-ops", "Foo", "add",         [19, 23],            42  ),
            ("arith-ops", "Foo", "addFive",     [12],                17  ),
            ("arith-ops", "Foo", "addFiveApp",  [6],                 11  ),
            ("arith-ops", "Foo", "add1923App",  [1234],              42  ),
            ("arith-ops", "Foo", "sub",         [19, 23],           -4   ),
            ("arith-ops", "Foo", "mult",        [19, 23],            437 ),
            ("arith-ops", "Foo", "mult",        [19, -23],          -437 ),
            ("arith-ops", "Foo", "div",         [437, 19],           23  ),
            ("arith-ops", "Foo", "div",         [440, 19],           23  ),
            ("arith-ops", "Foo", "div",         [0,   19],           0   ),
            ("arith-ops", "Foo", "div",         [19, 0],             ExitCode_DivByZero),
            ("arith-ops", "Foo", "mod",         [440, 19],           3   ),
            ("arith-ops", "Foo", "mod",         [-440, 19],          -3  ),
            ("arith-ops", "Foo", "mod",         [0, 19],             0   ),
            ("arith-ops", "Foo", "mod",         [19, 0],             ExitCode_DivByZero),
            ("arith-ops", "Foo", "one",         [],                  1   ),
            ("arith-ops", "Foo", "complex",     [5, 4, 7, 11, 2, 3], 7   ),
            ("arith-ops", "Foo", "complex",     [7, 4, 7, 11, 2, 3], 6   ),

            ("cmp-ops", "Foo", "lessThan",      [12, 12], False),
            ("cmp-ops", "Foo", "lessThan",      [12, 17], True ),
            ("cmp-ops", "Foo", "lessThan",      [17, 12], False),
            ("cmp-ops", "Foo", "lessThanFive",  [17],     False),
            ("cmp-ops", "Foo", "lessThanEq",    [12, 12], True ),
            ("cmp-ops", "Foo", "lessThanEq",    [12, 17], True ),
            ("cmp-ops", "Foo", "lessThanEq",    [17, 12], False),
            ("cmp-ops", "Foo", "greaterThan",   [12, 12], False),
            ("cmp-ops", "Foo", "greaterThan",   [12, 17], False),
            ("cmp-ops", "Foo", "greaterThan",   [17, 12], True ),
            ("cmp-ops", "Foo", "greaterThanEq", [12, 12], True ),
            ("cmp-ops", "Foo", "greaterThanEq", [12, 17], False),
            ("cmp-ops", "Foo", "greaterThanEq", [17, 12], True ),
            ("cmp-ops", "Foo", "equals",        [12, 12], True ),
            ("cmp-ops", "Foo", "equals",        [12, 17], False),
            # ("cmp-ops", "Foo", "myTrue",        [],       True ),

            ("case-simple", "SimpleCase", "boolean",        [13],  19),
            ("case-simple", "SimpleCase", "boolean",        [-13], 23),
            ("case-simple", "SimpleCase", "nonExhaustive",  [13],  19),
            ("case-simple", "SimpleCase", "nonExhaustive",  [-13], ExitCode_NonExhaustive),

            ("recursion",   "Recursion",  "sumToN",     [10, 0], 55),

            ("case-simple", "SimpleCase", "fooBarOrKungFu", [3],       7),
            ("case-simple", "SimpleCase", "fooBarOrKungFu", [-4],      11),

            ("case-simple", "SimpleCase", "testMyNat",      [0],       0),
            ("case-simple", "SimpleCase", "testMyNat",      [1],       -2),
            ("case-simple", "SimpleCase", "testMyNat",      [-4],      0),
            ("case-simple", "SimpleCase", "testMyNat",      [7],       -14),

            ("case-simple", "SimpleCase", "secondArg",      [13, 21],  21),
            ("case-simple", "SimpleCase", "testPair",       [13],      26),

            ("modules", "Bar", "four",                      [5],       4),
            ("modules", "Foo", "four",                      [5],       4),

           ]

    unimplemented = [
            ("ctor-duplicate", "Duplicate", "one",  [], None),

            # Should fail in typechecking phase
            ("module-call-private-indirect", "Foo", "bar", [0], None),
            ("module-call-private-indirect", "Foo", "baz", [0], None),

           ]
    translation_unimplemented = [
            ("ctor-case", "Foo", "bar", [0], 19),
            ("ctor-case", "Foo", "baz", [0], 23),

            # ("bytestring", "Foo", "toByteString",    [0x2345],  "2345"),
            # ("bytestring", "Foo", "toByteString",    [0x0000],  "0000"),
            # ("bytestring", "Foo", "takeByteStringx", [0,   "23"],   ""),
            # ("bytestring", "Foo", "takeByteStringx", [1, "2345"], "23"),
            # ("bytestring", "Foo", "takeByteStringx", [0,  ""],      ""),
            # ("bytestring", "Foo", "takeByteStringx", [2,  ""], ExitCode_TakeFromEmpty),
           ]
    execution_unimplemented = [
            ("arith-ops", "Foo", "notPublic",   [19, 23],            ExitCode_NotPublic),
           ]

    if type == 'translation':
        return (passing                                                                               +
                map(pytest.mark.xfail(reason="unimplemented"), unimplemented)                         +
                map(pytest.mark.xfail(reason="translation unimplemented"), translation_unimplemented) +
                execution_unimplemented
               )
    if type == 'execution':
        return (passing                                                                               +
                translation_unimplemented                                                             +
                map(pytest.mark.xfail(reason="translation unimplemented"), execution_unimplemented)   +
                map(pytest.mark.xfail(reason="unimplemented"), unimplemented)
               )

@pytest.mark.parametrize("file, mod, fct, args, expected", generate_tests('execution'))
def test_execution(file, mod, fct, args, expected):
    krun_args = [bin("kplc"), "run", "execution", base("test/", file +".pre.plc"),
                 "-cMAINMOD=#token(\"" + mod + "\", \"UpperName\")",
                 "-pMAINMOD=printf %s",
                 "-cMAINFCT=#token(\"" + fct + "\", \"LowerName\")",
                 "-pMAINFCT=printf %s",
                 "-cMAINARGS=" + kast_args(args),
                 "-pMAINARGS=printf %s"]
    krun = Popen(krun_args, stdout=PIPE)
    (output, err) = krun.communicate()
    exit_code = krun.wait()

    if 0 == toPlutusExitCode(expected):
        assert extract_exec_output(output) == toPlutusReturn(expected)
    assert exit_code == toPlutusExitCode(expected)

@pytest.mark.parametrize("file, mod, fct, args, expected", generate_tests('translation'))
def test_translation(file, mod, fct, args, expected):
    template = json.load(open(base("test/template.iele.json")))
    account = "0x1000000000000000000000000000000000000000"
    template["pre"][account]["code"] = template["postState"][account]["code"] = base("test/", file + ".iele")
    template["blocks"][0]["transactions"][0]["function"] = mod + "." + fct
    template["blocks"][0]["transactions"][0]["arguments"] = map(toIeleArg, args)
    template["blocks"][0]["results"][0]["status"] = toIeleExitStatus(expected)
    template["blocks"][0]["results"][0]["out"] = toIeleReturn(expected)

    iele_test = { mod : template }

    temp_json = tempfile.NamedTemporaryFile(delete=False)
    json.dump(iele_test, temp_json)
    temp_json.write("\n")
    temp_json.flush()

    blockchain_args = ["./blockchaintest", temp_json.name]
    blockchaintest = Popen(blockchain_args, stdout=PIPE, cwd=base(".build/iele/"))
    (output, err) = blockchaintest.communicate()
    exit_code = blockchaintest.wait()

    def line_is_interesting(l):
        return any(["output" in l, "exit" in l])
    list(map(print, filter(line_is_interesting, output.replace('`<', "\n`<").splitlines())))

    assert exit_code == 0

def kast_args(args):
    if args == []:
        return "`.List{\"tmList\"}`(.KList)"
    else:
        return "tmList("+ toPlutusArg(args[0]) + "," + kast_args(args[1:]) + ")"

def extract_exec_output(config):
    config_xml = xml.dom.minidom.parseString(config)
    output = config_xml.getElementsByTagName('k')[0].firstChild.data
    return output.strip()
