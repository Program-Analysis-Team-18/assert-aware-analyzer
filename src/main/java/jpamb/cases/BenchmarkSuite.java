package jpamb.cases;

import jpamb.utils.CappedInteger;
import jpamb.utils.PositiveInteger;
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
        assert n != 10;

        int result = x / n;
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
}
