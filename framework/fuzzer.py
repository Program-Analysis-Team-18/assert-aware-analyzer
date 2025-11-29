import random
import string
from copy import deepcopy
from typing import List
from interpreter import interpret
from core import WrongInput


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
    def __init__(self, method: str, corpus: List = None, symbolic_corpus=False, coveraged_based: bool = True, fuzz_for: int = 10_000):
        try:
            self.method = method
            self.coverage_based = coveraged_based
            self.method_params = self.parse_parameters(method)
            if symbolic_corpus:
                    self.corpus = {0: input for input in interpret(method, "".join(self.method_params), corpus=True)}
            else:
                self.corpus = {0: self.random_input() if corpus is None else corpus}

            # print(f"CORPUS: \n{self.corpus}")

            self.fuzz_for = fuzz_for
            self.wrong_inputs: List[List[WrongInput]] = []
            self.error_map = {}
        except ValueError as e:
            print(f"Fuzzer error: {e}")
            return ValueError(f"Fuzzer error: {e}")


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
                return random.randint(-1000, 1000)
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
                return round(random.uniform(-1000, 1000), 3)
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
                interesting_substitutions = [-1, 0, 1, 128, -128]
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
                    lambda v: v + random.randint(-100, 100),
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
    
    def _is_smaller(self, a, b):
        return self.serialized_size_in_bytes(a) < self.serialized_size_in_bytes(b)

    
    def _is_faulty(self, altered_output):
        if altered_output is None:
            return False
        return altered_output.message == "ok"

    
    def _search_argument_mutation(self, original_input, idx, depth, min_depth):
        for _ in range(self.fuzz_for):
            # print(f"---FUZZ FOR 2: {self.fuzz_for}---------")
            candidate = deepcopy(original_input)
            mutant_source = deepcopy(random.choice(list(self.corpus.values())))
            mutated = self.mutate(mutant_source)[idx]

            if mutated == original_input[idx]:
                continue

            candidate[idx] = mutated
            out = self._run(candidate, assertions_disabled=False)

            if out.depth >= min_depth and out.message not in("assertion error", "timeout"):
                return out
        return None


    def _find_faulty_arguments(self, input, depth, min_depth) -> List[WrongInput]:
        result = []
        for i in range(len(input)):
            mutated_val = self._search_argument_mutation(input, i, depth, min_depth)
            faulty = self._is_faulty(mutated_val)
            is_obj = isinstance(input[i], list)
            result.append(WrongInput(
                value=input[i][1] if is_obj else input[i],
                faulty=faulty,
                is_obj=is_obj
            ))
        return result

    
    def _crash_is_unprotected(self, input, depth):
        check = self._run(input, assertions_disabled=False)
        return check.depth == depth

    
    def _handle_new_coverage(self, input, output, depth, min_depth):
        self.corpus[depth] = input

        if output.message in("ok", "assertion error", "timeout"):
            return

        if depth < min_depth:
            return

        # If enabling assertions gives same depth, crash is real, not blocked
        if not self._crash_is_unprotected(input, depth):
            return

        # Find faulty inputs
        # print("FIND FAULTY WITH THIS OUTPUT: ", output.message)
        wrong_inputs = self._find_faulty_arguments(input, depth, min_depth)
        
        self.wrong_inputs.append(wrong_inputs)


    def _run(self, input, assertions_disabled):
        return interpret(
            method=self.method,
            inputs=self.format_input(input),
            verbose=False,
            assertions_disabled=assertions_disabled,
        )

    
    def fuzz(self, min_depth=1, max_errors=1, assertion_disabled=False):
        """
        Coverage-based (concolic-style) fuzzing.
        Randomly mutates inputs from the corpus, tracks coverage depth, and
        identifies inputs that crash without being guarded by assertions.
        """
        for _ in range(self.fuzz_for):
            # print("FUZZ FOR: ", _)
            seed = deepcopy(random.choice(list(self.corpus.values())))
            candidate = self.mutate(seed)

            # print("CANDIDATE: ", candidate)
            output = self._run(candidate, assertions_disabled=assertion_disabled)
            if output.message in ("assertion error", "timeout"):
                continue
            depth = output.depth

            if depth not in self.corpus:
                self._handle_new_coverage(candidate, output, depth, min_depth)
                if len(self.wrong_inputs) >= max_errors:
                    break
            elif self._is_smaller(candidate, self.corpus[depth]):
                self.corpus[depth] = candidate

    def fuzz_print(self):
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
# method_id = "jpamb.cases.Tricky.PositiveIntegers:(Ljpamb/cases/PositiveInteger<init>I;Ljpamb/cases/PositiveInteger<init>I;)V"
# method_id = "jpamb.cases.BenchmarkSuite.incr:(I)I"
# method_id = "jpamb.cases.BenchmarkSuite.divideByN:(II)V"
# fuzzer = Fuzzer(method_id, fuzz_for=10000, symbolic_corpus=True)
# fuzzer.fuzz()
