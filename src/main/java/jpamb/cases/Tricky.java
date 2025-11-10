package jpamb.cases;

import jpamb.utils.*;
import static jpamb.utils.Tag.TagType.*;

public class Tricky {

  @Case("(0) -> assertion error")
  @Case("(24) -> ok")
  @Tag({ LOOP })
  public static void collatz(int n) { 
    assert n > 0;
    while (n != 1) { 
      if (n % 2 == 0) { 
        n = n / 2;
      } else { 
        n = n * 3 + 1;
      }
    }
  }

  public static void crashy(int x, int y, int z, char[] chars) {
    if (x > 10 && x < 50) {
      int[] bad = new int[-1];
    }

    if (y == 0) {
      z = 100 / y;
    }

    if (z == x) {
      int overflow = Integer.MAX_VALUE * Integer.MAX_VALUE;
    }

    if(z % 20 == 5) {
      if(x % y == 3) {
        int[] arr = new int[8];
        arr[z] = 1;
      }
    }

    if (z > 0) {
        if(x % z == 137) {
          int array[] = null;
          array[1] = 0;
        }
    }

    if(x % z == 37) {
      if(y > 0) {
        if(x % y != 0)
          while(true) {}
        }
    }

    if(x == 0) {
      if(z < 0) {
        assert false;
      }
    }

    assert chars[0] == 'p' &&
           chars[1] == 'r' &&
           chars[2] == 'o' &&
           chars[3] == 'g' &&
           chars[4] == 'r' &&
           chars[5] == 'a' &&
           chars[6] == 'm' &&
           chars[7] == 'a' &&
           chars[8] == 'n' &&
           chars[9] == 'a' &&
           chars[10] == 'l' &&
           chars[11] == 'y' &&
           chars[12] == 's' &&
           chars[13] == 'i' &&
           chars[14] == 's';

    return;
  }

  public static void charToInt(int[] ints, char[] chars) {
    assert ints[0] == chars[0] + '\0';
    assert ints[1] == chars[2] + '\0';
    assert ints[3] == chars[4] + '\0';
    assert ints[2] == chars[6] + '\0';
    assert ints[10] == chars[15] + '\0';
  }
}
