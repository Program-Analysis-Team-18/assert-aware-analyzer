import syntaxer
from pathlib import Path

assert_map = syntaxer.run()

def print_ground_truth_list(assert_map):
    """ print all the assertions to /framework/ground_truth.txt """
    gt = []
    for c in assert_map.classes:
        for m in c.methods:
            for a in m.assertions:
                gt.append ([c.class_name,m.method_name,a.absolute_start_point.row,a.classification])

    gt_sorted = sorted(gt, key=lambda x: x[2])

    for a in gt_sorted:
        print(f"{a[1]},{a[2]},{a[3]}")

def load_ground_truth():
    truth = {}
    for line in Path("framework/ground_truth.txt").read_text().splitlines():
        cls, method, line_no, label = line.strip().split(",")
        truth[(cls, method, int(line_no))] = label
    return truth

def calculate_performance(assert_map):
    """ calculates performance for the benchmark files
    assumes that the compared functions are in the same order in the map as in the file"""
    truth = load_ground_truth()

    allasserts= [a
                 for c in assert_map.classes
                 for m in c.methods
                 for a in m.assertions
                 ]
    assert len(truth) == len(allasserts)

    score = 0
    for c in assert_map.classes:
        for m in c.methods:
            for a in m.assertions:
                # print(f"c.class_name: {c.class_name} m.method_name: {m.method_name}")

                if (a.classification == truth[c.class_name, m.method_name, a.absolute_start_point.row]):
                    score += 1

    print(f"score is {score} / {len(truth)}")

# print_ground_truth_list(assert_map)

# calculate_performance(assert_map)