package jpamb.cases;

/**
 * A class that demonstrates method chaining with side effects.
 * Used for testing side effects in fluent API patterns within assertions.
 */
public class SideEffectChain {
    int counter = 0;
    static int state;
    
    public SideEffectChain increment() {
        counter++;
        state++;
        return this;
    }
    
    public SideEffectChain doubleIncrement() {
        return increment().increment();
    }
    
    public boolean isPositive() {
        return counter > 0;
    }
}
