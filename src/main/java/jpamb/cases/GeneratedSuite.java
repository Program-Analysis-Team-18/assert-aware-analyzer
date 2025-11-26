package jpamb.cases;

import jpamb.utils.Tag;
import static jpamb.utils.Tag.TagType.*;

public class GeneratedSuite {

    @Tag({ USEFUL_ASSERT })
    public static void safeArrayAccess(PositiveInteger index, int limit) {
        assert index.get() < limit;
        int[] arr = new int[limit];
        arr[index.get()] = 1;
    }

    @Tag({ USEFUL_ASSERT })
    public static void safeDivision(PositiveInteger numerator, PositiveInteger denominator) {
        assert denominator.get() != 0;
        int result = numerator.get() / denominator.get();
    }

    @Tag({ TAUTOLOGY_ASSERT })
    public static void knownPositive(PositiveInteger p) {
        assert p.get() >= 0;
    }

    @Tag({ CONTRADICTION_ASSERT })
    public static void impossibleNegative(PositiveInteger p) {
        assert p.get() < 0;
    }

    @Tag({ USELESS_ASSERT })
    public static void uselessCheck(PositiveInteger p) {
        assert p.get() != 100;
        int x = p.get() + 1; 
    }

    @Tag({ USEFUL_ASSERT })
    public static void complexLogic(PositiveInteger a, CappedInteger b) {
        assert a.get() < b.get();
        int[] arr = new int[b.get()];
        arr[a.get()] = 1;
    }
    
    @Tag({ USEFUL_ASSERT })
    public static void stepLogic(StepInteger s, int divisor) {
        assert s.get() != 0;
        int res = 100 / s.get();
    }

    @Tag({ SIDE_EFFECT_ASSERT })
    public static void sideEffect(int[] arr) {
        assert (arr[0] = 1) == 1;
    }
    @Tag({ USEFUL_ASSERT })
    public static void nestedArrayAccess(PositiveInteger index, PositiveInteger size) {
        assert index.get() < size.get();
        int[][] matrix = new int[size.get()][size.get()];
        matrix[index.get()][0] = 1;
    }

    @Tag({ USEFUL_ASSERT, TAUTOLOGY_ASSERT })
    public static void redundantChecks(PositiveInteger p) {
        assert p.get() >= 0; // Tautology
        assert p.get() != 1000; // Useful if p can be 1000
        if (p.get() == 1000) throw new RuntimeException();
    }

    @Tag({ CONTRADICTION_ASSERT })
    public static void impossibleRange(CappedInteger c) {
        // CappedInteger(val, cap) -> val <= cap
        // If we assert val > cap + 1, it's a contradiction
        assert c.get() > c.getCap() + 1;
    }

    @Tag({ USEFUL_ASSERT })
    public static void moduloCheck(StepInteger s) {
        // StepInteger ensures value % step == 0
        // If we divide by value, we need value != 0
        assert s.get() != 0;
        int x = 100 / s.get();
    }

    @Tag({ USELESS_ASSERT })
    public static void uselessModulo(StepInteger s) {
        // If step is 2, value is even.
        // Asserting value % 2 == 0 is tautology/useless? 
        // Actually StepInteger guarantees it, so it's a tautology relative to the type.
        // But let's say we assert something unrelated
        assert s.get() != 999999; 
        // No crash
    }

    @Tag({ USEFUL_ASSERT })
    public static void arrayBoundsWithCap(CappedInteger index, int[] arr) {
        // index.get() <= cap. 
        // If cap >= arr.length, we need the assertion.
        assert index.get() < arr.length;
        int x = arr[index.get()];
    }

    @Tag({ SIDE_EFFECT_ASSERT })
    public static void sideEffectInCondition(PositiveInteger p) {
        int[] arr = {1, 2};
        assert (arr[0]++) > 0;
    }

    @Tag({ USEFUL_ASSERT })
    public static void complexMath(PositiveInteger a, PositiveInteger b) {
        // a, b >= 0
        // prevent overflow or something?
        // simple div by zero
        assert a.get() + b.get() != 0;
        int x = 100 / (a.get() + b.get());
    }

    @Tag({ TAUTOLOGY_ASSERT })
    public static void tautologyMath(PositiveInteger a) {
        assert a.get() * a.get() >= 0;
    }

    @Tag({ CONTRADICTION_ASSERT })
    public static void contradictionMath(PositiveInteger a) {
        assert a.get() + 1 < 0;
    }
    
    @Tag({ USEFUL_ASSERT })
    public static void mixedTypes(PositiveInteger p, CappedInteger c) {
        // p >= 0, c <= cap
        // ensure p < c
        assert p.get() < c.get();
        int[] arr = new int[c.get()];
        arr[p.get()] = 123;
    }

    @Tag({ USEFUL_ASSERT })
    public static void loopBound(PositiveInteger limit) {
        assert limit.get() < 100;
        int[] arr = new int[100];
        for(int i=0; i<=limit.get(); i++) {
            arr[i] = i;
        }
    }

    @Tag({ USEFUL_ASSERT })
    public static void recursiveCheck(PositiveInteger n) {
        assert n.get() < 10;
        if (n.get() > 0) {
            // If n >= 10, this assertion fails.
            // If we remove it, we might recurse too deep or something?
            // Actually here if n >= 10, we just recurse.
            // But let's say we have an array of size 10.
            int[] arr = new int[10];
            arr[n.get()] = 1; 
            // If n=10, arr[10] throws.
            // recursive call
            // We need to create a new PositiveInteger to recurse, but we can't easily.
            // So we just simulate logic.
        }
    }

    @Tag({ USEFUL_ASSERT })
    public static void switchCase(PositiveInteger p) {
        assert p.get() < 3;
        switch(p.get()) {
            case 0: break;
            case 1: break;
            case 2: break;
            default: 
                throw new RuntimeException("Unexpected value");
        }
    }
    @Tag({ USEFUL_ASSERT })
    public static void complexBoolean(PositiveInteger a, PositiveInteger b) {
        // !(a < b) && !(a > b) => a == b
        // assert a == b
        assert !(a.get() < b.get()) && !(a.get() > b.get());
        int x = 100 / (a.get() - b.get() + 1); // if a==b, div by 1.
        // If assertion removed, a != b is possible.
        // If a - b + 1 == 0 => a - b == -1 => b = a + 1.
        // If b = a + 1, then a < b is true.
        // So !(a < b) is false.
        // So the assertion fails if a < b.
        // If we remove assertion, we can have b = a + 1.
        // Then 100 / (a - (a+1) + 1) = 100 / 0 -> ArithmeticException.
    }
}
