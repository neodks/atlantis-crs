
package java;

public class Example {
    public void execute() {
        String s = null;
        // This will cause a null pointer exception
        System.out.println(s.length());
    }

    public static void main(String[] args) {
        Example example = new Example();
        example.execute();
    }
}
