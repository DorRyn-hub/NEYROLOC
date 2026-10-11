package ru.dorryn.neyroloc;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.inputmethod.EditorInfo;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.URI;

/**
 * NEYROLOC для Android: тонкая нативная оболочка над мобильным веб-клиентом,
 * который отдаёт настольное приложение (Файл -> Удалённый доступ с телефона).
 *
 * Перед загрузкой страницы адрес быстро проверяется TCP-пробой (4 секунды),
 * чтобы неверный адрес/выключенный сервер давали мгновенную понятную ошибку,
 * а не чёрный экран на минуты. Во время загрузки — экран с индикатором.
 */
public class MainActivity extends Activity {

    private static final int BG = Color.parseColor("#0d111a");
    private static final int SURFACE = Color.parseColor("#1b2433");
    private static final int BORDER = Color.parseColor("#2b3749");
    private static final int TEXT = Color.parseColor("#eef3fa");
    private static final int MUTED = Color.parseColor("#a6b3c5");
    private static final int ACCENT = Color.parseColor("#6d8cff");
    private static final int DANGER = Color.parseColor("#ff7184");

    private static final int PROBE_TIMEOUT_MS = 4000;

    private SharedPreferences prefs;
    private WebView webView;
    private int attempt = 0;  // защита от гонок между пробами

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences("neyroloc", MODE_PRIVATE);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);

        String url = prefs.getString("server_url", "");
        if (url.isEmpty()) {
            showSetup(null);
        } else {
            connectTo(url);
        }
    }

    // ----- подключение с быстрой проверкой доступности -----

    private void connectTo(String url) {
        showLoading("Подключение к компьютеру…");
        final int myAttempt = ++attempt;
        new Thread(() -> {
            String error = null;
            try {
                URI u = URI.create(url);
                int port = u.getPort() > 0 ? u.getPort() : 8765;
                try (Socket s = new Socket()) {
                    s.connect(new InetSocketAddress(u.getHost(), port), PROBE_TIMEOUT_MS);
                }
            } catch (Exception e) {
                error = "Компьютер не отвечает по адресу " + url + ".\n\n"
                        + "Проверьте: та же Wi-Fi-сеть, в настольном приложении включён "
                        + "удалённый доступ, адрес совпадает с показанным на компьютере.";
            }
            final String err = error;
            runOnUiThread(() -> {
                if (myAttempt != attempt) return;  // уже начали другую попытку
                if (err != null) {
                    showSetup(err);
                } else {
                    showWeb(url);
                }
            });
        }).start();
    }

    // ----- экраны -----

    private LinearLayout screenBase() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(BG);
        int pad = dp(28);
        root.setPadding(pad, pad, pad, pad);
        return root;
    }

    private TextView logoView() {
        TextView logo = new TextView(this);
        logo.setText("N");
        logo.setTextColor(Color.WHITE);
        logo.setTextSize(30);
        logo.setTypeface(Typeface.DEFAULT_BOLD);
        logo.setGravity(Gravity.CENTER);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(ACCENT);
        bg.setCornerRadius(dp(14));
        logo.setBackground(bg);
        return logo;
    }

    private void showLoading(String message) {
        LinearLayout root = screenBase();

        LinearLayout.LayoutParams logoLp = new LinearLayout.LayoutParams(dp(64), dp(64));
        logoLp.gravity = Gravity.CENTER_HORIZONTAL;
        logoLp.bottomMargin = dp(18);
        root.addView(logoView(), logoLp);

        ProgressBar spinner = new ProgressBar(this);
        spinner.getIndeterminateDrawable().setTint(ACCENT);
        LinearLayout.LayoutParams spLp = new LinearLayout.LayoutParams(dp(40), dp(40));
        spLp.gravity = Gravity.CENTER_HORIZONTAL;
        root.addView(spinner, spLp);

        TextView text = new TextView(this);
        text.setText(message);
        text.setTextColor(MUTED);
        text.setTextSize(14);
        text.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams tLp = wrap();
        tLp.topMargin = dp(14);
        root.addView(text, tLp);

        Button change = new Button(this);
        change.setText("Изменить адрес");
        change.setTextColor(MUTED);
        change.setTextSize(13);
        change.setAllCaps(false);
        change.setBackgroundColor(Color.TRANSPARENT);
        change.setOnClickListener(v -> {
            attempt++;  // отменить исход текущей пробы
            showSetup(null);
        });
        LinearLayout.LayoutParams cLp = wrap();
        cLp.topMargin = dp(20);
        cLp.gravity = Gravity.CENTER_HORIZONTAL;
        root.addView(change, cLp);

        setContentView(root);
    }

    private void showSetup(String error) {
        LinearLayout root = screenBase();

        LinearLayout.LayoutParams logoLp = new LinearLayout.LayoutParams(dp(64), dp(64));
        logoLp.gravity = Gravity.CENTER_HORIZONTAL;
        logoLp.bottomMargin = dp(14);
        root.addView(logoView(), logoLp);

        TextView title = new TextView(this);
        title.setText("NEYROLOC");
        title.setTextColor(TEXT);
        title.setTextSize(21);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams titleLp = wrap();
        titleLp.gravity = Gravity.CENTER_HORIZONTAL;
        root.addView(title, titleLp);

        TextView hint = new TextView(this);
        hint.setText(error != null
                ? error
                : "Адрес компьютера показан в настольном приложении:\nФайл → Удалённый доступ с телефона");
        hint.setTextColor(error != null ? DANGER : MUTED);
        hint.setTextSize(14);
        hint.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams hintLp = wrap();
        hintLp.topMargin = dp(10);
        hintLp.bottomMargin = dp(22);
        root.addView(hint, hintLp);

        final EditText addr = new EditText(this);
        addr.setHint("192.168.1.10:8765");
        addr.setText(prefs.getString("server_url", "")
                .replace("http://", "").replace("https://", ""));
        addr.setTextColor(TEXT);
        addr.setHintTextColor(MUTED);
        addr.setTextSize(16);
        addr.setSingleLine(true);
        addr.setImeOptions(EditorInfo.IME_ACTION_GO);
        addr.setInputType(InputType.TYPE_TEXT_VARIATION_URI);
        addr.setPadding(dp(16), dp(14), dp(16), dp(14));
        GradientDrawable addrBg = new GradientDrawable();
        addrBg.setColor(SURFACE);
        addrBg.setCornerRadius(dp(12));
        addrBg.setStroke(dp(1), BORDER);
        addr.setBackground(addrBg);
        root.addView(addr, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));

        Button connect = new Button(this);
        connect.setText("Подключиться");
        connect.setTextColor(Color.WHITE);
        connect.setTextSize(16);
        connect.setTypeface(Typeface.DEFAULT_BOLD);
        connect.setAllCaps(false);
        GradientDrawable btnBg = new GradientDrawable();
        btnBg.setColor(ACCENT);
        btnBg.setCornerRadius(dp(12));
        connect.setBackground(btnBg);
        connect.setPadding(dp(20), dp(12), dp(20), dp(12));
        LinearLayout.LayoutParams btnLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        btnLp.topMargin = dp(14);
        root.addView(connect, btnLp);

        Runnable go = () -> {
            String value = addr.getText().toString().trim();
            if (value.isEmpty()) return;
            if (!value.startsWith("http://") && !value.startsWith("https://")) {
                value = "http://" + value;
            }
            if (!value.matches(".*:\\d+.*")) {
                value = value + ":8765";
            }
            prefs.edit().putString("server_url", value).apply();
            connectTo(value);
        };
        connect.setOnClickListener(v -> go.run());
        addr.setOnEditorActionListener((v, actionId, event) -> {
            go.run();
            return true;
        });

        setContentView(root);
    }

    // ----- WebView -----

    @SuppressLint("SetJavaScriptEnabled")
    private void showWeb(String url) {
        webView = new WebView(this);
        webView.setBackgroundColor(BG);
        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);   // localStorage: код сопряжения
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, WebResourceRequest request,
                                        WebResourceError e) {
                if (request.isForMainFrame()) {
                    runOnUiThread(() -> showSetup(
                            "Сервер найден, но страница не загрузилась. "
                            + "Перезапустите удалённый доступ на компьютере и попробуйте снова."));
                }
            }
        });
        webView.loadUrl(url);
        setContentView(webView);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private LinearLayout.LayoutParams wrap() {
        return new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
    }
}
