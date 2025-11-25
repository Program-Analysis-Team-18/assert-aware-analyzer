package jpamb.cases;

class StepInteger {
    private int value;
    private final int step;
    StepInteger(int v, int step) { this.step = step; set(v); }
    void set(int v) {
        if (v % step != 0) throw new IllegalArgumentException();
        value = v;
    }
    int get() { return value; }
}