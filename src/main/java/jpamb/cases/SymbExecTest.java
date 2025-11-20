package jpamb.cases;

import jpamb.utils.Case;

public class SymbExecTest {

    @Case("(9) -> ok")
    public static int incr(int a) { 
        int x = a;          // []                    |- x := a
        if (x > 10) {       // [a > 10]              |- x := a
            x += 1;           // [a > 10]              |- x := a + 1
            if (x < 10)       // [a > 10, a + 1 < 10]  |- UNSAT
                assert false;   // never executed
        }
        return x;           // returns [ a  > 10 |- a + 1 
                            //         , a <= 10 |- a      ]
    }
}