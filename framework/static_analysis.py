#!/usr/bin/env python3
import logging
import tree_sitter
import tree_sitter_java
from tree_sitter import Tree, Query, QueryCursor, Node
import jpamb
import sys
from jpamb import model
from pathlib import Path
from typing import List

from utils import Parameter, Assertion, Method, Classes, Map

"""Refactor"""
def parse_tree(srcfile: Path) -> tuple[Tree, bytes]:
    with open(srcfile, "rb") as f:
        file_data: bytes = f.read()
        tree = parser.parse(file_data)
    
    return tree, file_data

"""Refactor"""
def get_class_query(class_name: str) -> Query:
    return Query(JAVA_LANGUAGE,
        f"""
        (class_declaration 
            name: ((identifier) @class-name 
                (#eq? @class-name "{class_name}"))) @class
        """,
    )

"""Refactor"""
def get_method_query(method_name: str):
    return Query(JAVA_LANGUAGE,
        f"""
        (method_declaration 
            name: ((identifier) @method-name
                (#eq? @method-name "{method_name}"))) @method
        """,
    )

"""Refactor"""
def parse_parameters_data(method_name: str, method_node: Node, file_data: bytes) -> List[Parameter]:
    parameters_q = Query(JAVA_LANGUAGE, """(formal_parameters) @params""")
    
    param_list: List[Parameter]  = []

    for name, nodelist in QueryCursor(parameters_q).captures(method_node).items():
        for formal_params in nodelist:
            for formal_param in formal_params.children:
                if formal_param.type != "formal_parameter":
                    continue
                ptype = formal_param.child_by_field_name("type")
                pname = formal_param.child_by_field_name("name")
                ptype_text = file_data[ptype.start_byte : ptype.end_byte].decode("utf8")
                pname_text = file_data[pname.start_byte : pname.end_byte].decode("utf8")
                if (pname and ptype):
                    param_list.append(Parameter(pname_text, ptype_text))
                else: raise ValueError("a parameter is missing")
    return param_list

"""Refactor"""
def parse_assertion_data(method_node: Node, file_data: bytes) -> List[Assertion]:
    assert_q = Query(JAVA_LANGUAGE, """(assert_statement) @assert""")
    assertion_list = []

    for name, nodelist in QueryCursor(assert_q).captures(method_node).items():
        for assertion_node in nodelist:
            start_line, start_col = assertion_node.start_point
            end_line, end_col = assertion_node.end_point
            # this will replaced by classify_assertion()
            classification: str = "unclassified"
            assertion_list.append(Assertion(start_line, end_line, assertion_node, classification))

    return assertion_list

"""Refactor"""
def get_assertion_nodes(method_node: Node)-> List[Node]:
    assert_q = Query(JAVA_LANGUAGE, """(assert_statement) @assert""")
    assertion_node_list = []
    for name, nodelist in QueryCursor(assert_q).captures(method_node).items():
        for assertion_node in nodelist:
            # # have to print here cause otherwise the AST is not shown
            # print(assertion_node)
            # print(assertion_node.type)
            assertion_node_list.append(assertion_node)
    
    return assertion_node_list

"""Refactor"""
def get_method_node(method_id: jpamb.jvm.Absolute[jpamb.jvm.MethodID]):
    srcfile = suite.sourcefile(method_id.classname)
    class_name = method_id.classname
    method_name = method_id.extension.name

    tree, file_data = parse_tree(srcfile)
    method_node = QueryCursor(get_method_query(method_name)).captures(tree.root_node)["method"][0]
    return method_node

"""Refactor"""
def get_method_data(method_id: jpamb.jvm.Absolute[jpamb.jvm.MethodID]) -> tuple[str, Method]:
    srcfile = suite.sourcefile(method_id.classname)
    class_name = method_id.classname
    method_name = method_id.extension.name

    tree, file_data = parse_tree(srcfile)
    method_node = get_method_node(method_id)

    param_list = parse_parameters_data(method_name, method_node, file_data)
    assertion_list = parse_assertion_data(method_node, file_data)

    return class_name.name, Method(method_id, param_list, assertion_list)

"""refactor merge with find_child"""
def check_update_assignment_expression(assertion_node: Node) -> bool:
    side_effect_nodes = ["update_expression", "assignment_expression"]

    if assertion_node.type in side_effect_nodes:
        return True

    for child in assertion_node.children:
        if check_update_assignment_expression(child):
            return True

    return False

"""Refactor"""
def find_child(node: Node, matching_child: List[str]) -> List[Node]:
    result: List[Node] = []

    def walk(n: Node):
        if n.type in matching_child:
            result.append(n)

        for child in n.children:
            walk(child)

    walk(node)
    return result

"""Refactor"""
def get_method_invocation_chain(method: Method, cls: Classes):
    result = []
    visited = set()

    srcfile = suite.sourcefile(method.method_id.classname)
    tree, file_data = parse_tree(srcfile)
    root = tree.root_node

    inv_q = Query(
        JAVA_LANGUAGE,
        """
        (method_invocation
            name: (identifier) @invoked)
        """
    )

    def explore(node):
        captures = QueryCursor(inv_q).captures(node)

        for capname, nodelist in captures.items():
            for n in nodelist:
                invoked_name = file_data[n.start_byte:n.end_byte].decode("utf8")

                if not cls.method_present(invoked_name):
                    continue

                callee = cls.return_method(invoked_name)
                mid = callee.method_id

                if mid in visited:
                    continue

                visited.add(mid)
                result.append(mid)

                callee_node = QueryCursor(get_method_query(invoked_name)).captures(root)["method"][0]

                explore(callee_node)

    start_node = QueryCursor(get_method_query(method.method_id.extension.name)).captures(root)["method"][0]

    explore(start_node)
    return result

"""Refactor"""
def check_invoked_method_side_effecting(invocation_chain: List[jpamb.jvm.Absolute[jpamb.jvm.MethodID]], cls: Classes):
    for method_id in invocation_chain:
        method = cls.return_method(method_id.extension.name)
        if method.change_state:
            return True
    return False

"""Refactor"""
def update_methods_change_state_field(cls: Classes):
    for method in cls.methods:
        method.change_state = check_update_assignment_expression(get_method_node(method.method_id))

    for method in cls.methods:
        if not method.change_state:
            invocation_chain = get_method_invocation_chain(method, cls)
            method.change_state =  check_invoked_method_side_effecting(invocation_chain, cls)

def classify_assertion(assertion: Assertion, cls: Classes) -> str:

    #check for side effect
    if check_update_assignment_expression(assertion.assertion_node):
        return "side_effect"
    else:
        for child in find_child(assertion.assertion_node, ["method_invocation"]):
            method = cls.return_method((child.children[0].text).decode("utf8"))
            if method.change_state:
                return "side_effect"

        # check for tautology and contradiction if not already listed as side effect
        not_useless_types = [
            "identifier",
            "field_access",
            "array_access",
            "method_invocation"
        ]
        if len(find_child(assertion.assertion_node, not_useless_types)) is 0:
            return "useless"

    return "unclassified"

"""Refactor"""
def average_assertions_per_method(cls: Classes):
    total_assertions = 0
    for method in cls.methods:
        total_assertions += len(method.assertions)
    if len(cls.methods) > 0:
        cls.average_assertion_per_method = total_assertions / len(cls.methods)
    else:
        cls.average_assertion_per_method = 0.0

"""Refactor"""
def start_static_analysis(assertion_mapping: Map):
    
    #count average assertion per method
    for cls in assertion_mapping.classes:
        average_assertions_per_method(cls)

    # Start assertion classification
    for cls in assertion_mapping.classes:
        for method in cls.methods:
            for assertion in method.assertions:
                assertion.classification = classify_assertion(assertion, cls)

def setup():
    global JAVA_LANGUAGE
    JAVA_LANGUAGE = tree_sitter.Language(tree_sitter_java.language())
    global parser
    parser = tree_sitter.Parser(JAVA_LANGUAGE)

    global log
    log = logging
    log.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    setup()

    # Resolve the path of the suite
    path_file: Path = Path(".").resolve()
    suite = model.Suite(Path(path_file))
    
    # Initialize the assertion mapping
    assertion_mapping = Map()

    # We go through all methods in the suite to do a first mapping
    for method_id, correct in suite.case_methods():
        class_name, method = get_method_data(method_id)
        assertion_mapping.add_method_to_class(class_name, method)
    # We update the change_state flag of the methods
    for cls in assertion_mapping.classes:
        update_methods_change_state_field(cls)

    assertion_mapping.print_mapping()
    start_static_analysis(assertion_mapping)
    assertion_mapping.print_mapping()

