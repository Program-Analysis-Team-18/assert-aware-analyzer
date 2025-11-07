from dataclasses import dataclass
from typing import Dict, List
import tree_sitter import Point, Tree


@dataclass
class Parameter:
    name: str
    type: str


@dataclass
class Assertion:
    absolute_start_line: Point
    absolute_end_line: Point
    assert_ast: Tree
    classification: str 


@dataclass
class AAAMethod:
    parameters: List[Parameter]  # because your example shows parameters may include "..." placeholders
    assertions: List[Assertion]


@dataclass
class AAAClass:
    methods: Dict[str, AAAMethod]


@dataclass
class AAAStructure:
    classes: Dict[str, AAAClass]
