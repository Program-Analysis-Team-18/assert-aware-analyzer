package jpamb.utils;

public class CappedInteger {
    private int value;
    private final int cap;

    public CappedInteger(int value, int cap) {
        this.cap = cap;
        set(value);
    }

    public void set(int value) {
        if (value > cap) throw new IllegalArgumentException();
        this.value = value;
    }
    
    public int get() { return value; }

    public int getCap() { return cap; }
}