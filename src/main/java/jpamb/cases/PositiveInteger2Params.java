package jpamb.cases;

import jpamb.utils.Case;


public class PositiveInteger2Params {

        private int check_value;
        private int check_value2;

        PositiveInteger2Params(int value1, int value2) { set(value1); set2(value2); }

        void set(int newValue) {
            if (newValue < 0) throw new IllegalArgumentException();
            this.check_value = newValue;
        }

        void set2(int newValue) {
            if (newValue < 0) throw new IllegalArgumentException();
            this.check_value2 = newValue;
        }

        int get() { return check_value; }
}   