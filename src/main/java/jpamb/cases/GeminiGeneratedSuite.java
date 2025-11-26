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
    public static void loopBound(PositiveInteger limit) {
        assert limit.get() < 100;
        int[] arr = new int[100];
        for(int i=0; i<=limit.get(); i++) {
            arr[i] = i;
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

}
