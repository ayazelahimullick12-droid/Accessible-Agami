# Accessible Agami

An accessible, adaptive version of the Agami app for rural members in Bangladesh, including people who
cannot read. Live demo: **https://accessible-agami.onrender.com/**

One codebase, two ways to ship it:

| | What | Where |
|---|---|---|
| **The app** | `agami.html` + `assets/` (audio clips, icons) | repo root |
| **Android APK** | a WebView wrapper that bundles the app and gives it the phone's Bengali voice | `android/` |
| **Website** | the same files served as a static site | `render.yaml` |

Editing `agami.html` or replacing a clip in `assets/audio/` updates both: the Android build copies the files
in automatically, and Render redeploys from GitHub.

## What it does

- **Four ways to use it (tiers):** ১২৩ (a spoken, numbered menu for people who can't read), নতুন (guided, one
  thing at a time; hidden by default, switch it on in Settings), মাঝারি (the standard screens) and দক্ষ
  (everything at once).
- **It adapts, but the member decides.** The app scores how each task goes and offers to move a member up or
  down a tier. See *How the adaptation works* below.
- **Nothing scrolls.** Every screen and dialog fits the phone it is opened on; long pages are split into
  steps or pages.
- **Everything can be heard.** In ১২৩ and নতুন, the first tap on a button says what it does and a second tap
  does it. মাঝারি has a small 🔊 on each button. Pages, dialogs and tier offers speak for themselves in the
  two guided tiers, with a 🔊/🔇 switch in the top bar. Balances are never read out on their own: in ১২৩
  the account page says how to hear them, and they are spoken when a line is tapped or ০ is pressed, so
  people nearby don't hear them by default.
- **Amounts as pictures.** In ১২৩ and নতুন, sums are also drawn as taka notes, including while typing.
- **Pictures from village life.** Icons are drawn for the members the app is for: a hand with bangles
  receiving taka (ঋণ), a clay money bank (সঞ্চয়), a tin-roof house (হোম), a woman in a saree (প্রোফাইল), the
  passbook (ইতিহাস). They are SVGs in `assets/icons/`; see the note there to swap one for your own picture.
- **"Did BRAC get my money?"** A member who hands a payment to a field worker can check that BRAC recorded
  it, without reading:
  - Each account page and the dashboard lead with the latest payment: ✅ green when BRAC received it, ❌ red
    for a month with nothing received. In ১২৩ it is the first line of the account page.
  - Every history row says whether BRAC received it, and each history page has a "paid, but not here?"
    button that gives BRAC's own call-centre number, not the field worker's.
  - The number is `CONFIG.hotline` in `agami.html`. Set `CONFIG.hotlineTel` to make the button dial it.
- **Each member has their own settings**, kept under the mobile number they log in with, because phones are
  shared.

## How the adaptation works

- **What is measured:** everyday tasks (opening an account or history page and using it: paging through its
  details, hearing a line, opening its history; using a calculator) and the rarer applications, which count
  double. A page only looked at counts neither way. ১২৩ is measured on its own menu: picking a number
  without asking for help (no ০ or ? first).
- **No clock.** Time on task is never used to judge skill, as the AUI guide requires: in the field a slow
  task usually means an interruption, not a lack of skill. Only actions count.
- **Signs of difficulty:** two taps on **?**, abandoning a task, three keypad corrections, going round in a
  loop (re-opening a page that was left without being used), replaying the same button's audio, and three
  taps on things that aren't buttons.
- **The rule:** of the last 10 results in a tier, 8 clean ones spread over 3 different days offer the next
  tier up; 6 rough ones offer the tier below.
- **The offer** only appears on the dashboard or a success page. Declining rests it for 3 tasks (10 when it
  involves ১২৩). After moving up, the next 3 tasks are a trial: two rough ones bring an immediate "go back?".

## Research panel and running a demo

Open **Settings (⚙) and tap the title 7 times.** The panel (in English) shows the current member's score and
lets you:

- **Change the rules.** *Demo rules* make an offer appear after 4 results on the same day, which is what you
  want on stage; *Study rules* restore 8 of 10 over 3 days.
- **Switch the note pictures off** to compare with and without.
- **Export the log as CSV** (every task result, offer, answer, tier and setting change, with a timestamp;
  members appear as the last four digits of their number), clear it, or **reset the current member** so they
  start again from "choose your level".

To show a tier offer live: choose *Demo rules*, go to the dashboard in মাঝারি, then open an account page,
tap its › arrow (or a 🔊), and go back. After the fourth time the offer appears.

**For a QR code:** a link ending in `?rules=demo`
(`https://accessible-agami.onrender.com/?rules=demo`) puts whoever opens it on the demo rules without
touching the panel, so an audience sees the offers too. The plain link keeps the study rules.

Any mobile number and any 4-digit PIN log in; each new number is a new member and starts at "choose your
level".

## Audio

- `assets/audio/` holds every clip. The app's original clips are unchanged. The clips added since are TTS
  stand-ins in a Bangladeshi voice.
- **[AUDIO_SCRIPTS.md](AUDIO_SCRIPTS.md)** lists each added clip's file name, where it plays and its script.
  To use your own recording, save it under the same file name in `assets/audio/`.
- The scripts live in the `CLIP_TEXT` block of `agami.html`. `tools/generate_audio.py` reads them to make
  missing stand-ins (`python tools/generate_audio.py`, after `pip install edge-tts`) and to refresh the sheet
  (`--doc`). It never overwrites an existing file unless you pass `--force` with clip names.
- Amounts, dates and names are read by the phone's own Bengali voice, so they need one installed (see the
  notes under each platform).

---

## Host the website (Render)

The site is set up from `render.yaml` (a Blueprint): a static site whose build step publishes only the app
itself, with `agami.html` as the home page.

- **After every push to GitHub, redeploy:** in the Render dashboard open the service → *Manual Deploy →
  Deploy latest commit* (or suspend and resume it). If *Auto-Deploy* is on, this happens by itself.
- **First-time setup:** render.com → *New → Blueprint* → choose this repository → *Deploy Blueprint*.
  Without a Blueprint: *New → Static Site*, build command
  `rm -rf public && mkdir -p public && cp -r assets public/ && cp agami.html public/index.html && cp agami.html public/agami.html`,
  publish directory `public`.

**Notes for the web version**
- Browsers only allow sound after the first tap on a page, so the opening login screen can't speak by
  itself; everything after the first tap can.
- Amounts are read by the browser's own voice. That works in Chrome on Android with Google's Bengali voice
  installed and may be silent on phones without a Bengali voice. Recorded clips play everywhere.
- Each browser keeps its own members, settings and log.
- On a laptop or projector the app stays a phone-width column in the middle of the window.

## Build the Android app (Android Studio)

The project uses AGP 9.3 and Gradle 9.6, which Android Studio **2026.1.2 (Quail 2) or newer** opens. It was
built successfully from the command line with the JDK that ships with Android Studio Quail 4 (2026.1.4).

1. **Get the code.** Use this folder, or clone it:
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
- **Sharing:** `window.AndroidApp.shareText` sends the research log to the phone's share sheet, since a
  WebView can't save files.
- **Phone behaviour:** keeps the page clear of the status and navigation bars, and silences audio when the
  app goes to the background (for example during a phone call).
