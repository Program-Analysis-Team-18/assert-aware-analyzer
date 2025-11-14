from dataclasses import dataclass
from typing import List
from tree_sitter import Point, Node
import pickle

global MAP_PATH
MAP_PATH = "framework/aaa_map.pkl"

@dataclass
class Parameter:
    name: str
    type: str
    
    def __init__(self, name: str, type: str):
        self.name = name
        self.type = type

@dataclass
class AssertionNodeInfo:
    start_byte: int
    end_byte: int
    source_code: str
    
    def __init__(self, start_byte: int, end_byte: int, source_code: str):
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.source_code = source_code

@dataclass
class Assertion:
    absolute_start_line: Point
    absolute_end_line: Point
    assert_ast: AssertionNodeInfo
    classification: str 
    
    def __init__(self, absolute_start_line: Point, absolute_end_line: Point, assert_ast: AssertionNodeInfo, classification: str):
        self.absolute_start_line = absolute_start_line
        self.absolute_end_line = absolute_end_line
        self.assert_ast = assert_ast
        self.classification = classification

@dataclass
class AAAMethod:
    method_name: str
    parameters: List[Parameter]
    assertions: List[Assertion]
    
    def __init__(self, method_name: str, parameters: List[Parameter], assertions: List[Assertion]):
        self.method_name = method_name
        self.parameters = parameters
        self.assertions = assertions


@dataclass
class AAAClass:
    class_name: str
    methods: List[AAAMethod]
    
    def __init__(self, class_name: str, methods: List[AAAMethod]):
        self.class_name = class_name
        self.methods = methods

@dataclass
class AAAMap:
    classes: List[AAAClass]
    
    def __init__(self, classes: List[AAAClass]):
        self.classes = classes

    def save_to_file(self, filepath: str) -> None:
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load_from_file(filepath: str) -> "AAAMap":
        with open(filepath, 'rb') as f:
            return pickle.load(f)
        



'''
{
  "class_name": {
    "method_id": {
      "parameters" : [
        {
          "name" : "parameter_name",
          "type" : "parameter_type"
        },
        "..." // other parameters
      ],
      "assertions" : [
        {
          "absolute_start_line" : Point,
          "absolute_end_line" : Point,
          "assert_": "{custom_assertion_type}",
          "classification": "undefined | side_effects | tautological | incorrect | logically_implied | useless | useful"
        },
        "..." // other assertions
      ]
    },
    "..." // other methods
  },
  "..." // other classes
}
'''
