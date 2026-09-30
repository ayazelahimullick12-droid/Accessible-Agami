# Accessible Agami

An accessible, adaptive version of the Agami app for rural members in Bangladesh, including people who
cannot read. It adapts between tiers (১২৩ voice menu → [নতুন] → মাঝারি → দক্ষ): the app suggests moving up
or down, and the member always decides.

One codebase, two ways to ship it:

| | What | Where |
|---|---|---|
| **The app** | `agami.html` + `assets/` (audio clips, optional icons) | repo root |
| **Android APK** | a WebView wrapper that bundles the app and gives it the phone's Bengali voice | `android/` |
| **Website** | the same files served as a static site | `render.yaml` |

Editing `agami.html` or replacing a clip in `assets/audio/` updates both: the Android build copies the files
in automatically, and Render redeploys on every push.

## Audio

- `assets/audio/` holds every clip. The app's original clips are unchanged. The clips added for the ১২৩ tier,
  onboarding, tier prompts, button speakers, dialogs and settings are TTS stand-ins in a Bangladeshi voice.
- **[AUDIO_SCRIPTS.md](AUDIO_SCRIPTS.md)** lists each added clip's file name, where it plays, and its script.
  To use your own recording, save it under the same file name in `assets/audio/`.
- The scripts live in the `CLIP_TEXT` block of `agami.html`. `tools/generate_audio.py` reads them to make
  missing stand-ins (`python tools/generate_audio.py`, after `pip install edge-tts`) and to refresh the sheet
  (`--doc`). It never overwrites an existing file unless you pass `--force` with clip names.

---

## Build the Android app (Android Studio)

The project uses AGP 9.3 and Gradle 9.6, which Android Studio **2026.1.2 (Quail 2) or newer** opens. It was
built successfully from the command line with the JDK that ships with Android Studio Quail 4 (2026.1.4).

1. **Get the code.** Either use this folder, or clone it:
   `git clone https://github.com/ayazelahimullick12-droid/Accessible-Agami.git`
2. **Open the `android` folder**, not the repo root: Android Studio → *File → Open…* → select
   `Accessible-Agami/android` → *OK*. Trust the project if asked.
3. **Wait for Gradle sync** (bottom status bar). The first time it downloads Gradle and the Android 16
   (API 36) platform, which takes a few minutes. If a banner offers to install a missing SDK platform, accept
   it. If it offers an AGP upgrade, you can skip it.
4. **Try it on a phone.** On the phone, enable *Developer options → USB debugging* (tap *Build number* 7
   times in *About phone* to unlock Developer options), connect by USB, allow the prompt, pick the phone in
   the device list at the top of Studio, and press **Run ▶**.
5. **Make an APK to share:**
   - *Quick test APK:* *Build → Generate App Bundles or APKs → Generate APKs*. When it finishes, click
     *locate*. The file is `android/app/build/outputs/apk/debug/app-debug.apk`.
   - *Release APK (for real users):* *Build → Generate Signed App Bundle or APK… → APK → Next →
     Create new…* keystore. **Keep the keystore file and passwords safe;** every future update must be
     signed with the same key. Choose *release → Create*. The file is
     `android/app/release/app-release.apk`.
6. **Install on members' phones:** copy the APK over (USB, Bluetooth, Google Drive…), open it, and allow
   *Install unknown apps* when Android asks.
7. **Bengali voice on each phone (important).** Amounts and dates are read by the phone's own speech
   engine. On each phone: *Settings → search "Text-to-speech" → Preferred engine: Speech Services by Google →
   ⚙ → Install voice data → বাংলা (বাংলাদেশ)*. Without it, recorded clips still play but amounts stay
   silent.

Command-line alternative (no Studio UI): `cd android` then `gradlew.bat assembleDebug` (Windows) or
`./gradlew assembleDebug`.

**What the wrapper does** (`android/app/src/main/java/com/accessibleagami/app/MainActivity.java`):
- **Speech:** exposes the phone's speech engine to the page as `window.AndroidTTS`, with `speak`, `stop`
  and `isSpeaking`. It prefers Bangladeshi Bengali, then Indian Bengali. `isSpeaking` lets a recorded clip
  play right after a spoken amount.
- **Auto-play:** allows audio without a tap first, so pages can speak for themselves.
- **Back:** closes a dialog, or goes back to the dashboard, instead of quitting the app.
- **Phone behaviour:** keeps the page clear of the status and navigation bars, and silences audio when the
  app goes to the background (for example during a phone call).

## Host the website (Render)

1. Make sure the latest code is pushed to GitHub (`main` branch).
2. Go to **https://render.com** → *Sign up / Log in with GitHub*.
3. Click **New → Blueprint**. Connect your GitHub account if asked, choose the **Accessible-Agami**
   repository, and Render finds `render.yaml`. Review and click **Deploy Blueprint** (or *Apply*).
   - *Without a Blueprint:* **New → Static Site** → pick the repo → set the **Build Command** to
     `rm -rf public && mkdir -p public && cp -r assets public/ && cp agami.html public/index.html && cp agami.html public/agami.html`
     and the **Publish Directory** to `public` → *Deploy Static Site*.
4. When the deploy log says *Your site is live*, open the URL at the top of the service page. It looks like
   `https://accessible-agami.onrender.com`; Render adds a suffix if the name is taken.
5. From now on, every push to `main` redeploys automatically. Static sites are free and don't go to sleep.

**Notes for the web version**
- Browsers only allow sound after the first tap on a page. The opening login screen can't speak on its
  own, but everything after the first tap can.
- Amounts are read by the browser's own voice. That works in Chrome on Android with Google's Bengali voice
  installed, but may be silent on a desktop computer.
- Each browser keeps its own settings, tier and progress (stored in that browser only).
