package jpamb.cases;
import jpamb.utils.Case;

import jpamb.utils.*;
import static jpamb.utils.Tag.TagType.*;


public class Assertions {
    static int i;

    // Testing the assert chain. 
    // Since c() has a side effect, both a() and b() should also be classified as side-effecting.
    public void a() { 
        b(); 
    }

    public void b() { 
        c(); 
    }

    public void c() { 
        x = 5; 
    }

    // Testing the assert-with-call chain.
    // b1() is used inside an assert, but it still calls c1(), which has a side effect.
    public void a1() { 
        assert b1() == 7; 
    }

    public boolean b1() { 
        c1(); 
        return true;
    }

    public void c1() { 
        x = 5; 
    }

    @Case("() -> useless")
    @Tag({ ASSERTION })
    public static void assertLiteralTrue() {
        assert true;
    }

    @Case("() -> useless")
    @Tag({ ASSERTION })
    public static void assertTautology() {
        assert 1 + 1 == 2;
    }

    @Case("() -> no-side-effect")
    @Tag({ ASSERTION })
    public static void assertPureExpression() {
        int x = 10;
        assert x + 5 > 0;   // pure arithmetic
    }

    @Case("() -> side-effect")
    @Tag({ ASSERTION })
    public static void assertWithIncrement() {
        assert i++ == 7;    // modifies static field
    }
    
    @Case("() -> side-effect")
    @Tag({ ASSERTION })
    public static int assertAndReturnWithIncrement() {
        assert i++ == 7;    // modifies static field
        return i;
    }

    @Case("() -> side-effect")
    @Tag({ ASSERTION })
    public static void assertArrayWrite() {
        int[] arr = {1};
        assert (arr[0] = 9) == 9; // assignment expression
    }
    
    // @Case("() -> side-effect")
    // @Tag({ ASSERTION })
    // public static void callToSideEffect() {
    //     assert assertWithIncrement() == 42; // method call with side effects
    // }
    
    // @Case("() -> side-effect")
    // @Tag({ ASSERTION })
    // public static void callToSideEffectRecursive() {
    //     assert callToSideEffect() == 42; // method call with side effects
    // }

}
