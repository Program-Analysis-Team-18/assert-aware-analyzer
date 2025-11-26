"""Generation   Invoker module"""
import random
import string
from typing import Dict, Any
import z3
from interpreter import interpret, InterpretationResult


class CustomType:
    """Custom Type wrapper"""
    def __init__(self, name, init_params):
        self.name = name
        self.init_params = init_params


class GenerationInvoker:
    """
    Generates method invocation arguments using:
    - CustomType support
    - Z3 model values
    - Fuzzer fallback for missing params
    """

    def __init__(self, method_id: str):
        self.method_id = method_id
        self.param_types = self._parse_params(method_id)

    def _parse_params(self, method_id):
        """Parse primitives and CustomType with <init> signature params."""
        inside = method_id[method_id.index("(") + 1 : method_id.index(")")]
        out = []
        i = 0

        while i < len(inside):
            if inside[i] == "L":
                semi = inside.index(";", i)
                descriptor = inside[i+1:semi]
                cname = descriptor[:descriptor.index("<init>")]
                ctor_sig = descriptor[descriptor.index("<init>") + 6 :]

                init_params = list(ctor_sig)
                out.append(CustomType(cname, init_params))
                i = semi + 1
            else:
                out.append(inside[i])
                i += 1

        return out

    def _random_primitive(self, t):
        """Random primitive param (fuzzer fallback)."""
        match t:
            case "I": return random.randint(-10000, 10000)
            case "S": return random.randint(-1000, 1000)
            case "B": return random.randint(-128, 127)
            case "Z": return random.choice([True, False])
            case "C": return random.choice(string.ascii_letters)
            case "F": return round(random.uniform(-1000, 1000), 3)
            case "D": return round(random.uniform(-10000, 10000), 3)
        return None

    def _build_custom_type(self, ct: CustomType, params: list[Any]):
        """Build a Custom Type instance from the given parameters."""
        return [ct.name] + params

    def _generate_custom_type(self, ct: CustomType):
        """Generate a Custom Type instance using fuzzer logic."""
        return [ct.name] + [self._random_primitive(t) for t in ct.init_params]

    def _convert_z3_value(self, z3val: z3.ExprRef, expected_type):
        """Convert from Z3 value to python value"""
        if isinstance(expected_type, CustomType):
            vals = []
            for t in expected_type.init_params:
                vals.append(self._convert_z3_value(z3val, t))
            return [expected_type.name] + vals

        if str(expected_type) in {"I", "S", "B", "C"}:
            return int(z3val.as_long())
        if expected_type == "Z":
            return bool(z3val.as_long())
        if expected_type in {"F", "D"}:
            return float(z3val.as_decimal(10))

        return None

    def _fmt(self, v):
        """Format value to str for interpret()"""
        if isinstance(v, str):
            return f"'{v}'"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, list):
            classname = v[0]
            args = ",".join(self._fmt(x) for x in v[1:])
            return f"new {classname}({args})"
        return str(v)

    def build_arguments(self, param_order: list[str], model, z3_vars: Dict[str, Any]):
        """Build full argument list using model and fuzzer fallback."""
        final = []

        for index, pname in enumerate(param_order):
            # print(f"PARAM ORDER: {param_order}")
            # print(f"PARAM TYPES: {self.param_types}")
            spec = self.param_types[index]

            # If Z3 has a value for this primitive parameter -> use it
            if pname in z3_vars and model:
                z3val = model.get_interp(z3_vars[pname])
                if z3val is not None:
                    final.append(self._convert_z3_value(z3val, spec))
                    continue

            # If Z3 has a value for this custom type parameter -> use it
            if f"{pname}.get()" in z3_vars and model:
                z3val = model.get_interp(z3_vars[f"{pname}.get()"])
                if z3val is not None and isinstance(spec, CustomType):
                    custom_obj = self._convert_z3_value(z3val, spec)
                    final.append(custom_obj)
                    continue

            # Otherwise, generate default value
            if isinstance(spec, CustomType):
                final.append(self._generate_custom_type(spec))
            else:
                final.append(self._random_primitive(spec))

        return final

    def invoke(self, param_order, model, z3_vars, max_attempts=10) -> InterpretationResult:
        """Build arguments, formats, and invokes the interpreter."""
        # print("PARAM_ORDER:", param_order)
        # print("MODEL:", model)
        # print("z3_vars:", z3_vars)

        # try max_attempts times if the problem is with the generated params (useful for Custom Type args)
        for _ in range(max_attempts):
            args = self.build_arguments(param_order, model, z3_vars)
            formatted = "(" + ",".join(self._fmt(v) for v in args) + ")"

            result = interpret(
                method=self.method_id,
                inputs=formatted,
                verbose=False,
                assertions_disabled=True
            )

            # if result.depth == 0 it means that the method failed because of the arguments
            if result.message == 'ok' or result.depth > 0:
                break

        # print("METHOD:", self.method_id)
        # print("FORMATTED:", formatted)
        return result
