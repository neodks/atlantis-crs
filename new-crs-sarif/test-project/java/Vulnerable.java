package java;

public class Vulnerable {
    public void execute() {
        String s = null;
        // Null pointer dereference vulnerability
        System.out.println(s.length());
    }

    public static void main(String[] args) {
        Vulnerable v = new Vulnerable();
        v.execute();
    }
}
