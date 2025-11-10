import random
import string
from copy import deepcopy
from typing import List
from solutions.interpreter import interpret


class Fuzzer:
    def __init__(self, method: str, corpus: List, coveraged_based: bool):
        self.method = method
        self.coverage_based = coveraged_based
        self.method_params = self.parse_parameters(method)
        self.corpus = {0: self.random_input() if corpus is None else corpus}
        self.error_map = {}


    def parse_parameters(self, method: str):
        params_start = method.index('(') + 1
        params_end = method.index(')')
        params = method[params_start:params_end]

        result = []
        i = 0
        while i < len(params):
            if params[i] == '[':
                i += 1
                base = params[i]
                i += 1
                result.append("[" + base)
            else:
                result.append(params[i])
                i += 1
        return result

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

    def random_input(self):
        randomized_input = []
        for t in self.method_params:
            if t[0] == '[':
                base_type = t[1]
                size = random.randint(0, 50) # max random array size set to 50
                arr = [self.random_value(base_type) for _ in range(size)]
                arr.insert(0, base_type)
                randomized_input.append(arr)
            else:
                randomized_input.append(self.random_value(t))
        return randomized_input

    def format_input(self, input):
        def format(x):
            if isinstance(x, str):
                return f"'{x}'"
            if isinstance(x, bool):
                return 'true' if x else 'false'
            if isinstance(x, list):
                base_type = x[0]
                x.remove(base_type)
                result =  f"[{base_type}:" + ",".join(format(v) for v in x) + "]"
                x.insert(0, base_type)
                return result
            return str(x)

        return "(" + ",".join(format(v) for v in input) + ")"

    def remove_base_types_from_input_arrays(self, input):
        for i, v in enumerate(input):
            if isinstance(v, list):
                input[i] = v[1:]
        return input

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
                c = x[:i] + c + x[i + 1:]
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
            for i, v in enumerate(input):
                input[i] = mutation(input[i])
            return input
        else:
            return mutation(input)


    def serialized_size_in_bytes(self, x):
        #fuzzer
        if isinstance(x, list):
            # Byte structure: "[" + items + "]"
            size = 2  # for "[" and "]"
            for i, elem in enumerate(x):
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

    def fuzz(self):
        if self.coverage_based:
            for _ in range(100000):
                input = self.mutate(deepcopy(random.choice(list(self.corpus.values()))))
                output = interpret(self.method, self.format_input(input), False)
                if output.depth not in self.corpus:
                    print(f"New input: {input} with depth: {output.depth}")
                    print(f"{input} -> {output.message}")
                    self.corpus[output.depth] = input
                    if output.message != "ok":
                        self.error_map[output.message] = input
                elif self.serialized_size_in_bytes(input) < self.serialized_size_in_bytes(self.corpus[output.depth]):
                    print(f"Smaller input: {input} for depth: {output.depth}")
                    print(f"{input} -> {output.message}")
                    self.corpus[output.depth] = input
            print(self.error_map)
        else:
            for _ in range(100000):
                input = self.random_input()
                output = interpret(method_id, self.format_input(input), False)
                if(output.message != "ok"):
                    print(f"{input} --> {output.message}:{output.depth}")


method_id = "jpamb.cases.Tricky.crashy:(III[C)V"
# method_id = "jpamb.cases.Arrays.arraySpellsHello:([C)V"
# method_id = "jpamb.cases.Tricky.charToInt:([I[C)V"
fuzzer = Fuzzer(method_id, None, True)
fuzzer.fuzz()
