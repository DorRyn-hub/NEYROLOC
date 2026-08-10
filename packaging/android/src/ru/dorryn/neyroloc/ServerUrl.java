package ru.dorryn.neyroloc;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.Locale;

/** Pure URL validation shared by the setup form and the TCP reachability probe. */
final class ServerUrl {

    static final int LOCAL_SERVER_PORT = 8765;

    private ServerUrl() {
    }

    /**
     * Validate and normalize a server address.
     *
     * A bare host is the convenient LAN form and receives http + port 8765.
     * Explicit http/https URLs keep their standard or explicitly supplied port,
     * so https://example.test correctly uses 443 instead of 8765.
     */
    static String normalize(String value) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException("server address is empty");
        }

        String raw = value.trim();
        boolean explicitScheme = raw.contains("://");
        String candidate = explicitScheme ? raw : "http://" + raw;

        final URI parsed;
        try {
            parsed = new URI(candidate);
        } catch (URISyntaxException e) {
            throw new IllegalArgumentException("invalid server address", e);
        }

        String scheme = parsed.getScheme();
        scheme = scheme == null ? "" : scheme.toLowerCase(Locale.ROOT);
        if (!scheme.equals("http") && !scheme.equals("https")) {
            throw new IllegalArgumentException("only http and https are supported");
        }
        if (parsed.isOpaque() || parsed.getHost() == null || parsed.getHost().isEmpty()) {
            throw new IllegalArgumentException("server host is missing");
        }
        if (parsed.getUserInfo() != null) {
            throw new IllegalArgumentException("credentials in the server URL are not supported");
        }
        if (parsed.getFragment() != null) {
            throw new IllegalArgumentException("URL fragments are not supported");
        }

        int port = parsed.getPort();
        if (port == 0 || port > 65535) {
            throw new IllegalArgumentException("invalid server port");
        }
        if (!explicitScheme && port < 0) {
            port = LOCAL_SERVER_PORT;
        }

        try {
            URI normalized = new URI(
                    scheme,
                    null,
                    parsed.getHost(),
                    port,
                    parsed.getPath(),
                    parsed.getQuery(),
                    null
            );
            return normalized.toASCIIString();
        } catch (URISyntaxException e) {
            throw new IllegalArgumentException("invalid server address", e);
        }
    }

    static String hostForProbe(String value) {
        return parseNormalized(value).getHost();
    }

    static int portForProbe(String value) {
        URI parsed = parseNormalized(value);
        return effectivePort(parsed);
    }

    static boolean sameOrigin(String trustedValue, String candidateValue) {
        URI trusted = parseNormalized(trustedValue);
        URI candidate = parseNormalized(candidateValue);
        return trusted.getScheme().equalsIgnoreCase(candidate.getScheme())
                && trusted.getHost().equalsIgnoreCase(candidate.getHost())
                && effectivePort(trusted) == effectivePort(candidate);
    }

    private static int effectivePort(URI parsed) {
        if (parsed.getPort() > 0) {
            return parsed.getPort();
        }
        return "https".equalsIgnoreCase(parsed.getScheme()) ? 443 : 80;
    }

    private static URI parseNormalized(String value) {
        try {
            return new URI(normalize(value));
        } catch (URISyntaxException e) {
            // normalize() already guarantees URI syntax; keep a stable public error type.
            throw new IllegalArgumentException("invalid normalized server address", e);
        }
    }
}
