package jpamb.cases;

import jpamb.utils.CappedInteger;
import jpamb.utils.PositiveInteger;
import jpamb.utils.StepInteger;
import jpamb.utils.Tag;

import static jpamb.utils.Tag.TagType.*;

public class BenchmarkSuite {
    // ===================
    // ===== SIMPLE ======
    // ===================

    static int state;

    public static boolean invokeChangeState() { 
        changeState(); 
        return true;
    }

    public static void changeState() {
        state = 5;
    }

    // Testing the assert-with-call chain.
    // invokeChangeState() is used inside an assert, but it still calls changeState(), which has a side effect.
    @Tag({ SIDE_EFFECT_ASSERT })
    public static void changeStateNested() {
        assert invokeChangeState(); 
    }

    @Tag({ USELESS_ASSERT })
    public static void assertLiteralTrue() {
        assert true;
    }

    @Tag({ SIDE_EFFECT_ASSERT })
    public static void assertWithIncrement() {
        assert state++ == 7;
    }

    @Tag({ SIDE_EFFECT_ASSERT })
    public static void assertArrayWrite(int[] arr) {
        assert (arr[0] = 9) == 9;
    }

    @Tag({ USELESS_ASSERT })
    public static void divideByN(int x, int n) {
        assert n != 12;

        int result = x / n;
    }

    @Tag({ USELESS_ASSERT })
    public static void divideByNMinus12(int x, int n) {
        assert n != 0;

        if (x == 10) {
            int result = x / (n - 12);
        }
    }

    // ===================
    // ===== MEDIUM ======
    // ===================

    @Tag({ USEFUL_ASSERT, TAUTOLOGY_ASSERT, CONTRADICTION_ASSERT })
    public static void normalizeEdgeWeight(PositiveInteger weight, int lowerBound, int higherBound) {
        assert (weight.get() >= lowerBound && weight.get() <= higherBound && lowerBound < higherBound);
        assert (lowerBound < higherBound) || (higherBound <= lowerBound);
        assert (lowerBound < higherBound) && (higherBound <= lowerBound);

        int normalized = (weight.get() - lowerBound) * 100 / (higherBound - lowerBound);

        // ... more stuff ...
    }

    @Tag({ USEFUL_ASSERT, USELESS_ASSERT, TAUTOLOGY_ASSERT, CONTRADICTION_ASSERT, SIDE_EFFECT_ASSERT })
    public static void withdraw(PositiveInteger balance, PositiveInteger amount, int percentage) {
        // assert balance.get() != 0; EXPECTED SUGGESTION
        assert balance.get() - amount.get() >= 0;
        assert balance.get() > 10 + amount.get();
        assert amount.get() + 10 > amount.get();
        assert 2 * balance.get() > (10 + balance.get()) + balance.get();
        assert percentage++ >= 0;
        // // ...
        int percentageWithdrawn = amount.get() * percentage / balance.get();
        balance.set(balance.get() - amount.get());

        // ... more stuff ...
    }

    @Tag({ USEFUL_ASSERT, TAUTOLOGY_ASSERT })
    public static void calculateInterest(PositiveInteger principal, PositiveInteger months, PositiveInteger rate) {
        assert principal.get() > 0;
        assert months.get() + 10 > months.get();

        double interest = principal.get() * (rate.get() / 100);
        double riskModifier = months.get() > 12 ? 1 : 1;
        double finalValue = principal.get() + interest * riskModifier;

        // simulate compounding loop
        for (int i = 0; i < months.get(); i++) {
            finalValue += finalValue * (rate.get() / 1200);
        }

        //  ... more stuff ...
    }

    // ===================
    // ==== ADVANCED =====
    // ===================

    @Tag({ USEFUL_ASSERT, USELESS_ASSERT })
    public static void balanceLoad(PositiveInteger servers, PositiveInteger requests, int maxLoad) {
        // Complex useful assertion involving TWO parameters:
        // Ensures that (requests.get() / servers.get()) is within maxLoad range.
        // If removed, both division-by-zero and out-of-range array accesses can occur.
        assert (servers.get() > 0 && (requests.get() / servers.get()) <= maxLoad);
        assert servers.get() != 2 || requests.get() != 3 || maxLoad != 5;

        // If servers.get() == 0 -> exception
        int[] loadPerServer = new int[servers.get()];
        CappedInteger cappedLoad = new CappedInteger(0, maxLoad);

        // Simulate request distribution
        for (int i = 0; i < requests.get(); i++) {
            // If numServers == 0 -> exception
            int target = i % servers.get();

            int current = loadPerServer[target];
            cappedLoad.set(current + 1);
            loadPerServer[target] = cappedLoad.get();
        }

        // If servers.get() == 0 -> exception
        int avgLoad = requests.get() / servers.get();

        // ... more stuff ...
    }

    @Tag({ USEFUL_ASSERT })
    public static void extractBlock(PositiveInteger matrixSize, CappedInteger blockSize, CappedInteger startIndex) {
        // prevents out-of-bounds AND division-by-zero later
        assert (startIndex.get() + blockSize.get() <= matrixSize.get()) && (matrixSize.get() % blockSize.get() == 0);

        int size   = matrixSize.get();
        int block  = blockSize.get();
        int start  = startIndex.get();

        int[][] matrix = new int[size][size];
        for (int i = 0; i < size; i++)
            for (int j = 0; j < size; j++)
                matrix[i][j] = i + j;

        int[][] blockData = new int[block][block];
        for (int i = 0; i < block; i++)
            for (int j = 0; j < block; j++)
                blockData[i][j] = matrix[start + i][start + j];

        int norm = size / block;  // crashes if assertion was violated

        int checksum = 0;
        for (int i = 0; i < block; i++)
            for (int j = 0; j < block; j++)
                checksum += blockData[i][j] * norm;

        // ... more stuff ...
    }


    //start gemini cases 
    
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

    @Tag({ USEFUL_ASSERT, USELESS_ASSERT })
    public static void nestedArrayAccess(PositiveInteger index, PositiveInteger size) {
        assert index.get() < size.get();
        assert index.get() < size.get() - 10;
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

    @Tag({ USEFUL_ASSERT, USELESS_ASSERT })
    public static void complexMath(PositiveInteger a, PositiveInteger b) {
        // a, b >= 0
        // simple div by zero
        assert a.get() + b.get() != 0;
        assert a.get() + b.get() == 100; // useless
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

    @Tag({ USEFUL_ASSERT, USELESS_ASSERT })
    public static void loopBound(PositiveInteger limit) {
        assert limit.get() < 100; // useful
        assert limit.get() < 5; // useless
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

    // end gemini cases

    //start claude cases - for assertion rewriting:
    @Tag({ USELESS_ASSERT })
    public static void divideByPositive(int x, int n) {
        assert x == 2;

    if (n > 0) {
        int result = x / n;
    }
    }

    @Tag({ USELESS_ASSERT })
    public static void calculateRatio(int numerator, int denominator) {
        assert numerator == 2;

        int ratio = numerator / denominator;
    }

    @Tag({ USELESS_ASSERT })
    public static void processValue(int value, int divisor) {
        assert value == 2;

        if (value > 100) {
            divisor = divisor + 5;
        }
        int result = value / divisor;
    }

    @Tag({ USELESS_ASSERT })
    public static void computeWithCondition(int a, int b) {
        assert a == 2;

        if (a != 0) {
            int temp = 100 / a;
        }
        int result = a / b;
    }

    @Tag({ USELESS_ASSERT })
    public static void nestedDivision(int x, int y, int z) {
        assert x == 2;

        if (x > 10) {
            if (y != 0) {
                int first = x / y;
            }
        }
        int second = x / z;
    }

    @Tag({ USELESS_ASSERT })
    public static void arrayAccess(int[] arr, int index) {
        assert index == 2;

        if (index >= 0) {
            int value = arr[index];
        }
    }

    @Tag({ USELESS_ASSERT })
    public static void multipleOperations(int a, int b, int c) {
        assert a == 2;

        int result1 = a / b;
        int result2 = b / c;
        int result3 = a / c;
    }

    @Tag({ USELESS_ASSERT })
    public static void conditionalDivision(int x, int y) {
        assert x == 10;

        if (x % 2 == 0) {
            int result = x / y;
        } else {
            int result = y / x;
        }
    }

    @Tag({ USELESS_ASSERT })
    public static void loopWithDivision(int n, int divisor) {
        assert n == 2;

        for (int i = 0; i < n; i++) {
            int result = i / divisor;
        }
    }

    @Tag({ USELESS_ASSERT })
    public static void arrayIndexCalculation(int[] data, int size, int index) {
        assert index == 2;

        if (size > 0) {
            int normalizedIndex = index / size;
            int value = data[normalizedIndex];
        }
    }

    @Tag({ USELESS_ASSERT })
    public static void convertCharToIndex(char c, int divisor) {
        assert divisor == 2;

        int charValue = (int) c;
        int index = charValue / divisor;
    }

    @Tag({ USELESS_ASSERT })
    public static void processCharRange(char start, char end, int step) {
    assert start == 2;
    
    int range = end - start;
    int segments = range / step;
    
    for (int i = 0; i < segments; i++) {
        char current = (char) (start + i * step);
    }
    }

    //end claude cases

}
