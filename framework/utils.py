from dataclasses import dataclass
from typing import List
from tree_sitter import Point, Node, Tree
from jpamb.jvm import Absolute, MethodID

@dataclass
class SimpleMethodID:
    name: str
    class_name: str



@dataclass
class Parameter:
    name: str
    type: str
    
    def __init__(self, name: str, type: str):
        self.name = name
        self.type = type
    def __str__(self):
        return f"parameter: {self.name}, type: {self.type}"

@dataclass
class Assertion:
    absolute_start_line: Point
    absolute_end_line: Point
    assertion_node: Node
    classification: str 
    
    def __init__(self, absolute_start_line: Point, absolute_end_line: Point, assertion_node: Node, classification: str):
        self.absolute_start_line = absolute_start_line
        self.absolute_end_line = absolute_end_line
        self.assertion_node = assertion_node
        self.classification = classification
        

@dataclass
class Method:
    method_id: Absolute[MethodID]
    parameters: List[Parameter]
    assertions: List[Assertion]
    change_state: bool
    
    def __init__(self, method_id: Absolute[MethodID], parameters: List[Parameter], assertions: List[Assertion]):
        self.method_id = method_id
        self.parameters = parameters
        self.assertions = assertions
        self.change_state = False


@dataclass
class Classes:
    class_name: str
    average_assertion_per_method: float
    methods: List[Method]
    
    def __init__(self, class_name: str):
        self.class_name = class_name
        self.methods = []
        self.average_assertion_per_method = None

    def add_method(self, method: Method):
        self.methods.append(method)
        
    def return_method(self, method_name: str) -> Method:
        for method in self.methods:
            if method.method_id.extension.name == method_name:
                return method
        return None
    
    def method_present(self, method_name: str) -> bool:
        for method in self.methods:
            if method.method_id.extension.name == method_name:
                return True
        return False

@dataclass
class Map:
    classes: List[Classes]
    
    def __init__(self):
        self.classes = []

    def add_class(self, class_name: str):
        self.classes.append(Classes(class_name))
    
    def return_class(self, class_name: str) -> Classes:
        for cls in self.classes:
            if cls.class_name == class_name:
                return cls
        return None
    
    def add_method_to_class(self, class_name: str, method: Method):
        cls = self.return_class(class_name)
        if cls:
            cls.add_method(method)
        else:
            self.add_class(class_name)
            cls = self.return_class(class_name)
            if not (cls.return_method(class_name)):
                cls.add_method(method)

    def print_mapping(self):
        for cls in self.classes:
            print(f"\n=== Class: {cls.class_name} ===")
            print(f"Average assertions per method: {cls.average_assertion_per_method}")
            if not cls.methods:
                print("  (No methods)")
            for method in cls.methods:
                print(f"\n  Method: {method.method_id.extension.name}")
                print(f"    Change-state: {method.change_state}")

                # Parameters
                if method.parameters:
                    print("    Parameters:")
                    for param in method.parameters:
                        print(f"      - {param.name}: {param.type}")
                else:
                    print("    Parameters: None")

                # Assertions
                if method.assertions:
                    print("    Assertions:")
                    for assertion in method.assertions:
                        start_line = assertion.absolute_start_line
                        print(f"      - {assertion.classification} (line {start_line})")
                else:
                    print("    Assertions: None")

    def class_present(self, class_name: str) -> bool:
        for cls in self.classes:
            if cls.class_name == class_name:
                return True
        return False
