from framework import syntaxer

assert_map = syntaxer.run()





def print_ground_truth_list(assert_map):
    """ print all the assertions to /framework/groud_truth.txt """
    for c in assert_map.classes:
        for m in c.methods:
            for a in m.assertions:
                print(f"{c.class_name},{m.method_name},{a.absolute_start_line},{a.classification}")
    
    
