import random
import string
from copy import deepcopy
from typing import List
from solutions.interpreter import interpret


class CustomType:
    def __init__(self, name, params):
        self.name = name
        self.init_params = params


"""
    A fuzzer that generates random or coverage-guided inputs for the JPAMB methods.

    Usage: f = Fuzzer("jpamb.cases.Arrays.arraySpellsHello:([C)V", None, True)
           f.fuzz()
"""
class Fuzzer:
    def __init__(self, method: str, corpus: List = None, symbolic_corpus=False, coveraged_based: bool = True, fuzz_for: int = 100000):
        self.method = method
        self.coverage_based = coveraged_based
        self.method_params = self.parse_parameters(method)
        if symbolic_corpus:
            self.corpus = {0: input for input in interpret(method, "".join(self.method_params), corpus=True)}
        else:
            self.corpus = {0: self.random_input() if corpus is None else corpus}
        self.fuzz_for = fuzz_for
        self.error_map = {}


    # Parses JVM descriptors between ( and ) into a list like ["I", "[C"].
    def parse_parameters(self, method: str):
        params_start = method.index('(') + 1
        params_end = method.index(')')
        params = method[params_start:params_end]

        result = []
        while len(params) > 0:
            if params[0] == 'L':
                name = params[1:params.find('<init>')]
                ctor_params = params[params.find('<init>') + 6: params.find(';')]
                j = 0
                init_params = []
                while j < len(ctor_params):
                    if ctor_params[j] == '[':
                        init_params.append("[" + ctor_params[j + 1])
                        j += 2
                    else:
                        init_params.append(ctor_params[j])
                        j += 1
                result.append(CustomType(name, init_params))
                i = params.find(';')
                params = params[i+1:]
            elif params[0] == '[':
                result.append("[" + params[1])
                params = params[2:]
            else:
                result.append(params[0])
                params = params[1:]
        return result

    # Returns a random Python value for a primitive JVM type.
    # Example: random_value("I") → 57
    def random_value(self, t: str):
        match t:
            case "I":
                return random.randint(-10000, 10000)
            case "S":
                return random.randint(-1000, 1000)
            case "J":
                return random.randint(-10 ** 5, 10 ** 5)
            case "B":
                return random.randint(-128, 127)
            case "Z":
                return random.choice([True, False])
            case "C":
                return random.choice(string.ascii_letters)
            case "F":
                return round(random.uniform(-1000, 1000), 3)
            case "D":
                return round(random.uniform(-10000, 10000), 3)
        return None

    # Creates a random argument list for the method, including random arrays.
    # Example: ["I","[C"] → [42, ['C','H','i']]
    def random_array(self, t):
        size = random.randint(0, 50)  # max random array size set to 50
        arr = [self.random_value(t) for _ in range(size)]
        arr.insert(0, t)
        return arr

    # Formats an internal argument list into the string format interpret(...) expects.
    # ExampleL: [['C','H','i']] → "([C:'H','i'])"
    def random_input(self):
        randomized_input = []
        for t in self.method_params:
            if isinstance(t, CustomType):
                input_values = []
                for v in t.init_params:
                    if v.startswith('['):
                        input_values.append(self.random_array(v[1]))
                    else:
                        input_values.append(self.random_value(v))
                input_values.insert(0, t.name)
                randomized_input.append(input_values)
            elif t.startswith('['):
                randomized_input.append(self.random_array(t[1]))
            else:
                randomized_input.append(self.random_value(t))
        return randomized_input

    # Formats an internal argument list into the string format interpret(...) expects.
    # ExampleL: [['C','H','i']] → "([C:'H','i'])"
    def format_input(self, input):
        def format(x):
            if isinstance(x, str):
                return f"'{x}'"
            if isinstance(x, bool):
                return 'true' if x else 'false'
            if isinstance(x, list):
                base_type = x[0]
                x.remove(base_type)
                if len(base_type) > 1:
                    result = f"new {base_type}(" + ",".join(format(v) for v in x) + ")"
                else:
                    result =  f"[{base_type}:" + ",".join(format(v) for v in x) + "]"
                x.insert(0, base_type)
                return result
            return str(x)

        return "(" + ",".join(format(v) for v in input) + ")"

    # Mutates input arguments using either deterministic or havoc mutations.
    # Example: [10] → [19]   # maybe adds +9
    # ['C','H','i'] → ['C','i','H']  # maybe reversed
    def mutate(self, input):
        def deterministic(x):
            if isinstance(x, list):
                base_type = x[0]
                x.remove(base_type)
                for i, v in enumerate(x):
                    x[i] = deterministic(v)
                x.insert(0, base_type)
                return x
            if isinstance(x, bool):
                x &= random.choice([True, False])
                return x
            elif isinstance(x, str) and x:
                safe_chars = string.ascii_letters + string.digits  # only letters and digits
                i = random.randrange(len(x))
                c = chr(ord(x[i]) ^ (1 << random.randint(0, 6)))
                c = x[:i] + c + x[i+1:]
                if c not in safe_chars:
                    c = random.choice(safe_chars)
                return c
            else:
                interesting_substitutions = [-1, 0, 1, 255, 256, 1024, -128, 32767, -32768]
                ops = [
                    lambda v: v ^ (1 << random.randint(0, 7)) if isinstance(v, int) else v * v,
                    lambda v: v + random.randint(-10, 10),
                    lambda v: random.choice(interesting_substitutions)
                ]
                return random.choice(ops)(x)

        def havoc(x):
            if isinstance(x, list):
                base_type = x[0]
                x.remove(base_type)
                ops = [
                    lambda v: v + [self.random_value(base_type)], # append
                    lambda v: v[:-1] if v else v,  # delete last
                    lambda v: v + v,  # duplicate whole list
                    lambda v: v[::-1]  # reverse
                ]
                x = random.choice(ops)(x)
                x.insert(0, base_type)
                return x
            if isinstance(x, str):
                ops = [
                    lambda v: v + chr(random.randint(32, 126)),
                    lambda v: v[:-1] if v else v,
                    lambda v: v * 2,
                    lambda v: ''.join(reversed(v))
                ]
                return random.choice(ops)(x)
            elif isinstance(x, bool):
                return x ^ (1 << random.randint(0, 7))
            else:
                ops = [
                    lambda v: v + random.randint(-1000, 1000),
                    lambda v: v * 2,
                    lambda v: v // 2 if v else v
                ]
                return random.choice(ops)(x)

        mutation = random.choice([havoc, deterministic])

        if(isinstance(input, list)):
            for i, _ in enumerate(input):
                if isinstance(input[i], list) and len(input[i][0]) > 1:
                    custom_type = input[i][0]
                    input[i].remove(custom_type)
                    for j, _ in enumerate(input[i]):
                        input[i][j] = mutation(input[i][j])
                    input[i].insert(0, custom_type)
                else:
                    input[i] = mutation(input[i])
            return input
        else:
            return mutation(input)

    # Estimates how many bytes the value would take when serialized.
    # Example: 123 → 3
    # Example: ['C','A'] → approx 5–7
    def serialized_size_in_bytes(self, x):
        if isinstance(x, list):
            # Byte structure: "[" + items + "]"
            size = 2  # for "[" and "]"
            for i, elem in enumerate(x):
                if isinstance(elem, list) and len(elem[0]) > 1:
                    size += 2
                    j = 1
                    while j < len(elem):
                        size += self.serialized_size_in_bytes(elem[j])
                        j += 1
                else:
                    size += self.serialized_size_in_bytes(elem)
                if i > 0:
                    size += 1  # comma
            return size
        if isinstance(x, int):
            return len(str(x).encode("utf8"))
        if isinstance(x, float):
            return 8
        if isinstance(x, bool):
            return 1
        if isinstance(x, str):
            return len(x.encode("utf8"))

        return 0

    # Runs the fuzzing loop:
    # if coverage_based -> mutate corpus → track new coverage depth
    # else random -> generate new random inputs
    def fuzz(self):
        if self.coverage_based:
            for _ in range(self.fuzz_for):
                input = self.mutate(deepcopy(random.choice(list(self.corpus.values()))))
                output = interpret(self.method, self.format_input(input), False)
                if output.depth not in self.corpus:
                    print(f"New input: {input} with depth: {output.depth}")
                    print(f"{input} -> {output.message}")
                    self.corpus[output.depth] = input
                    if output.message != "ok":
                        self.error_map[output.message] = input
                elif self.serialized_size_in_bytes(input) < self.serialized_size_in_bytes(self.corpus[output.depth]):
                    print(f"Smaller input: {input} for depth {output.depth} --> {output.message}")
                    self.corpus[output.depth] = input
        else:
            for _ in range(self.fuzz_for):
                input = self.random_input()
                output = interpret(method_id, self.format_input(input), False)
                if(output.message != "ok"):
                    self.error_map[output.depth] = input
                    print(f"{input} --> {output.message}:{output.depth}")
        print(self.error_map)


# method_id = "jpamb.cases.Tricky.crashy:(III[C)V"
# method_id = "jpamb.cases.SymbExecTest.misc:(III)I"
# method_id = "jpamb.cases.CustomClasses.Withdraw:(Ljpamb/cases/PositiveInteger<init>I;)V"
# method_id = "jpamb.cases.Arrays.arraySpellsHello:([C)V"
# method_id = "jpamb.cases.Tricky.charToInt:([I[C)V"
method_id = "jpamb.cases.Tricky.PositiveIntegers:(Ljpamb/cases/PositiveInteger<init>I;Ljpamb/cases/PositiveInteger<init>I;)V"
fuzzer = Fuzzer(method_id, fuzz_for=10000)
fuzzer.fuzz()