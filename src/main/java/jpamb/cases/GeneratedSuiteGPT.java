package jpamb.cases;

import jpamb.utils.Tag;
import static jpamb.utils.Tag.TagType.*;

public class GeneratedSuiteGPT {


    // Simple global state for side-effect assertions
    private static int globalState = 0;

    // ===========================
    //  SIMPLE SYNTACTIC CASES
    // ===========================

    /**
     * Contains:
     *  - assert true              -> USELESS_ASSERT
     *  - x.get() + 1 > x.get()    -> TAUTOLOGY_ASSERT
     *  - x.get() < x.get()        -> CONTRADICTION_ASSERT
     */
    @Tag({ USELESS_ASSERT, TAUTOLOGY_ASSERT, CONTRADICTION_ASSERT })
    public static void simpleSyntactic(PositiveInteger x) {
        // always true, no relation to later code -> useless
        assert true;

        // arithmetic tautology
        assert x.get() + 1 > x.get();

        // arithmetic contradiction
        assert x.get() < x.get();

        int y = x.get(); // just to have some body
        if (y > 0) {
            y--;
        }
    }

    // ===========================
    //  RELATIONAL PRECONDITIONS
    // ===========================

    /**
     * Assertions:
     *  - denom.get() > 0            -> USEFUL_ASSERT (prevents division-by-zero)
     *  - limit.get() + 1 > limit.get() -> TAUTOLOGY_ASSERT
     */
    @Tag({ USEFUL_ASSERT, TAUTOLOGY_ASSERT })
    public static void relationalGuards(PositiveInteger num,
                                        PositiveInteger denom,
                                        PositiveInteger limit) {
        // useful: if removed, denom may become 0 and cause a crash
        assert denom.get() > 0;

        // tautology on a parameter
        assert limit.get() + 1 > limit.get();

        int ratio = num.get() / denom.get();

        int[] arr = new int[Math.max(1, limit.get())];
        arr[ratio % arr.length] = ratio;
    }

    // ===========================
    //   SIDE-EFFECT ASSERTIONS
    // ===========================

    /**
     * Assertion:
     *  - globalState++ >= 0   -> SIDE_EFFECT_ASSERT
     *    (assert used only to trigger side effect on global state)
     */
    @Tag({ SIDE_EFFECT_ASSERT })
    public static void bumpGlobalInAssert() {
        // side effect on global state, assert value itself is irrelevant
        assert globalState++ >= 0;
    }

    /**
     * Assertion:
     *  - (arr[0] = arr[0] + 1) > 0  -> SIDE_EFFECT_ASSERT
     *    (writes into array inside assert)
     */
    @Tag({ SIDE_EFFECT_ASSERT })
    public static void assertArraySideEffect(int[] arr) {
        if (arr == null || arr.length == 0) {
            return;
        }

        // side-effect: modifies arr[0] inside assertion
        assert (arr[0] = arr[0] + 1) > 0;
    }

    // ===========================
    //   DYNAMIC GUARDING CASES
    // ===========================

    /**
     * Assertion:
     *  - start + length <= size and size, start, length non-negative
     *    -> USEFUL_ASSERT (prevents out-of-bounds in the loop)
     */
    @Tag({ USEFUL_ASSERT })
    public static void safeSlice(PositiveInteger size,
                                 PositiveInteger start,
                                 PositiveInteger length) {
        int n = size.get();
        int s = start.get();
        int len = length.get();

        // if removed: can cause out-of-bounds write/reads below
        assert n >= 0 && s >= 0 && len >= 0 && s + len <= n;

        int[] arr = new int[n];
        for (int i = 0; i < len; i++) {
            arr[s + i] = i;
        }

        int sum = 0;
        for (int i = s; i < s + len; i++) {
            sum += arr[i];
        }
    }

    /**
     * Similar to extractBlock but smaller:
     * ensures block fits in matrix and divisor is non-zero.
     */
    @Tag({ USEFUL_ASSERT })
    public static void safeSubmatrix(PositiveInteger matrixSize,
                                     CappedInteger blockSize,
                                     CappedInteger startIndex) {
        int n = matrixSize.get();
        int b = blockSize.get();
        int start = startIndex.get();

        // useful: if removed, can cause out-of-bounds + division-by-zero later
        assert n > 0 &&
               b > 0 &&
               start >= 0 &&
               start + b <= n &&
               n % b == 0;

        int[][] m = new int[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                m[i][j] = i + j;
            }
        }

        int[][] block = new int[b][b];
        for (int i = 0; i < b; i++) {
            for (int j = 0; j < b; j++) {
                block[i][j] = m[start + i][start + j];
            }
        }

        int factor = n / b;
        int checksum = 0;
        for (int i = 0; i < b; i++) {
            for (int j = 0; j < b; j++) {
                checksum += block[i][j] * factor;
            }
        }
    }

    // ===========================
    //   MIXED LABEL CASE
    // ===========================

    /**
     * Contains:
     *  - useful assert on x        -> USEFUL_ASSERT
     *  - tautology on x            -> TAUTOLOGY_ASSERT
     *  - side-effect on arr[0]     -> SIDE_EFFECT_ASSERT
     */
    @Tag({ USEFUL_ASSERT, TAUTOLOGY_ASSERT, SIDE_EFFECT_ASSERT })
    public static void mixedAssertions(PositiveInteger x, int[] arr) {
        if (arr == null || arr.length == 0) {
            return;
        }

        // useful: ensures we never divide by zero below
        assert x.get() > 0;

        // tautology on parameter
        assert x.get() + 1 > x.get();

        // side effect: arr[0] is overwritten inside assert
        assert (arr[0] = x.get()) == x.get();

        int[] local = new int[x.get()];
        local[0] = arr[0];
    }

}
