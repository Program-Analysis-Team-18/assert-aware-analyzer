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


from utils import Parameter, Assertion, Methods, Classes, Map

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

def get_method_node(method_id: jpamb.jvm.Absolute[jpamb.jvm.MethodID]):
    srcfile = suite.sourcefile(method_id.classname)
    class_name = method_id.classname
    method_name = method_id.extension.name
    
    tree, file_data = parse_tree(srcfile)
    method_node = QueryCursor(get_method_query(method_name)).captures(tree.root_node)["method"][0]
    return method_node

# def has_side_effect(node: Node, class_of_function: Classes) -> bool:
def has_side_effect(node: Node, method_id: jpamb.jvm.Absolute[jpamb.jvm.MethodID]) -> bool:
    SIDE_EFFECT_NODES = ["update_expression", "assignment_expression"]
    # 1. Node type directly indicates mutation
    if node.type in SIDE_EFFECT_NODES:
        return True
    
    # if node.type == "method_invocation":
    #     method: Methods = class_of_function.return_method()
    #     method.method_name()
    #     # convert method_name to methodid
    #     method_node: Node = get_method_node(method_id)
    #     return has_side_effect(method_node, method_id)
        

    # 3. Recursively check children
    for child in node.children:
        if has_side_effect(child, method_id):
            return True

    return False

def get_method_data(method_id: jpamb.jvm.Absolute[jpamb.jvm.MethodID]) -> tuple[str, Methods]:
    srcfile = suite.sourcefile(method_id.classname)
    class_name = method_id.classname
    method_name = method_id.extension.name
    
    tree, file_data = parse_tree(srcfile)
    method_node = get_method_node(method_id)
    
    param_list = parse_parameters_data(method_name, method_node, file_data)
    assertion_list = parse_assertion_data(method_node, file_data)
    
    return class_name.name, Methods(method_id, param_list, assertion_list, has_side_effect(method_node))

def average_assertions_per_method(cls: Classes):
    total_assertions = 0
    for method in cls.methods:
        total_assertions += len(method.assertions)
    if len(cls.methods) > 0:
        cls.average_assertion_per_method = total_assertions / len(cls.methods)
    else:
        cls.average_assertion_per_method = 0.0

def classify_assertion(assertion_node: Node, method_id: jpamb.jvm.Absolute[jpamb.jvm.MethodID]):
    """
    classify_assertion takes in an assertion node, recursively goes through it to check if there exists: update_expression or unary_expression or assignment_expression. If any of these exist, the assertion is classified as side-effect causing
    """
    # goal: return binary_expression or update_expression
    if assertion_node.type != "assert_statement":
        raise ValueError("the node is not an assertion node")
    # if assertion_node
    if has_side_effect(assertion_node, method_id): return True
    else: return False

def debug_print_assertion(method_id, assertion_node):
    # Print header
    print("====================================================")
    print(f"Method: {method_id.classname}.{method_id.extension.name}")
    print(f"method_id: {method_id}")
    
    # Classification
    side = classify_assertion(assertion_node, method_id)
    label = "side-effect" if side else "no-side-effect"
    print(f"Classification: {label}")

    # # Extract assert source text
    # src = file_data[assertion_node.start_byte : assertion_node.end_byte].decode("utf8")
    # print(f"Source: {src}")

    # Tree-sitter AST (your version prints S-expr only via print(node))
    print("AST:")
    print(assertion_node)   # this shows the S-expression in *your* build

    print("====================================================\n")

def start_static_analysis(assertion_mapping: Map):
    
    #count average assertion per method
    for cls in assertion_mapping.classes:
        average_assertions_per_method(cls)
    
    # Start assertion classification
    #for cls in assertion_mapping.classes:
    #    for method in cls.methods:
    #        for assertion in method.assertions:
    #            classify_assertion(assertion_node=assertion.assertion_node)
    

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
    assertion_node_list = []
    
    # We go through all methods in the suite
    for method_id, correct in suite.case_methods():
        class_name, method = get_method_data(method_id)
        assertion_mapping.add_method_to_class(class_name, method)
        
        method_node = get_method_node(method_id)
        assertion_node_list.extend(get_assertion_nodes(method_node))

        # assertion_mapping.print_mapping()
        for assertion in assertion_node_list:
            debug_print_assertion(method_id, assertion)
        
    for class_object in assertion_mapping.classes:
        for method in class_object.methods:
            method_id = method.method_id
            for assertion in method:
                classify_assertion(assertion.assertion_node, method_id)

    start_static_analysis(assertion_mapping)
