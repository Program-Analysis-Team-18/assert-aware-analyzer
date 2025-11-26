package jpamb.cases;

import jpamb.utils.Tag;

import static jpamb.utils.Tag.TagType.*;

/**
 * Test suite for complex nested side effects in assertions.
 * These tests are more complex than the simple changeStateNested() example,
 * covering edge cases like multi-level nesting, conditional execution,
 * method chaining, array modifications, and recursive patterns.
 */
public class ComplexNestedSideEffect {

    static int state;
    static int[] sideEffectArray = new int[10];
    static int nestedCounter = 0;

    // ===========================================
    // Multi-level nested side effects (3 levels)
    // ===========================================

    // Level 3: Actually performs the side effect
    private void deepSideEffect() {
        sideEffectArray[0]++;
        nestedCounter++;
    }

    // Level 2: Conditionally calls level 3, performs its own side effect
    private boolean midLevelSideEffect(int threshold) {
        sideEffectArray[1]++;
        if (nestedCounter < threshold) {
            deepSideEffect();
        }
        return nestedCounter > 0;
    }

    // Level 1: Calls level 2 with conditional logic, has its own side effect
    private boolean topLevelSideEffect(boolean condition) {
        sideEffectArray[2]++;
        return condition && midLevelSideEffect(5);
    }

    // Test with 3 levels of nested side effects in assert
    @Tag({ SIDE_EFFECT_ASSERT })
    public void complexNestedSideEffects() {
        assert topLevelSideEffect(true);
    }

    // ===========================================
    // Logical operators with nested side effects
    // ===========================================

    // Test combining nested calls with logical operators
    @Tag({ SIDE_EFFECT_ASSERT })
    public void nestedSideEffectsWithLogicalOps() {
        // Both methods have side effects, and both will be called due to || operator
        assert topLevelSideEffect(false) || midLevelSideEffect(10);
    }

    // ===========================================
    // Method chaining with side effects
    // ===========================================

    // Test with method chaining and nested side effects (using external SideEffectChain class)
    @Tag({ SIDE_EFFECT_ASSERT })
    public void chainedSideEffects() {
        SideEffectChain chain = new SideEffectChain();
        assert chain.doubleIncrement().increment().isPositive();
    }

    // ===========================================
    // Array modifications with nested calls
    // ===========================================

    // Test with nested side effects in array operations
    private boolean modifyArrayNested(int[] arr, int index) {
        if (index >= 0 && index < arr.length) {
            arr[index] = incrementAndGetState();
            return true;
        }
        return false;
    }

    private int incrementAndGetState() {
        state++;
        nestedCounter++;
        return state;
    }

    @Tag({ SIDE_EFFECT_ASSERT })
    public void nestedArraySideEffects() {
        int[] arr = new int[10];
        assert modifyArrayNested(arr, 0) && modifyArrayNested(arr, 1);
    }

    // ===========================================
    // Recursive side effects
    // ===========================================

    // Test with recursive side effects
    private boolean recursiveSideEffect(int depth) {
        if (depth <= 0) {
            return true;
        }
        state++;
        return recursiveSideEffect(depth - 1);
    }

    @Tag({ SIDE_EFFECT_ASSERT })
    public void recursiveNestedSideEffects() {
        assert recursiveSideEffect(3);
    }
}
