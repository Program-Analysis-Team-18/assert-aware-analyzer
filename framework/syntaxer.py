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

from core import Parameter, Assertion, Method, Classes, Map, Classification

def parse_local_variables(method_node: Node, file_data: bytes) -> List[Parameter]:
    local_params = []

    local_q = Query(JAVA_LANGUAGE, """
        (local_variable_declaration
            type: (_) @vtype
            declarator: (variable_declarator
                name: (identifier) @vname))
    """)

    captures = QueryCursor(local_q).captures(method_node)

    # Group captures by their nodes to maintain pairing
    capture_list = []
    for capname, nodes in captures.items():
        for node in nodes:
            capture_list.append((capname, node))

    # Sort by byte position to maintain order
    capture_list.sort(key=lambda x: x[1].start_byte)

    current_type = None
    for capname, node in capture_list:
        if capname == "vtype":
            current_type = file_data[node.start_byte:node.end_byte].decode("utf8")
        elif capname == "vname":
            var_name = file_data[node.start_byte:node.end_byte].decode("utf8")
            local_params.append(Parameter(var_name, current_type))

    return local_params

def parse_tree(srcfile: Path) -> tuple[Tree, bytes]:
    with open(srcfile, "rb") as f:
        file_data: bytes = f.read()
        tree = parser.parse(file_data)
    
    return tree, file_data

def get_class_query(class_name: str) -> Query:
    return Query(JAVA_LANGUAGE,
        f"""
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

def get_method_queries():
    return Query(JAVA_LANGUAGE, """
        (method_declaration) @method
    """)

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

def parse_assertion_data(method_node: Node, file_data: bytes) -> List[Assertion]:
    assert_q = Query(JAVA_LANGUAGE, """(assert_statement) @assert""")
    assertion_list = []

    for name, nodelist in QueryCursor(assert_q).captures(method_node).items():
        for assertion_node in nodelist:
            start_point = assertion_node.start_point
            end_point = assertion_node.end_point

            classification = "unclassified"
            assertion_list.append(Assertion(start_point, end_point, assertion_node, classification))

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

def get_method_data(method_name: str, method_node: Node, file_data: bytes) -> Method:

    param_list = parse_parameters_data(method_name, method_node, file_data)
    assertion_list = parse_assertion_data(method_node, file_data)
    local_variables = parse_local_variables(method_node, file_data)

    return Method(method_name, method_node, param_list, assertion_list, local_variables)

def check_update_assignment_expression(assertion_node: Node) -> bool:
    side_effect_nodes = ["update_expression", "assignment_expression"]

    if assertion_node.type in side_effect_nodes:
        return True

    for child in assertion_node.children:
        if check_update_assignment_expression(child):
            return True

    return False

def find_child(node: Node, matching_child: List[str]) -> List[Node]:
    result: List[Node] = []

    def walk(n: Node):
        if n.type in matching_child:
            result.append(n)

        for child in n.children:
            walk(child)

    walk(node)
    return result

def get_method_invocation_chain(method: Method, cls: Classes) -> List[str]:
    result = []
    visited = set()

    class_file_path = cls.class_file_path
    tree, file_data = parse_tree(Path(class_file_path))
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
                mid = callee.method_name

                if mid in visited:
                    continue

                visited.add(mid)
                result.append(mid)

                callee_node = QueryCursor(get_method_query(invoked_name)).captures(root)["method"][0]

                explore(callee_node)

    start_node = method.method_node

    explore(start_node)
    return result

def check_invoked_method_side_effecting(invocation_chain: List[str], cls: Classes):
    for method_name in invocation_chain:
        method: Method = cls.return_method(method_name)
        if method.change_state:
            return True
    return False

def update_methods_change_state_field(cls: Classes):
    for method in cls.methods:
        method.change_state = check_update_assignment_expression(method.method_node)

    for method in cls.methods:
        if not method.change_state:
            invocation_chain = get_method_invocation_chain(method, cls)
            method.change_state =  check_invoked_method_side_effecting(invocation_chain, cls)

""""GPT to check"""
def get_invocation_info(inv_node: Node, method, cls, file_data: bytes):
    """
    Returns all information about a method invocation:
        - qualified_name: "obj.get" or "a.b.c.compute"
        - method_name: "get"
        - object_chain: ["obj"] or ["a","b","c"]
        - object_type: Java type of the final receiver (from locals, params, fields)
    """

    def text(n: Node) -> str:
        return file_data[n.start_byte:n.end_byte].decode("utf8")

    # -------------------------------------------------------------------------
    # Extract raw method name
    # -------------------------------------------------------------------------
    name_node = inv_node.child_by_field_name("name")
    method_name = text(name_node)

    # -------------------------------------------------------------------------
    # Extract the object expression (identifier, field_access, etc.)
    # -------------------------------------------------------------------------
    obj_node = inv_node.child_by_field_name("object")
    if obj_node is None:
        # static call like ClassName.method()
        return {
            "qualified_name": method_name,
            "method_name": method_name,
            "object_chain": [],
            "object_type": None,
        }

    # -------------------------------------------------------------------------
    # Build full object chain: a.b.c
    # -------------------------------------------------------------------------
    def build_chain(node: Node):
        """
        Returns ["a","b","c"] for a.b.c
        """
        if node.type == "identifier":
            return [text(node)]

        if node.type == "field_access":
            left = build_chain(node.child_by_field_name("object"))
            right = text(node.child_by_field_name("field"))
            return left + [right]

        if node.type in ("this", "super"):
            return [text(node)]

        # Fallback: treat as single segment
        return [text(node)]

    object_chain = build_chain(obj_node)
    qualified_name = ".".join(object_chain + [method_name])

    # -------------------------------------------------------------------------
    # Resolve type of the final object in chain
    # -------------------------------------------------------------------------
    def resolve_type(chain: list[str], method, cls):
        """
        Resolve a.b.c -- get type of the last element (c).
        """
        if not chain:
            return None

        current = chain[0]

        # 1. method parameter?
        for p in method.parameters:
            if p.name == current:
                current_type = p.type
                break
        else:
            # 2. local variable?
            if hasattr(method, "local_vars") and current in method.local_vars:
                current_type = method.local_vars[current]
            # 3. field?
            elif hasattr(cls, "fields") and current in cls.fields:
                current_type = cls.fields[current]
            else:
                return None  # cannot resolve first element

        # For each next element, navigate the class fields
        for segment in chain[1:]:
            other_cls = cls.map.return_class(current_type)
            if other_cls and hasattr(other_cls, "fields"):
                current_type = other_cls.fields.get(segment)
            else:
                return None

        return current_type

    object_type = resolve_type(object_chain, method, cls)

    # -------------------------------------------------------------------------
    # Output structure
    # -------------------------------------------------------------------------
    return {
        "qualified_name": qualified_name,
        "method_name": method_name,
        "object_chain": object_chain,
        "object_type": object_type,
    }

""""Name to change?"""
def get_obj_type(obj: str, params: List[Parameter], local: List[Parameter]):

    for o in params:
        if o.name == obj:
            return o.type

    for o in local:
        if o.name == obj:
            return o.type

    return None

"""Very messy, to refactor"""
def classify_assertion(assertion: Assertion, assertion_mapping: Map, cls: Classes, method: Method) -> Classification:

    tree, file_data = parse_tree(cls.class_file_path)

    #check for side effect
    if check_update_assignment_expression(assertion.assertion_node):
        return "side_effect"
    else:
        for child in find_child(assertion.assertion_node, ["method_invocation"]):
            call_info = get_invocation_info(child, method, cls,file_data)
            method_check: Method = cls.return_method(call_info["method_name"])
            if method_check is None:
                obj = call_info["object_chain"][0]
                obj_type = get_obj_type(obj, method.parameters,  method.local_variables)
                obj_class = assertion_mapping.return_class(obj_type)
                if obj == "balance":
                    pass
                if obj_class is None:
                    continue
                method_check = obj_class.return_method(call_info["method_name"])

                if method_check is None:
                    continue
                if method_check.change_state:
                    return "side_effect"

                continue
            if method_check.change_state:
                return "side_effect"

        # check for tautology and contradiction if not already listed as side effect
        not_useless_types = [
            "identifier",
            "field_access",
            "array_access",
            "method_invocation"
        ]
        if len(find_child(assertion.assertion_node, not_useless_types)) == 0:
            return "useless"

    return "unclassified"

def average_assertions_per_method(cls: Classes):
    total_assertions = 0
    for method in cls.methods:
        total_assertions += len(method.assertions)
    if len(cls.methods) > 0:
        cls.average_assertion_per_method = total_assertions / len(cls.methods)
    else:
        cls.average_assertion_per_method = 0.0

def start_syntactic_analysis(assertion_mapping: Map):
    
    #count average assertion per method
    for cls in assertion_mapping.classes:
        average_assertions_per_method(cls)

    # Start assertion classification
    for cls in assertion_mapping.classes:
        for method in cls.methods:
            for assertion in method.assertions:
                assertion.classification = classify_assertion(assertion, assertion_mapping, cls, method)

def from_class_get_method_nodes(cls: Classes):
    """
    from_class_get_method_nodes adds all methods from a class and adds them to the class object

    Parameters
    ----------
    cls : Classes
        the class for which method nodes are added
    """
    tree, file_data = parse_tree(cls.class_file_path)

    try:
        method_nodes_list = QueryCursor(get_method_queries()).captures(tree.root_node)["method"]
    except Exception:
        method_nodes_list = []

    for method_node in method_nodes_list:
        method_name = method_node.child_by_field_name("name").text.decode("utf8")
        cls.add_method(get_method_data(method_name, method_node, file_data))

def parse_classes(assertion_map: Map):
    root = "src/main/java/jpamb/"
    java_files = list(Path(root).rglob("*.java"))

    for class_file in java_files:
        # changed to use the safer .stem for file names
        class_name:str = Path(class_file.name).stem
        assertion_map.add_class(class_name, class_file)
        from_class_get_method_nodes(assertion_map.return_class(class_name))
        pass

def setup():
    global JAVA_LANGUAGE
    JAVA_LANGUAGE = tree_sitter.Language(tree_sitter_java.language())
    global parser
    parser = tree_sitter.Parser(JAVA_LANGUAGE)

    global log
    log = logging
    log.basicConfig(level=logging.DEBUG)

def run() -> Map:
    """Run Syntaxer."""
    setup()

    # Initialize the assertion mapping
    assertion_mapping = Map()

    parse_classes(assertion_mapping)

    for cls in assertion_mapping.classes:
        update_methods_change_state_field(cls)

    # assertion_mapping.print_mapping()
    start_syntactic_analysis(assertion_mapping)
    # assertion_mapping.print_mapping()

    mapping_output = Map()
    mapping_output.append(assertion_mapping.return_class("BenchmarkSuite"))
    return mapping_output

def return_empty_map():
    assetion_mapping = Map()

    parse_classes(assetion_mapping)

    for cls in assetion_mapping.classes:
        update_methods_change_state_field(cls)

    return assetion_mapping

if __name__ == "__main__":
    setup()