package jpamb.utils;

import java.lang.annotation.*;

// Annotation for tagging methods
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Tag {
  TagType[] value();

  public static enum TagType {
    SIDE_EFFECT_ASSERT,
    USELESS_ASSERT,
    USEFUL_ASSERT,
    TAUTOLOGY_ASSERT,
    CONTRADICTION_ASSERT,
  }
}
