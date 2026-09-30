package com.accessibleagami.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Insets;
import android.os.Build;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.view.WindowInsets;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.window.OnBackInvokedDispatcher;

import java.util.Locale;

/**
 * Shows agami.html (copied in from the repo root at build time, see
 * app/build.gradle.kts) full screen, and gives the page the phone's own
 * speech engine as window.AndroidTTS. Back is handed to androidBack() in
 * the page, which closes a dialog or steps back toward the dashboard.
 */
public class MainActivity extends Activity implements TextToSpeech.OnInitListener {

    private static final String START_URL = "file:///android_asset/agami.html";
    private static final int BASE_BG = 0xFFEEF1F6; // --base-bg in agami.html

    private WebView web;
    private TextToSpeech tts;
    private volatile boolean ttsReady;
    private volatile String pendingSpeech;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        tts = new TextToSpeech(this, this);

        web = new WebView(this);
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);                 // localStorage: tier, settings, progress
        settings.setMediaPlaybackRequiresUserGesture(false); // pages auto-play their recorded clips
        web.setBackgroundColor(BASE_BG);
        web.setWebViewClient(new WebViewClient());
        web.setWebChromeClient(new WebChromeClient());
        web.addJavascriptInterface(new TtsBridge(), "AndroidTTS");

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(BASE_BG);
        root.addView(web);
        if (Build.VERSION.SDK_INT >= 35) {
            // Android 15+ draws every app edge to edge: keep the page clear
            // of the status bar, the navigation bar and any camera cutout.
            root.setOnApplyWindowInsetsListener((v, insets) -> {
                Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                v.setPadding(bars.left, bars.top, bars.right, bars.bottom);
                return WindowInsets.CONSUMED;
            });
        }
        setContentView(root);
        web.loadUrl(START_URL);

        if (Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    OnBackInvokedDispatcher.PRIORITY_DEFAULT, this::handleBack);
        }
    }

    /** Only leaves the app from the dashboard, onboarding or the first login screen. */
    private void handleBack() {
        web.evaluateJavascript("typeof androidBack === 'function' ? androidBack() : 'exit'", value -> {
            if ("\"exit\"".equals(value)) finish();
        });
    }

    @SuppressWarnings("deprecation")
    @Override
    public void onBackPressed() { // Android 12 and older
        handleBack();
    }

    @Override
    public void onInit(int status) {
        if (status != TextToSpeech.SUCCESS) return;
        // Bangladeshi Bengali first, then Indian Bengali, then any Bengali voice the phone has.
        for (Locale locale : new Locale[]{bengali("BD"), bengali("IN"), bengali(null)}) {
            int result = tts.setLanguage(locale);
            if (result != TextToSpeech.LANG_MISSING_DATA && result != TextToSpeech.LANG_NOT_SUPPORTED) {
                ttsReady = true;
                String waiting = pendingSpeech;
                pendingSpeech = null;
                if (waiting != null) tts.speak(waiting, TextToSpeech.QUEUE_FLUSH, null, "agami");
                return;
            }
        }
    }

    private static Locale bengali(String region) {
        Locale.Builder b = new Locale.Builder().setLanguage("bn");
        if (region != null) b.setRegion(region);
        return b.build();
    }

    /** window.AndroidTTS: speaks what can't be pre-recorded (amounts, dates, names). */
    private class TtsBridge {
        @JavascriptInterface
        public void speak(String text) {
            if (!ttsReady) { pendingSpeech = text; return; }
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "agami");
        }

        @JavascriptInterface
        public void stop() {
            pendingSpeech = null;
            if (ttsReady) tts.stop();
        }

        /** Lets the page play a recorded clip right after a spoken amount (speakThen in agami.html). */
        @JavascriptInterface
        public boolean isSpeaking() {
            return ttsReady && tts.isSpeaking();
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        // A phone call or the home button shouldn't leave the app talking in the background.
        web.evaluateJavascript("typeof stopVoiceChain === 'function' && stopVoiceChain()", null);
        if (ttsReady) tts.stop();
        web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        web.onResume();
    }

    @Override
    protected void onDestroy() {
        tts.shutdown();
        web.destroy();
        super.onDestroy();
    }
}
