"""Stand-in clips and the recording sheet for the audio added to Agami.

The words of every added clip live in one place: the CLIP_TEXT block in
agami.html (between the CLIP_TEXT:BEGIN / CLIP_TEXT:END markers). This
script reads them from there to:

  * make TTS stand-in MP3s in assets/audio (Microsoft neural voice,
    Bangladeshi Bengali by default), for any clip not recorded yet;
  * write AUDIO_SCRIPTS.md, the file-name + script sheet for recording.

The app's original clips (help_*, prompt_*, tile_*, ...) are not in
CLIP_TEXT, so this script never touches them. Existing files are never
overwritten unless you pass --force AND name the clips, so your own
recordings in assets/audio are safe.

    pip install edge-tts
    python tools/generate_audio.py                 # make any missing clips
    python tools/generate_audio.py --doc           # rewrite AUDIO_SCRIPTS.md
    python tools/generate_audio.py --force btn_logout nav_home   # remake these two
"""
import argparse
import asyncio
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
HTML = ROOT / "agami.html"
AUDIO_DIR = ROOT / "assets" / "audio"
DOC = ROOT / "AUDIO_SCRIPTS.md"
DEFAULT_VOICE = "bn-BD-NabanitaNeural"

# Recording-sheet layout: (section title, note, [(clip, where it plays)]).
GROUPS = [
    ("১২৩ tier: main menu (dashboard)",
     "Plays automatically when the ১২৩ dashboard opens, clip after clip; each number key glows while its line plays.",
     [("voice_menu_intro", "first"), ("voice_menu_1", "key ১ glows"), ("voice_menu_2", "key ২ glows"),
      ("voice_menu_3", "key ৩ glows"), ("voice_menu_4", "key ৪ glows"), ("voice_repeat", "key ০ glows"),
      ("voice_help_dashboard", "the ? button on the ১২৩ menu")]),
    ("১২৩ tier: account page (after pressing ১–৪)",
     "Intro, then the amounts and dates are read by the phone's own voice, then the closing line.",
     [("voice_info_loan", "after pressing ১"), ("voice_info_savings", "after pressing ২"),
      ("voice_info_special", "after pressing ৩"), ("voice_info_insurance", "after pressing ৪"),
      ("voice_info_nav", "closing line"), ("voice_help_info", "the ? button on this page")]),
    ("১২৩ tier: login",
     "Plays automatically on each login screen, and from its 🔊, when the saved tier is ১২৩.",
     [("voice_login_mobile", "mobile number screen"), ("voice_login_pin", "PIN screen")]),
    ("Tier-change dialog (promotion / demotion)",
     "Spoken when it opens in ১২৩ or নতুন (if auto-play is on); the offer to move to ১২৩ always speaks.",
     [("nudge_voice_promote", "১২৩ → next tier up"), ("nudge_voice_demote", "any tier → ১২৩"),
      ("nudge_promote", "নতুন → মাঝারি, মাঝারি → দক্ষ"), ("nudge_demote", "দক্ষ → মাঝারি, মাঝারি → নতুন"),
      ("nudge_trial_back", "soon after a move up that is going badly: go back?")]),
    ("First-run onboarding (choose your level)",
     "Plays automatically. The number said for মাঝারি / দক্ষ depends on whether নতুন is shown, so record both "
     "versions; the app picks the right one.",
     [("onboard_intro", "always first"), ("onboard_opt_voice", "option ১"),
      ("onboard_opt_novice", "option ২, only when নতুন is shown"),
      ("onboard_opt_intermediate_2", "নতুন hidden (মাঝারি = ২)"), ("onboard_opt_intermediate_3", "নতুন shown (মাঝারি = ৩)"),
      ("onboard_opt_expert_3", "নতুন hidden (দক্ষ = ৩)"), ("onboard_opt_expert_4", "নতুন shown (দক্ষ = ৪)"),
      ("onboard_repeat", "always last")]),
    ("Tap to hear, tap again to do (১২৩ and নতুন)",
     "In these two tiers there are no small 🔊 icons: the first tap on a button plays its clip from the "
     "\"Button speakers\" list below, and a second tap does it.",
     [("tap_again", "added after the button's clip, for a member's first few taps only")]),
    ("Button speakers",
     "In মাঝারি the small 🔊 on each button plays these; in ১২৩ and নতুন the first tap on the button does. "
     "Not used in দক্ষ. The four big cards on the নতুন dashboard reuse your original tile_* clips.",
     [("btn_loan_history", "Loan page: পরিশোধের ইতিহাস"),
      ("btn_outstanding_calc", "Loan page: বকেয়া হিসাব · Calculators: বকেয়া ক্যালকুলেটর"),
      ("btn_loan_apply_new", "Loan page: নতুন ঋণের আবেদন করুন"),
      ("btn_loan_apply_calc", "Loan calculator result: ঋণের আবেদন করুন"),
      ("btn_loan_apply_product", "Loan product page: ঋণের আবেদন করুন"),
      ("btn_gensavings_history", "Savings page: জমার ইতিহাস"),
      ("btn_savings_register", "Savings page: নতুন সঞ্চয় নিবন্ধন"),
      ("btn_dps_history", "Special savings page: পরিশোধের ইতিহাস"),
      ("btn_dps_register", "Special savings page: নতুন বিশেষ সঞ্চয় নিবন্ধন · DPS product page: সরাসরি আবেদন করুন"),
      ("btn_dps_apply_calc", "DPS calculator result: এই হিসাবে আবেদন করুন"),
      ("btn_insurance_more", "Insurance page: বীমার সুবিধা সম্পর্কে আরও জানুন"),
      ("btn_help_center", "Contact page: সাহায্য কেন্দ্র"),
      ("btn_calc_loan", "Calculators: ঋণ ক্যালকুলেটর · Loan product page: ঋণ ক্যালকুলেটর"),
      ("btn_calc_dps", "Calculators: ডিপিএস ক্যালকুলেটর · DPS product page: ডিপিএস ক্যালকুলেটর"),
      ("btn_product_dabi", "Products list: দাবি সাধারণ ঋণ"),
      ("btn_product_progoti", "Products list: প্রগতি ঋণ"),
      ("btn_product_projasha", "Products list: প্রত্যাশা ঋণ"),
      ("btn_product_special_savings", "Products list: বিশেষ সঞ্চয়ী হিসাব"),
      ("btn_product_loan_protection", "Products list: ঋণ সুরক্ষা বীমা"),
      ("prod_tab_loan", "Products tabs: ঋণ"), ("prod_tab_savings", "Products tabs: সঞ্চয়"),
      ("prod_tab_insurance", "Products tabs: বীমা"),
      ("btn_call_app_help", "Contact list: অ্যাপ ব্যবহারের সাহায্য"),
      ("btn_call_branch", "Contact list: ব্রাঞ্চ ম্যানেজার"),
      ("btn_call_po", "Contact list: প্রোগ্রাম অর্গানাইজার"),
      ("btn_call_center", "Contact list: কল সেন্টার"),
      ("btn_lang_bn", "Profile: বাংলা"), ("btn_lang_en", "Profile: English"),
      ("btn_logout", "Profile: লগআউট"), ("btn_see_more", "History lists: আরও দেখুন")]),
    ("Calculators: second step (১২৩ and নতুন)",
     "The 🔊 on the loan and DPS calculators once the amount is entered and the keypad gives way to the choices.",
     [("prompt_loan_tenure", "loan calculator, step 2"), ("prompt_dps_tenure", "DPS calculator, step 2")]),
    ("Outstanding balance: month buttons",
     "Replaces typing a date (দক্ষ keeps the date keypad and your original prompt_outstanding_date / "
     "help_outstanding_date clips).",
     [("prompt_outstanding_month", "the 🔊 on the month page"), ("help_outstanding_month", "the ? on the month page")]
     + [("month_%d" % m, "the button for month %d" % m) for m in range(1, 13)]),
    ("Bottom navigation bar",
     "The 🔊 on each item of the bar at the bottom of the dashboard.",
     [("nav_home", "হোম"), ("nav_contact", "যোগাযোগ"), ("nav_profile", "প্রোফাইল")]),
    ("Pop-up dialogs",
     "Each dialog's 🔊; also spoken when the dialog opens in ১২৩ / নতুন with auto-play on. In the two confirm "
     "dialogs the phone's own voice first reads the amount, then this clip plays.",
     [("dlg_logout", "Log out? dialog"),
      ("dlg_hold_confirm", "Confirm loan / savings application dialogs")]),
    ("Settings page",
     "The ? button and the 🔊 beside each setting.",
     [("help_accessibility_hub", "the ? button"), ("set_tier", "ব্যবহারের ধরন (mode buttons)"),
      ("set_show_novice", "\"নতুন\" মোড দেখান"), ("set_autoplay_voice", "\"১২৩\" মোডে (auto-play)"),
      ("set_autoplay_novice", "\"নতুন\" মোডে (auto-play)"), ("set_text_size", "লেখার আকার"),
      ("set_contrast", "উচ্চ কনট্রাস্ট"), ("set_haptic", "স্পর্শে কম্পন"),
      ("set_replay_onboarding", "শুরুর পরিচিতি আবার দেখুন")]),
    ("Help centre",
     "The ? button on the help centre (question list) page.",
     [("help_help_center", "the ? button")]),
]


def read_clip_text():
    html = HTML.read_text(encoding="utf-8")
    block = re.search(r"/\* CLIP_TEXT:BEGIN \*/(.*?)/\* CLIP_TEXT:END \*/", html, re.S)
    if not block:
        raise SystemExit("CLIP_TEXT:BEGIN / CLIP_TEXT:END markers not found in agami.html")
    clips = dict(re.findall(r"^\s*(\w+):\s*'([^']*)',?\s*$", block.group(1), re.M))
    grouped = [k for _, _, rows in GROUPS for k, _ in rows]
    missing = set(clips) - set(grouped)
    unknown = set(grouped) - set(clips)
    if missing or unknown:
        raise SystemExit(f"GROUPS out of sync with CLIP_TEXT. Not in GROUPS: {sorted(missing)}; "
                         f"not in CLIP_TEXT: {sorted(unknown)}")
    return clips


def write_doc(clips):
    lines = [
        "# Audio clips added to Agami: file names and scripts",
        "",
        f"There are {len(clips)} clips. Each file below is already in `assets/audio/` as a **stand-in** made with",
        "a Bangladeshi TTS voice (`bn-BD-NabanitaNeural`), so the app works now. Your original clips",
        "(`help_*`, `prompt_*`, `tile_*`, `loan_apply_success`) are not listed here and were not changed.",
        "",
        "**To use your own recording:** save it under the exact file name below into `assets/audio/`,",
        "replacing the stand-in. Nothing else needs to change. The Android build and Render pick it up.",
        "",
        "**Recording tips**",
        "- MP3, mono. 24 kHz / 48 kbps matches the existing clips; 44.1 kHz is fine too.",
        "- Trim silence at the start and end to under ~0.3 s: menus play clips back to back.",
        "- Keep loudness similar to the other clips (about −16 LUFS).",
        "- Say numbers as words, as written (\"এক\", \"দুই\", \"শূন্য\", \"নয়\").",
        "- \"টিক চিহ্ন\" / \"ক্রস চিহ্ন\" are the ✅ / ❌ shown on dialog buttons.",
        "",
        "**To change a script:** edit its line in the `CLIP_TEXT` block of `agami.html` (that text is also",
        "what the phone says if a file is missing), then run `python tools/generate_audio.py --doc` to",
        "refresh this sheet, and re-record, or run `python tools/generate_audio.py --force <name>`.",
        "",
        "*This file is generated by `tools/generate_audio.py --doc`.*",
    ]
    for title, note, rows in GROUPS:
        lines += ["", "---", "", f"## {title}", "", note, "", "| File name | Where | Script |", "|---|---|---|"]
        for key, where in rows:
            lines.append(f"| `{key}.mp3` | {where} | {clips[key]} |")
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {DOC.name}")


async def make_clips(clips, keys, voice, force):
    import edge_tts
    for key in keys:
        path = AUDIO_DIR / (key + ".mp3")
        if path.exists() and not force:
            print("skip  " + path.name + " (exists)")
            continue
        await edge_tts.Communicate(clips[key], voice).save(str(path))
        print("wrote " + path.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("keys", nargs="*", help="clip names (default: all clips in CLIP_TEXT)")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--force", action="store_true", help="overwrite the named clips even if they exist")
    parser.add_argument("--doc", action="store_true", help="only rewrite AUDIO_SCRIPTS.md")
    args = parser.parse_args()

    clips = read_clip_text()
    if args.doc:
        write_doc(clips)
        return
    unknown = [k for k in args.keys if k not in clips]
    if unknown:
        parser.error("not in CLIP_TEXT: " + ", ".join(unknown))
    if args.force and not args.keys:
        parser.error("--force needs clip names, so a slip can't overwrite every recording at once")
    asyncio.run(make_clips(clips, args.keys or list(clips), args.voice, args.force))


if __name__ == "__main__":
    main()
