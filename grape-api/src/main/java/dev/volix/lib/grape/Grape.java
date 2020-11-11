package dev.volix.lib.grape;

/**
 * @author Tobias Büser
 */
public class Grape extends ServiceRegistry {

    private static Grape instance;

    public static Grape getInstance() {
        if (instance == null) instance = new Grape();
        return instance;
    }

}
