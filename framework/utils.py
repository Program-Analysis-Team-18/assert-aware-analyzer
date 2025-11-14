from dataclasses import dataclass
from typing import List
from tree_sitter import Point, Node


@dataclass
class Parameter:
    name: str
    type: str
    
    def __init__(self, name: str, type: str):
        self.name = name
        self.type = type

@dataclass
class Assertion:
    absolute_start_line: Point
    absolute_end_line: Point
    assert_ast: Node
    classification: str 
    
    def __init__(self, absolute_start_line: Point, absolute_end_line: Point, assert_node: Node, classification: str):
        self.absolute_start_line = absolute_start_line
        self.absolute_end_line = absolute_end_line
        self.assert_node = assert_node
        self.classification = classification

@dataclass
class Methods:
    method_name: str
    parameters: List[Parameter]
    assertions: List[Assertion]
    
    def __init__(self, method_name: str, parameters: List[Parameter], assertions: List[Assertion]):
        self.method_name = method_name
        self.parameters = parameters
        self.assertions = assertions


@dataclass
class Classes:
    class_name: str
    methods: List[Methods]
    
    def __init__(self, class_name: str):
        self.class_name = class_name
        self.methods = []

    def add_method(self, method: Methods):
        self.methods.append(method)
        
    def return_method(self, method_name: str) -> Methods:
        for method in self.methods:
            if method.method_name == method_name:
                return method
        return None
    
    def method_present(self, method_name: str) -> bool:
        for method in self.methods:
            if method.method_name == method_name:
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
    
    def add_method_to_class(self, class_name: str, method: Methods):
        cls = self.return_class(class_name)
        if cls:
            cls.add_method(method)
    
    def class_present(self, class_name: str) -> bool:
        for cls in self.classes:
            if cls.class_name == class_name:
                return True
        return False
