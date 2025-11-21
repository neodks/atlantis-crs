public class Example {
    public void vulnerableMethod(String userInput) {
        // SQL 인젝션 취약점
        String query = "SELECT * FROM users WHERE name = '" + userInput + "'";
        executeQuery(query);
    }
    
    private void executeQuery(String query) {
        System.out.println(query);
    }
}
