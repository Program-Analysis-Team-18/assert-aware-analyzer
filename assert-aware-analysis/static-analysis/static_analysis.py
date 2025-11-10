#!/usr/bin/env python3
import logging
import tree_sitter
import tree_sitter_java
from tree_sitter import Point, Node
import jpamb
import sys
from jpamb import model
from pathlib import Path

import inspect

#Import aaa_utils 
try:
    from aaa_utils import MAP_PATH, Parameter, Assertion, AAAMethod, AAAClass, AAAMap, AssertionNodeInfo
except Exception:
    repo_root = Path(__file__).resolve().parents[1]  # parent of static-analysis folder
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from aaa_utils import MAP_PATH, Parameter, Assertion, AAAMethod, AAAClass, AAAMap, AssertionNodeInfo

def print_tree(node, depth=0):
    print("  " * depth + f"{node.type}")
    for child in node.children:
        print_tree(child, depth + 1)



def get_method_data(methodid: jpamb.jvm.AbsMethodID):
    """TODO add documentation"""
    global log
    srcfile = suite.sourcefile(methodid.classname)
    method_class = methodid.classname
    method_name = methodid.extension.name
    print(f"srcfile: {srcfile}")
    print(f"method_name: {method_name}")
    
    with open(srcfile, "rb") as f:
        data = f.read()
        tree = parser.parse(data)
    # print(tree)
    class_q = tree_sitter.Query( JAVA_LANGUAGE,
        f"""
        (class_declaration 
            name: ((identifier) @class-name 
                (#eq? @class-name "{method_class.name}"))) @class
        """,
    )
    
    for node in tree_sitter.QueryCursor(class_q).captures(tree.root_node)["class"]:
        # return AssertionNodeInfo(node.start_byte, node.end_byte, methodid)   
        break
    else:
        log.error(f"could not find a class of name {method_class.name} in {srcfile}")

        sys.exit(-1)

    method_q = tree_sitter.Query( JAVA_LANGUAGE,
        f"""
        (method_declaration 
            name: ((identifier) @method-name
                (#eq? @method-name "{method_name}"))) @method
        """,
    )
    print("here")
    
    # parse the parameters of the function
    assert_q = tree_sitter.Query(JAVA_LANGUAGE, """(assert_statement) @assert""")
    parameters_q = tree_sitter.Query(JAVA_LANGUAGE, """(formal_parameters) @params""")
   
    
    for node in tree_sitter.QueryCursor(method_q).captures(tree.root_node)["method"]:
        for name, nodelist in tree_sitter.QueryCursor(parameters_q).captures(node).items():
            for formal_params in nodelist:
                for formal_param in formal_params.children:
                    if formal_param.type != "formal_parameter":
                        continue
                    print(f"formal_param.type: {formal_param.type}")
                    print(f"formal_param: {formal_param}")
                    for item in formal_param.children:
                        # if item.type == ""
                        print(f"  item.type: {item.type}")
                        print(f"  item: {item}")

    
    for node in tree_sitter.QueryCursor(method_q).captures(tree.root_node)["method"]:
        indent = 0
        start = node.start_point
        end = node.end_point
        print("  " * indent + f"{node.type} [{start[0]+1}:{start[1]}–{end[0]+1}:{end[1]}]")
        try:
            for assert_node in tree_sitter.QueryCursor(assert_q).captures(node)["assert"]:
                start = assert_node.start_point
                end = assert_node.end_point
                print(assert_node)
                print(inspect.getmodule(start))
                #print("  " * indent + f"{assert_node.type} [{start[0]+1}:{start[1]}–{end[0]+1}:{end[1]}]")
        except KeyError:
            pass


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

    path_file: Path = Path(".").resolve()
    
    suite = model.Suite(Path(path_file))
    # get_method_data(Simple)
    
    
    # We go through all methods in the suite
    for methodid, correct in suite.case_methods():        
        # the first one jpamb.cases.Arrays.arrayContent:()V
        if (str(methodid)  == "jpamb.cases.Simple.divideZeroByZero:(II)I"):
            print(f"methodid REACHED: {methodid}")
            #add all these json to their class
            method = get_method_data(methodid)
            break
        
        
                
        

'''

for node in tree_sitter.QueryCursor(method_q).captures(node)["method"]:

    if not (p := node.child_by_field_name("parameters")):
        log.debug(f"Could not find parameteres of {method_name}")
        continue

    params = [c for c in p.children if c.type == "formal_parameter"]

    if len(params) != len(methodid.extension.params):
        continue

    # log.debug(methodid.extension.params)
    # log.debug(params)

    for tn, t in zip(methodid.extension.params, params):
        if (tp := t.child_by_field_name("type")) is None:
            break

        if tp.text is None:
            break

        # todo check for type.
    else:
        break
else:
    log.warning(f"could not find a method of name {method_name} in {simple_classname}")
    sys.exit(-1)

# log.debug("Found method %s %s", method_name, node.range)

body = node.child_by_field_name("body")
assert body and body.text
for t in body.text.splitlines():
    log.debug("line: %s", t.decode())

assert_q = tree_sitter.Query(JAVA_LANGUAGE, """(assert_statement) @assert""")
cursor = tree_sitter.QueryCursor(assert_q)  # query goes here

tree_dict: dict[str, list[Node]] = cursor.captures(body) # this typing is accurate

# for node, name in cursor.captures(body):
print(type(cursor.captures(body)))
print([type(key) for key in cursor.captures(body).keys()])
print([type(v) for v in cursor.captures(body).values()])
print([type(v[0]) for v in cursor.captures(body).values()])

# main    : <class 'dict'>
# main    : [<class 'tuple'>]
# main    : [<class 'list'>]

    # print(body.text[node.start_byte:node.end_byte].decode())





assert_found = any(
    capture_name == "assert"
    for capture_name, _ in tree_sitter.QueryCursor(assert_q).captures(body).items()
)
if assert_found:
    log.debug("Found assertion")
    print("assertion error;80%")
else:
    log.debug("No assertion")
    print("assertion error;20%")

sys.exit(0)
'''