package jpamb.cases;

import jpamb.utils.Case;


public class PositiveInteger {

        private int value;
        private int value2;

        PositiveInteger(int value, int value2) { set(value, value2); }

        void set(int newValue, int newValue2) {
            if (newValue < 0) throw new IllegalArgumentException();
            this.value = newValue;
            this.value2 = newValue2;
        }

        int get() { return value; }
}   