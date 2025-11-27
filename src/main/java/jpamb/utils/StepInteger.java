package jpamb.utils;

public class StepInteger {
    private int value;
    private final int step;

    public StepInteger(int v, int step) { this.step = step; set(v); }

    public void set(int v) {
        if (v % step != 0) throw new IllegalArgumentException();
        value = v;
    }

    public int get() { return value; }
}