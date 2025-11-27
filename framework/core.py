from dataclasses import dataclass, field
from typing import List, Literal, Any
from tree_sitter import Point, Node
from pathlib import Path

Classification = Literal[
    "tautology",
    "contingent",
    "contradiction",
    "side_effect",
    "useful",
    "useless",
    "unclassified",
]


@dataclass
class WrongInput:
    value: Any
    faulty: bool
    is_obj: bool


@dataclass
class WrongParameter:
    name: str
    type: str
    value: Any
    faulty: bool

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
    absolute_start_point: Point
    absolute_end_point: Point
    assertion_node: Node
    classification: Classification 
    
    def __init__(self, absolute_start_line: Point, absolute_end_line: Point, assertion_node: Node, classification: str):
        self.absolute_start_point = absolute_start_line
        self.absolute_end_point = absolute_end_line
        self.assertion_node = assertion_node
        self.classification = classification
        

@dataclass
class Method:
    method_name: str
    method_id: str
    method_node: Node
    parameters: List[Parameter]
    assertions: List[Assertion]
    local_variables: List[Parameter]
    change_state: bool
    wrong_inputs: List[WrongParameter]
    
    def __init__(self, method_name: str,  method_node: Node, parameters: List[Parameter], assertions: List[Assertion], local_variables: List[Parameter]):
        self.method_name = method_name
        self.method_node = method_node
        self.parameters = parameters
        self.assertions = assertions
        self.local_variables = local_variables
        self.change_state = False
        self.wrong_inputs = []

    def set_method_id(self, method_id: str):
        self.method_id = method_id
        
    def add_wrong_inputs(self, inputs: List[WrongInput]):
        result: WrongParameter
        for i in range(len(inputs)):
            param_name = self.parameters[i].name
            param_type = self.parameters[i].type
            input = inputs[i]

            if input.is_obj:
                param_name = f'{param_name}.get()'

            result = WrongParameter(
                name=param_name,
                type=param_type,
                value=input.value,
                faulty=input.faulty,
            )
            self.wrong_inputs.append(result)
    
    def get_suggested_assertions(self) -> List[str]:
        result = []
        
        if len(self.wrong_inputs) == 0: return result

        no_faulty = all(not wi.faulty for wi in self.wrong_inputs)
        conditions = [f"{wi.name} != {wi.value}" for wi in self.wrong_inputs if wi.faulty or no_faulty]
        suggested = f"assert {" || ".join(conditions)};"
        result.append(suggested)
        return result


@dataclass
class Classes:
    class_name: str
    average_assertion_per_method: float
    methods: List[Method]
    class_file_path: Path

    
    def __init__(self, class_name: str, class_file_path: Path):
        self.class_name = class_name
        self.class_file_path = class_file_path
        self.methods = []
        self.average_assertion_per_method = None

    def add_method(self, method: Method):
        self.methods.append(method)
        
    def return_method(self, method_name: str) -> Method:
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

    def add_class(self, class_name: str, class_file_path: Path):
        self.classes.append(Classes(class_name, class_file_path))
    
    def return_class(self, class_name: str) -> Classes:
        for cls in self.classes:
            if cls.class_name == class_name:
                return cls
        return None
    
    # Petteri: I think this is not required anymore. Can be deleted
    # def add_method_to_class(self, class_name: str, method: Method):
    #     cls = self.return_class(class_name)
    #     if cls:
    #         cls.add_method(method)
    #     else:
    #         self.add_class(class_name)
    #         cls = self.return_class(class_name)
    #         if not (cls.return_method(class_name)):
    #             cls.add_method(method)

    def print_mapping(self):
        if not self.classes:
            print("Mapping is empty")
        for cls in self.classes:
            print(f"\n=== Class: {cls.class_name} ===")
            print(f"Average assertions per method: {cls.average_assertion_per_method}")
            if not cls.methods:
                print("  (No methods)")
            for method in cls.methods:
                print(f"\n  Method: {method.method_name}")
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
                        start_line = assertion.absolute_start_point
                        print(f"      - {assertion.classification} (line {start_line})")
                else:
                    print("    Assertions: None")

    def class_present(self, class_name: str) -> bool:
        for cls in self.classes:
            if cls.class_name == class_name:
                return True
        return False
