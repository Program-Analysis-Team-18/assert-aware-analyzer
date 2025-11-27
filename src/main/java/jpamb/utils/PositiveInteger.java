package jpamb.utils;


public class PositiveInteger {
    private int check_value;

    public PositiveInteger(int value) { set(value); }

    public void set(int newValue) {
        if (newValue < 0) throw new IllegalArgumentException();
        this.check_value = newValue;
    }

    public int get() { return check_value; }
}   