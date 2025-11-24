package jpamb.cases;


class PositiveInteger {
    private int check_value;

    PositiveInteger(int value) { set(value); }

    void set(int newValue) {
        if (newValue < 0) throw new IllegalArgumentException();
        this.check_value = newValue;
    }

    int get() { return check_value; }
}   