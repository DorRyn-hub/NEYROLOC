package ru.dorryn.neyroloc;

public final class ServerUrlTest {

    private interface CheckedAction {
        void run();
    }

    private static void assertEquals(Object expected, Object actual) {
        if (!expected.equals(actual)) {
            throw new AssertionError("expected=" + expected + ", actual=" + actual);
        }
    }

    private static void assertRejected(CheckedAction action) {
        try {
            action.run();
        } catch (IllegalArgumentException expected) {
            return;
        }
        throw new AssertionError("address should have been rejected");
    }

    public static void main(String[] args) {
        assertEquals("http://192.168.1.5:8765", ServerUrl.normalize("192.168.1.5"));
        assertEquals("http://192.168.1.5:9000", ServerUrl.normalize("192.168.1.5:9000"));
        assertEquals(
                "http://example.test:8765?code=123456",
                ServerUrl.normalize("example.test?code=123456")
        );
        assertEquals("https://public.example.test", ServerUrl.normalize("https://public.example.test"));
        assertEquals(443, ServerUrl.portForProbe("https://public.example.test"));
        assertEquals(80, ServerUrl.portForProbe("http://public.example.test"));
        assertEquals(9443, ServerUrl.portForProbe("https://public.example.test:9443"));
        assertEquals(true, ServerUrl.sameOrigin(
                "https://public.example.test/chat?code=123456",
                "https://public.example.test/mark.svg"
        ));
        assertEquals(false, ServerUrl.sameOrigin(
                "https://public.example.test",
                "https://other.example.test"
        ));
        assertEquals(false, ServerUrl.sameOrigin(
                "http://192.168.1.5:8765",
                "https://192.168.1.5:8765"
        ));

        assertRejected(() -> ServerUrl.normalize(""));
        assertRejected(() -> ServerUrl.normalize("ftp://example.test"));
        assertRejected(() -> ServerUrl.normalize("https://user:password@example.test"));
        assertRejected(() -> ServerUrl.normalize("https://example.test/#fragment"));
        assertRejected(() -> ServerUrl.normalize("https://example.test:0"));
        assertRejected(() -> ServerUrl.normalize("https://example.test:99999"));

        System.out.println("ServerUrlTest OK");
    }
}
