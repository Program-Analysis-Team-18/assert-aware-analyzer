package jpamb.cases;

class CappedInteger {
    private int value;
    private final int cap;

    CappedInteger(int value, int cap) {
        this.cap = cap;
        set(value);
    }

    void set(int value) {
        if (value > cap) throw new IllegalArgumentException();
        this.value = value;
    }
    
    int get() { return value; }

    int getCap() { return cap; }
}