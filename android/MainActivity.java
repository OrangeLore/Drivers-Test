package org.driverpractice.roadtrip;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.pm.ApplicationInfo;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.speech.tts.Voice;
import android.webkit.JavascriptInterface;
import android.webkit.JsResult;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/** All content is bundled. There is no listener, server, account or network permission. */
public final class MainActivity extends Activity {
    private static final String HOST = "appassets.androidplatform.net";
    private static final String START = "https://" + HOST + "/assets/index.html";
    private WebView web;
    private TextToSpeech speech;
    private volatile boolean voiceReady;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        FrameLayout frame = new FrameLayout(this);
        frame.setBackgroundColor(Color.rgb(247, 249, 252));
        frame.setOnApplyWindowInsetsListener((view, insets) -> {
            view.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                    insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets;
        });
        web = new WebView(this);
        frame.addView(web, new FrameLayout.LayoutParams(-1, -1));
        setContentView(frame);
        frame.requestApplyInsets();
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setBlockNetworkLoads(true);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);
        settings.setSafeBrowsingEnabled(true);
        WebView.setWebContentsDebuggingEnabled((getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !request.getUrl().toString().equals(START);
            }
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return asset(request.getUrl(), request.getMethod());
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onJsAlert(WebView view, String url, String message, JsResult result) {
                new AlertDialog.Builder(MainActivity.this).setMessage(message)
                    .setPositiveButton("OK", (dialog, which) -> result.confirm())
                    .setOnCancelListener(dialog -> result.cancel()).show();
                return true;
            }
            @Override public boolean onJsConfirm(WebView view, String url, String message, JsResult result) {
                new AlertDialog.Builder(MainActivity.this).setMessage(message)
                    .setPositiveButton("Yes", (dialog, which) -> result.confirm())
                    .setNegativeButton("No", (dialog, which) -> result.cancel())
                    .setOnCancelListener(dialog -> result.cancel()).show();
                return true;
            }
        });
        // This deliberately narrow bridge has no file, intent, URL, storage or networking APIs.
        web.addJavascriptInterface(new OfflineSpeech(), "NativeSpeech");
        speech = new TextToSpeech(this, status -> {
            if (status != TextToSpeech.SUCCESS || speech == null) return;
            if (speech.getVoices() == null) return;
            for (Voice voice : speech.getVoices()) {
                if (!voice.isNetworkConnectionRequired() && "en".equals(voice.getLocale().getLanguage())) {
                    voiceReady = speech.setVoice(voice) == TextToSpeech.SUCCESS;
                    if (voiceReady) break;
                }
            }
        });
        web.loadUrl(START);
    }

    private WebResourceResponse asset(Uri uri, String method) {
        String path = uri.getPath();
        if (!"GET".equals(method) || !"https".equals(uri.getScheme()) || !HOST.equals(uri.getHost())
                || uri.getUserInfo() != null || (uri.getPort() != -1 && uri.getPort() != 443)
                || uri.getQuery() != null || path == null || !path.startsWith("/assets/")) return blocked();
        String name = path.substring("/assets/".length());
        boolean known = name.matches("(?:index\\.html|questions\\.js|questions_more\\.js|ontario\\.js|security\\.js|rewards\\.js|parking\\.js|rewards-ui\\.js|rewards\\.css|achievement-popups\\.css|LICENSE\\.txt|SIGN-REVIEW\\.txt|images/[a-z0-9-]+\\.svg)");
        if (!known) return blocked();
        try {
            InputStream stream = getAssets().open(name);
            String type = name.endsWith(".html") ? "text/html" : name.endsWith(".js") ? "application/javascript"
                : name.endsWith(".css") ? "text/css" : name.endsWith(".svg") ? "image/svg+xml" : "text/plain";
            Map<String,String> headers = new HashMap<>();
            headers.put("X-Content-Type-Options", "nosniff");
            headers.put("Cache-Control", "no-store");
            headers.put("Referrer-Policy", "no-referrer");
            return new WebResourceResponse(type, "UTF-8", 200, "OK", headers, stream);
        } catch (Exception exception) { return blocked(); }
    }

    private WebResourceResponse blocked() {
        return new WebResourceResponse("text/plain", "UTF-8", 403, "Forbidden", new HashMap<>(), new ByteArrayInputStream(new byte[0]));
    }

    private final class OfflineSpeech {
        @JavascriptInterface public boolean speak(String text, double rate) {
            if (!voiceReady || text == null || text.length() > 12000) return false;
            final float safeRate = Double.isFinite(rate) ? (float)Math.max(0.6, Math.min(1.2, rate)) : 0.95f;
            runOnUiThread(() -> {
                if (!voiceReady || speech == null || !START.equals(web.getUrl())) return;
                speech.setSpeechRate(safeRate);
                speech.speak(text, TextToSpeech.QUEUE_FLUSH, null, "roadtrip-question");
            });
            return true;
        }
        @JavascriptInterface public void stop() { runOnUiThread(() -> { if (speech != null) speech.stop(); }); }
    }

    @Override public void onBackPressed() {
        web.evaluateJavascript("window.roadTripBack ? window.roadTripBack() : false", result -> {
            if (!"true".equals(result)) finish();
        });
    }
    @Override protected void onPause() { if (speech != null) speech.stop(); super.onPause(); }
    @Override protected void onDestroy() {
        voiceReady = false;
        if (speech != null) { speech.stop(); speech.shutdown(); speech = null; }
        if (web != null) { web.removeJavascriptInterface("NativeSpeech"); web.destroy(); }
        super.onDestroy();
    }
}
