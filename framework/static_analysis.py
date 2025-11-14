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


def parse_tree(srcfile: Path) -> tuple[Tree, bytes]:
    with open(srcfile, "rb") as f:
        file_data: bytes = f.read()
        tree = parser.parse(file_data)
    
    return tree, file_data

def get_class_query(class_name: str) -> Query:
    return Query(JAVA_LANGUAGE,
        f="""
        (class_declaration 
            name: ((identifier) @class-name 
                (#eq? @class-name "{class_name}"))) @class
        """,
    )

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
    print("assertion callled")
    assert_q = Query(JAVA_LANGUAGE, """(assert_statement) @assert""")
    assertion_list = []

    # def __init__(self, absolute_start_line: Point, absolute_end_line: Point, assert_node: Node, classification: str):
    for name, nodelist in QueryCursor(assert_q).captures(method_node).items():
        for assertion_node in nodelist:
            start_line, start_col = assertion_node.start_point
            end_line, end_col = assertion_node.end_point
            classification: str = "unclassified"
            assertion_list.append(Assertion(start_line, end_line, assertion_node, classification))

    return assertion_list

"""?TODO?"""
def run_query( query: Query):
    pass

def get_method_data(methodid: jpamb.jvm.AbsMethodID) -> tuple[str, Methods]:
    srcfile = suite.sourcefile(methodid.classname)
    class_name = methodid.classname
    method_name = methodid.extension.name
    
    tree, file_data = parse_tree(srcfile)
    method_node = QueryCursor(get_method_query(method_name)).captures(tree.root_node)["method"][0]
    
    param_list = parse_parameters_data(method_name, method_node, file_data)
    assertion_list = parse_assertion_data(method_node, file_data)
    
    return class_name, Methods(method_name, param_list, assertion_list)



    
    
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
    
    # Initialize the global assertion mapping
    global assertion_mapping
    assertion_mapping = Map()
    
    # We go through all methods in the suite
    for methodid, correct in suite.case_methods():
        class_name, method = get_method_data(methodid)
        print(f"Class: {class_name}, Method: {method}")
        #exit(0)
        if assertion_mapping.return_class(class_name) is None:
            class_obj = Classes(class_name)
            assertion_mapping.add_class(class_obj)
        else:
            if assertion_mapping.return_class(class_name).return_method(method.method_name) is None:
                assertion_mapping.return_class(class_name).add_method(method)
                
    print("Assertion Mapping:")
    print(assertion_mapping)
        # the first one jpamb.cases.Arrays.arrayContent:()V
        #if (str(methodid)  == "jpamb.cases.Arrays.arrayContent:()V"):
        #    print(f"methodid REACHED: {methodid}")
        #    class_name, method = get_method_data(methodid)
            
