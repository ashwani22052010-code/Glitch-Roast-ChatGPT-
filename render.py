#!/usr/bin/env python3
"""4-AI Cinematic Engine (ChatGPT / Gemini / Grok / Claude, Battle mode)  ->  MP4 (720p .. 4K, 30/60 fps)
Intro, end screen, memes, apni sounds, background music, voice (edge-tts) - sab GitHub Actions par.

Usage:  python3 render.py scripts/video1.txt --out out
"""
import argparse, json, math, multiprocessing, os, re, subprocess, sys, tempfile, time, wave
from pathlib import Path

BRAND = "Glitch Roast"               # intro me ye naam dikhega
INTRO_S = 2.8                        # intro kitne second ka
W, H = 1920, 1080                    # output ka "1080p" size (9:16 me 1080x1920) - settings() isko set karta hai
VW, VH = 608, 342                    # browser me tool ka CSS size (chhota = sab bada dikhega); 16:9 = phone preview jaisa
HERE = Path(__file__).resolve().parent
SR = 44100

# ----------------------------------------------------------------- numpy (khud install ho jaata hai)
try:
    import numpy as np
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "numpy"])
    import numpy as np

# ----------------------------------------------------------------- page helpers
INIT_JS = """
(() => {
  window.AudioContext = window.webkitAudioContext = undefined;
  let sd = 1234567;                       // fixed seed: har baar aur har worker me same timeline
  Math.random = () => { sd |= 0; sd = sd + 0x6D2B79F5 | 0; let t = Math.imul(sd ^ sd >>> 15, 1 | sd);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  window.__clicks = []; window.__done = false;
  window.__sync = (T, step) => {
    for (const a of document.getAnimations()) {
      if (a.__s === undefined) { a.__s = T - step / 2; a.pause(); }
      const t = T - a.__s, e = a.effect && a.effect.getComputedTiming().endTime;
      if (isFinite(e) && t >= e) { a.finish(); continue; }
      a.currentTime = t;
    }
    return window.__hold || 0;
  };
  window.__hold = 0;
})();
"""

PAGE_CSS = """
.panel,.panel-trigger,.fullscreen-overlay{display:none!important}
html,body{background:#000!important}
.chat-area{scroll-behavior:auto!important}
.app-container.light-mode.gemini-active,.app-container.light-mode.grok-active,.app-container.light-mode.claude-active{--app-bg:#ffffff}
body.ratio-9-16 #ov .ove{transform:scale(1.45)}
#customTopbarImg[src=""],#geminiTopbarImg[src=""],#grokTopbarImg[src=""],#claudeTopbarImg[src=""],#customSuggImg[src=""]{visibility:hidden!important}
@font-face{font-family:EMO;src:local("Noto Color Emoji");unicode-range:U+1F000-1FFFF,U+2190-21FF,U+2300-23FF,U+2600-27BF,U+2B00-2BFF,U+FE0F,U+200D}
.app-container,.app-container *{font-family:%s!important}
"""

LAUNCH_ARGS = ["--force-color-profile=srgb", "--font-render-hinting=none", "--hide-scrollbars"]
if hasattr(os, "geteuid") and os.geteuid() == 0: LAUNCH_ARGS.append("--no-sandbox")

OVERLAY_CSS = """
#ov{position:absolute;inset:0;pointer-events:none;z-index:500}
.ovi,.ovc{position:absolute;inset:0;background:#000;display:none;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 5vw}
.ovi{background:#05070a}
.ovi.on{display:flex;animation:ovBg var(--d) linear both}
.ovc.on{display:flex}
.ovi .t,.ovc .ct{position:relative;font-weight:800;line-height:1.12;color:#fff;letter-spacing:.01em;
 text-shadow:-.28vw 0 #00f0ff,.28vw 0 #ff2a6d;animation:ovPop .5s cubic-bezier(.2,1.3,.4,1) both,ovGl .6s steps(1) both}
.ovi .s,.ovc .cs{margin-top:2vw;color:#cfd3d8;font-weight:600;animation:ovFade .5s ease-out .45s both}
.ovi .b{margin-top:3vw;height:.55vw;width:34vw;background:linear-gradient(90deg,#00f0ff,#ff2a6d);animation:ovBar .8s ease-out .3s both}
.ove{position:absolute;inset:0;background:rgba(0,0,0,.8);display:none;flex-direction:column;align-items:center;justify-content:center;gap:3vw;text-align:center}
.ove.on{display:flex;animation:ovFade .5s ease-out both}
.ove .t{font-size:5.4vw;font-weight:800;color:#fff;animation:ovPop .6s cubic-bezier(.2,1.4,.4,1) .15s both}
.ove .s{margin-top:-1.6vw;font-size:2.4vw;color:#cfd3d8;animation:ovFade .5s ease-out .5s both}
.ove .row{display:flex;align-items:center;gap:2.2vw;animation:ovSlide .6s cubic-bezier(.2,1.2,.4,1) .55s both}
.ove .bw{position:relative;width:21vw;height:5.8vw}
.ove .btn{position:absolute;inset:0;border-radius:2.9vw;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:2.4vw;letter-spacing:.08em;color:#fff}
.ove .sub{background:#f00;animation:ovSubOut .3s ease-in 1.5s both}
.ove .done{background:#2b2b2b;opacity:0;animation:ovDoneIn .3s ease-out 1.6s both}
.ove .bell{width:5.2vw;height:5.2vw;opacity:0;animation:ovFade .3s ease-out 1.8s both}
.ove .bell svg{width:100%;height:100%;stroke:#fff;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;transform-origin:50% 8%;animation:ovRing 1.2s ease-in-out 2.1s both}
@keyframes ovBg{0%{opacity:0}5%{opacity:1}90%{opacity:1}100%{opacity:0}}
@keyframes ovPop{0%{opacity:0;transform:scale(.88)}100%{opacity:1;transform:scale(1)}}
@keyframes ovFade{0%{opacity:0}100%{opacity:1}}
@keyframes ovBar{0%{width:0}100%{width:34vw}}
@keyframes ovGl{0%{transform:translate(-1vw,0)}12%{transform:translate(1.1vw,.2vw)}24%{transform:translate(-.6vw,-.2vw)}36%{transform:translate(.7vw,0)}48%{transform:translate(-.25vw,0)}60%,100%{transform:translate(0,0)}}
@keyframes ovSlide{0%{opacity:0;transform:translateY(2.5vw)}100%{opacity:1;transform:translateY(0)}}
@keyframes ovSubOut{0%{transform:scale(1);opacity:1}40%{transform:scale(.9);opacity:1}100%{transform:scale(.9);opacity:0}}
@keyframes ovDoneIn{0%{opacity:0;transform:scale(.9)}100%{opacity:1;transform:scale(1)}}
@keyframes ovRing{0%{transform:rotate(0)}15%{transform:rotate(18deg)}30%{transform:rotate(-16deg)}45%{transform:rotate(12deg)}60%{transform:rotate(-8deg)}75%{transform:rotate(4deg)}100%{transform:rotate(0)}}
"""

DRIVER_JS = r"""
async ([items, o, ui]) => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const now = () => performance.now();
  // tool ki apni awaaz band - awaaz Python banata hai (events se)
  window.startTypingSound = window.stopTypingSound = window.playSendSound = window.playPing = () => {};
  const E = window.__ev = [], VS = window.__vstarts = {}, TY = window.__typing = [];
  window.click = () => window.__clicks.push(now());

  // ---- tool settings
  if (o.ratio === '9:16' || o.ratio === '16:9') setRatio(o.ratio); else setRatio('full');
  if (o.light && !isLightMode) toggleTheme();
  if (o.accent) setAccentColor(o.accent, null);
  typingSpeed = o.typing || 1; spd = o.speed || 1;
  humanModeEnabled = !!o.human; laptopModeEnabled = !!o.laptop; autoPauseEnabled = false;
  userImages.length = 0; aiImages.length = 0;
  (ui.user || []).forEach((u, i) => { userImages[i] = u; });
  (ui.ai || []).forEach((u, i) => { aiImages[i] = u; });
  for (const [k, v] of Object.entries(ui.saved || {})) savedImages[k] = v;
  isFirstType = true; applyPermanentUI(); updateImageAdjustments();
  const srcs = [...(ui.user || []), ...(ui.ai || []), ...Object.values(ui.saved || {})].filter(Boolean);
  await Promise.all(srcs.map(src => new Promise(r => { const im = new Image(); im.onload = im.onerror = () => r(); im.src = src; })));

  // ---- smooth scroll, lekin clock ke hisaab se (har render me bilkul same)
  const ca = document.getElementById('chatArea'), app = document.getElementById('appContainer');
  const SD = Object.getOwnPropertyDescriptor(Element.prototype, 'scrollTop');
  let sFrom = 0, sTo = 0, sT0 = 0, sOn = false;
  const sStep = () => {
    const p = Math.min(1, (now() - sT0) / 320), e = 1 - Math.pow(1 - p, 3);
    const max = Math.max(0, ca.scrollHeight - ca.clientHeight);
    SD.set.call(ca, sFrom + (Math.min(sTo, max) - sFrom) * e);
    if (p < 1) setTimeout(sStep, 16); else sOn = false;
  };
  Object.defineProperty(ca, 'scrollTop', { configurable: true, get() { return SD.get.call(ca); },
    set(v) { sFrom = SD.get.call(ca); sTo = v; sT0 = now(); if (!sOn) { sOn = true; setTimeout(sStep, 16); } } });

  // ---- overlay: intro / caption / end screen
  const ov = document.createElement('div'); ov.id = 'ov'; app.appendChild(ov);
  const esc2 = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const split = t => { const p = String(t).split('|'); return [p[0].trim(), (p.slice(1).join('|') || '').trim()]; };
  const BELL = '<svg viewBox="0 0 24 24"><path d="M6 17V11a6 6 0 0 1 12 0v6l1.5 2h-15z"/><path d="M10 21a2 2 0 0 0 4 0"/></svg>';
  const fitTxt = (el, maxF, minF, targetW, wrapW) => {
    const cq = app.clientWidth / 100;
    el.style.display = 'inline-block'; el.style.whiteSpace = 'nowrap'; el.style.maxWidth = ''; el.style.fontSize = maxF + 'vw';
    const w = el.scrollWidth / cq; let f = maxF * Math.min(1, targetW / w);
    if (f < minF) { f = minF; el.style.whiteSpace = 'normal'; el.style.maxWidth = wrapW + 'vw'; }
    el.style.fontSize = f + 'vw'; return f;
  };
  const card = (cls, a, b, d, big) => {
    const e = document.createElement('div'); e.className = cls; e.style.setProperty('--d', d + 's');
    const t1 = cls === 'ovi' ? 't' : 'ct', t2 = cls === 'ovi' ? 's' : 'cs';
    e.innerHTML = '<div class="' + t1 + '">' + esc2(a) + '</div>' + (cls === 'ovi' ? '<div class="b"></div>' : '') + (b ? '<div class="' + t2 + '">' + esc2(b) + '</div>' : '');
    ov.appendChild(e); e.classList.add('on');
    const f = fitTxt(e.querySelector('.' + t1), big, 5.6, 90, 90);
    const sub = e.querySelector('.' + t2); if (sub) fitTxt(sub, Math.max(2.6, Math.min(5.4, f * 0.42)), 2.4, 88, 88);
    return e;
  };
  const cmd = async m => {
    const [a, b] = split(m.t); E.push({n: 'cmd', c: m.cmd, t: now()});
    if (m.cmd === 'intro') { const d = m.dur || 3.2, e = card('ovi', a, b, d, 14); await sleep(d * 1000); e.remove(); }
    else if (m.cmd === 'caption' || m.cmd === 'level') { const d = m.dur || 3, e = card('ovc', a, b, d, 18); await sleep(d * 1000); e.remove(); }
    else if (m.cmd === 'end') {
      const e = document.createElement('div'); e.className = 'ove';
      e.innerHTML = '<div class="t">' + esc2(a || 'Thanks for watching!') + '</div>' + (b ? '<div class="s">' + esc2(b) + '</div>' : '') +
        '<div class="row"><div class="bw"><div class="btn sub">SUBSCRIBE</div><div class="btn done">SUBSCRIBED</div></div><div class="bell">' + BELL + '</div></div>';
      ov.appendChild(e); e.classList.add('on'); await sleep(5000); e.remove();
    }
  };
  window.memeHold = async function (n) {
    window.__holdT = now(); window.__hold = n;
    await new Promise(r => { window.__release = () => { window.__hold = 0; r(); }; });
  };

  // ---- typing (tool ke typeInInputBox jaisa, bas har akshar par click record hota hai)
  const CUR = '<span style="border-right: 2px solid var(--text-primary); margin-left: 1px;"></span>';
  const typeIt = async (text, perChar) => {
    removeSuggestions();
    const inp = document.getElementById('chatInput'); inp.innerHTML = ''; autoResize(inp); updateButtonsState();
    const arr = Array.from(text || ''); let i = 0, html = ''; const span = [now(), null]; TY.push(span);
    await sleep(50);
    while (i < arr.length) {
      let delay = perChar ? perChar * (0.7 + Math.random() * 0.6) : 30 / typingSpeed;
      if (humanModeEnabled && !perChar) { delay += (Math.random() * 40) / typingSpeed; if (Math.random() < 0.04) delay += (250 + Math.random() * 250) / typingSpeed; }
      if (laptopModeEnabled && !perChar && Math.random() < 0.02 && i > 1 && arr[i] !== ' ' && arr[i - 1] !== ' ' && adjKeys[arr[i].toLowerCase()]) {
        const wrong = getTypoChar(arr[i]); click();
        inp.innerHTML = html + '<span style="text-decoration-line: underline; text-decoration-style: wavy; text-decoration-color: red; text-underline-offset: 3px; color: var(--text-primary);">' + esc(wrong) + '</span>' + CUR;
        autoResize(inp); updateButtonsState(); await sleep(350 / typingSpeed);
        inp.innerHTML = html + CUR; click(); await sleep(100 / typingSpeed); await sleep(delay * 2); continue;
      }
      const ch = arr[i++]; html += esc(ch); inp.innerHTML = html + CUR; autoResize(inp); updateButtonsState();
      if (ch.trim()) click();
      await sleep(delay);
    }
    inp.innerHTML = html; autoResize(inp); updateButtonsState(); span[1] = now();
  };
  const think = role => role === 'gemini' ? getGeminiBThink() : role === 'grok' ? getGrokBThink() : role === 'claude' ? getClaudeBThink() : getGptBThink();
  const holdFor = async (ms, vd) => { await sleep(Math.max(ms, vd ? vd * 1000 + 350 : 0)); };

  window.__play = async function () {
    ca.querySelectorAll('.user-row, .ai-block, .think-wrap').forEach(el => el.remove()); clearInp();
    switchAITheme('chatgpt'); app.classList.remove('battle-mode'); isFirstType = true; applyPermanentUI();
    const MM = window.__memes || {}, VD = window.__vdur || {};
    await sleep(o.start == null ? 2000 : o.start);
    const msgs = items.filter(x => x.role !== 'cmd');
    for (let i = 0; i < items.length; i++) {
      const it = items[i];
      if (it.role === 'cmd') { await cmd(it); continue; }
      const k = it.k, j = msgs.indexOf(it), nx = msgs[j + 1], pv = msgs[j - 1];
      const r = extractImage(it.raw, it.role === 'user'), txt = r.cleanText, img = r.image, vd = VD[k] || 0, meme = MM[k] || 0;
      if (it.phase === 2) {
        E.push({n: 'think', k, role: it.role, t: now(), first: !(pv && pv.phase === 2)});
        app.classList.add('battle-mode'); ca.innerHTML = ''; switchAITheme(it.role); showThink(it.role);
        await sleep(d(think(it.role)));
        ca.innerHTML = ''; addAIMsg(txt || '', img, it.role); VS[k] = now(); E.push({n: 'show', k, role: it.role, t: now()});
        await holdFor(d(it.role !== 'chatgpt' ? getDG() : getDA()) + 1500, vd);
        if (meme) await window.memeHold(meme);
      } else if (it.role === 'user') {
        switchAITheme('chatgpt'); app.classList.remove('battle-mode'); if (img) showInputImage(img);
        VS[k] = now() + 50;
        const n = Array.from(txt || '').length;
        await typeIt(txt, vd && n ? Math.max(12, Math.min(400, vd * 1000 / (n + 1))) : 0);
        await sleep((getSendDelay() * 1000) / spd);
        if (meme) await window.memeHold(meme);
        const inp = document.getElementById('chatInput'), fin = inp.innerText.trim(), fimg = inputImageData;
        E.push({n: 'send', k, role: 'user', t: now()});
        addUserMsgToChat(fin || null, fimg, true); clearInp();
        if (nx && nx.phase === 1 && nx.role !== 'user') { switchAITheme(nx.role); showThink(nx.role); }
        else if (nx && nx.phase === 2) hideThink();
        await sleep(d(getDU()));
      } else {
        app.classList.remove('battle-mode');
        if (!pv || pv.role === 'user' || pv.phase !== 1) { switchAITheme(it.role); showThink(it.role); }
        await sleep(d(800 + Math.random() * 400));
        addAIMsg(txt || '', img, it.role); VS[k] = now(); E.push({n: 'show', k, role: it.role, t: now()});
        if (nx && nx.phase === 1 && nx.role !== 'user') { switchAITheme(nx.role); showThink(nx.role); }
        await holdFor(d(it.role !== 'chatgpt' ? getDG() : getDA()), vd);
        if (meme) await window.memeHold(meme);
      }
    }
    await sleep(600);
    if (o.end && !items.some(m => m.role === 'cmd' && m.cmd === 'end')) await cmd({cmd: 'end', t: (o.endText || 'Thanks for watching!') + '|' + (o.brand || '')});
  };
  function getSendDelay() { const e = document.getElementById('dSend'); return e ? (parseFloat(e.value) || 0) : 1.0; }
}
"""

OPT_RE = re.compile(r"^\s*#\s*(typing|speed|human|laptop|light|accent|ratio|view|ui|music|sfx|sfx_auto|click|keys|intro|shorts|auto|end|bgm|bgm_start|bgm_vol|quality|fps|intro_len|end_len|intro_vol|end_vol|meme_vol|"
                    r"gpt_delay|opp_delay|user_delay|send_delay|chat_size|think_gpt|think_gemini|think_grok|think_claude|start_delay|"
                    r"voice|voice_emotion|voice_user|voice_ai|voice_gemini|voice_grok|voice_claude|voice_user_rate|voice_user_pitch|voice_ai_rate|voice_ai_pitch|voice_vol)\s*=\s*(\S+)\s*$", re.I)
TEXT_OPT_RE = re.compile(r"^\s*#\s*(intro_text|end_text|end_sub)\s*=\s*(.+?)\s*$", re.I)
MSG_RE = re.compile(r"^\s*(user|you|chatgpt|gpt|ai|assistant|gemini|grok|claude)\s*:\s*(.*)$", re.I)
ROLE_OF = {"user": "user", "you": "user", "chatgpt": "chatgpt", "gpt": "chatgpt", "ai": "chatgpt", "assistant": "chatgpt",
           "gemini": "gemini", "grok": "grok", "claude": "claude"}
BATTLE_RE = re.compile(r"^\W*(battle|phase\s*2)\b.*$", re.I)
CMD_RE = re.compile(r"^\s*!(\w+)(?:\s+(\d+(?:\.\d+)?))?\s*:?\s*(.*)$")

# ----------------------------------------------------------------- APNI SOUND FILES (sounds/ folder)
# Repo me "sounds" folder banao aur usme mp3/wav daalo. File ka naam = sound ka naam.
#   send.mp3 / recv.mp3 / funny.wav / scary.mp3 / hit.wav ...  -> built-in awaaz ki jagah ye file bajegi
#   vine_boom.mp3 (koi naya naam)                                -> script me message ke end me {vine_boom} likho
SFX_DIR = HERE / "sounds"
SFX_EXT = (".wav", ".mp3", ".ogg", ".m4a", ".flac", ".aac")
SFX_MAX_S = 8          # isse lambi file kaat di jaayegi
SFX_PEAK = 0.6         # har file ki awaaz is level par barabar ki jaati hai

def _scan_sounds():
    found = {}
    if SFX_DIR.is_dir():
        for f in sorted(SFX_DIR.iterdir()):
            if f.suffix.lower() in SFX_EXT:
                nm = re.sub(r"[^a-z0-9_-]", "", f.stem.lower().replace(" ", "_"))
                if nm: found.setdefault(nm, f)
    return found
CUSTOM_SFX = _scan_sounds()

# ----------------------------------------------------------------- MEDIA: memes / intro video / end video / bgm
# Dashboard se upload hone par ye folders bante hain (bade video 3 MB ke tukdo me aate hain: file.mp4.p000, .p001 ...)
#   memes/1.mp4, memes/2.mp4 ...   -> script me message ke end me [1] [2]
#   media/intro.mp4, media/end.mp4 -> intro / end screen ki jagah video
#   music/bgm.mp3                  -> apna background music (loop)
MEME_DIR, MEDIA_DIR, MUSIC_DIR = HERE / "memes", HERE / "media", HERE / "music"
UI_DIR, UIMG_DIR, AIMG_DIR = HERE / "ui", HERE / "images" / "user", HERE / "images" / "ai"
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif")
UI_KEYS = ["cgpt_tb_img", "cgpt_ft_img", "cgpt_sg_img", "gemini_tb_img", "gemini_ft_img", "grok_tb_img", "grok_ft_img", "claude_tb_img", "claude_ft_img"]
VID_EXT = (".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi")
_PART_RE = re.compile(r"^(.*?)(\.[a-z0-9]+)(?:\.p(\d{3}))?$")

def scan_media(folder, exts):
    out = {}
    d = Path(folder)
    if not d.is_dir(): return out
    for f in sorted(d.iterdir()):
        m = _PART_RE.match(f.name.lower())
        if not m or m.group(2) not in exts or not f.is_file(): continue
        out.setdefault(m.group(1), {}).setdefault(m.group(2), []).append(f)
    return out

def materialize(paths):
    """ek file ya uske tukde -> ek asli file ka path"""
    if len(paths) == 1 and not re.search(r"\.p\d{3}$", paths[0].name.lower()): return paths[0]
    base = re.sub(r"\.p\d{3}$", "", paths[0].name)
    tmp = Path(tempfile.gettempdir()) / "rt_media"; tmp.mkdir(exist_ok=True)
    size = sum(p.stat().st_size for p in paths)
    dst = tmp / f"{size}_{base}"
    if not dst.exists() or dst.stat().st_size != size:
        part = tmp / f".{os.getpid()}_{size}_{base}"
        with open(part, "wb") as o:
            for p in paths: o.write(p.read_bytes())
        os.replace(part, dst)
    return dst

def find_media(folder, stem, exts):
    got = scan_media(folder, exts).get(str(stem).lower())
    if not got: return None
    return materialize(next(iter(got.values())))

def _scan_memes():
    out = {}
    for stem, v in scan_media(MEME_DIR, VID_EXT).items():
        if stem.isdigit(): out[int(stem)] = next(iter(v.values()))
    return out
MEME_FILES = _scan_memes()
MEME_END_RE = re.compile(r"\s*\[\s*m(?:eme)?\s*(\d{1,3})\s*\]", re.I)   # [m1] message me kahin bhi

def meme_path(n):
    return materialize(MEME_FILES[int(n)])

_dur_cache = {}
def media_duration(path):
    path = str(path)
    if path not in _dur_cache:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path], capture_output=True, text=True)
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr)
        d = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0
        if d <= 0:      # browser se bani webm me duration likhi nahi hoti -> poora padhkar naapo
            r2 = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-map", "0:v:0?", "-f", "null", "-"], capture_output=True, text=True)
            ts = re.findall(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)", r2.stderr)
            if ts: d = int(ts[-1][0]) * 3600 + int(ts[-1][1]) * 60 + float(ts[-1][2])
        _dur_cache[path] = d
    return _dur_cache[path]

def clip_frames(path, fps, cap=None):
    d = media_duration(path)
    if cap: d = min(d, float(cap)) if d else float(cap)
    return max(1, int(round(d * fps)))

def out_size(dsf=None):
    return W // 2 * 2, H // 2 * 2

def video_frames(path, fps, j0, j1, size):
    """clip ke frame j0..j1-1 (fps par, aakhri frame clone) -> JPEG bytes, bilkul chat frames jaise rang ke saath"""
    w, h = size
    vf = (f"fps={fps},tpad=stop_mode=clone:stop_duration=3,trim=start_frame={j0}:end_frame={j1},setpts=PTS-STARTPTS,"
          f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
          f"format=rgb24,scale=out_color_matrix=bt601:out_range=full,format=yuvj420p")
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", str(path), "-vf", vf, "-an", "-sn", "-r", str(fps),
                          "-f", "image2pipe", "-c:v", "mjpeg", "-q:v", "2", "-"], stdout=subprocess.PIPE)
    buf, n = b"", 0
    try:
        while True:
            chunk = p.stdout.read(1 << 20)
            if not chunk: break
            buf += chunk
            while True:
                i = buf.find(b"\xff\xd9")
                if i < 0: break
                yield buf[:i + 2]; n += 1; buf = buf[i + 2:]
    finally:
        p.stdout.close(); p.wait()
    if n != j1 - j0:
        print(f"(dhyan: {Path(path).name} se {n} frame mile, {j1 - j0} chahiye the)", flush=True)

def clip_audio(path, seconds):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-vn", "-t", f"{seconds:.3f}",
                          "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype="<f4").astype(float)

MOODS = ["calm", "funny", "scary", "sad", "mystery", "hype", "surprise", "angry"]
MUSIC_OF = {"calm": "calm", "funny": "funny", "scary": "scary", "sad": "sad",
            "mystery": "mystery", "hype": "hype", "surprise": "hype", "angry": "scary"}

AUTO = [
    ("funny", "😂🤣😆😹💀🤭", r"\b(lol+|lmf?ao+|rofl|(?:a?ha){2,}h?)\b"),
    ("scary", "😱😨😰👻🩸🔪🕷", r"\b(scary|ghost|haunted|creepy)\b"),
    ("sad", "😢😭💔😞😔🥺", r"\b(sad|crying|miss you)\b"),
    ("mystery", "🤔🧐🕵🔍", r"\b(secret|mystery|suspicious)\b"),
    ("hype", "🔥🎉🚀💪🥳🤩🏆", r"\b(let'?s go|amazing|epic)\b"),
    ("surprise", "😲😮🤯😳", r"\bno way\b|\bwhat\?!"),
    ("angry", "😡🤬😠👿", r"\b(angry|hate|stupid|idiot)\b"),
]

MOJI = re.compile("[\u00c2-\u00f4][\u0080-\u00bf\u0152\u0153\u0160\u0161\u0178\u017d\u017e\u0192\u02c6\u02dc\u2013-\u203a\u20ac\u2122]")

def fix_mojibake(line):
    if not MOJI.search(line):
        return line
    try:
        raw = bytearray()
        for ch in line:
            try:
                raw += ch.encode("cp1252")
            except UnicodeEncodeError:
                raw += ch.encode("latin-1")
        return raw.decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return line

def auto_mood(text):
    for mood, emojis, rx in AUTO:
        if any(e in text for e in emojis) or re.search(rx, text, re.I):
            return mood
    return None

def parse_script(path):
    """script -> (items, opts, moods, memes, {k:(role, voice text)})
    items: [{k, role, raw, phase}] ya {role:'cmd', cmd, dur, t}"""
    opts, items, tags, texts, memes, phase, vemo = {}, [], {}, {}, {}, 1, {}
    skip_user, stags = False, {}
    k = -1
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = fix_mojibake(line).rstrip()
        m = TEXT_OPT_RE.match(line)
        if m: opts[m.group(1).lower()] = m.group(2); continue
        m = OPT_RE.match(line)
        if m: opts[m.group(1).lower()] = m.group(2); continue
        if not line.strip(): continue
        mr = MSG_RE.match(line)
        if not mr and BATTLE_RE.match(line):
            phase = 2; continue
        mc = CMD_RE.match(line) if not mr else None
        if mc:
            items.append(dict(role="cmd", cmd=mc.group(1).lower(), dur=float(mc.group(2)) if mc.group(2) else None, t=mc.group(3).strip()))
            continue
        if mr and phase == 2 and ROLE_OF[mr.group(1).lower()] == "user":
            print(f"(Battle me User ka message nahi hota - skip: {line.strip()[:50]})"); skip_user = True; continue
        if mr: skip_user = False
        elif skip_user: continue
        if mr:
            k += 1; body = mr.group(2)
            items.append(dict(k=k, role=ROLE_OF[mr.group(1).lower()], raw="", phase=phase))
        elif k < 0 or line.lstrip().startswith("#"):
            continue
        else:
            body = line.strip()
        mv = list(VOICE_TAG_RE.finditer(body))
        if mv: vemo[k] = mv[-1].group(1).lower(); body = VOICE_TAG_RE.sub("", body)
        for f in (x.lower() for x in TAG_RE.findall(body)):
            stags.setdefault(k, []).append(f)
            if f in MOODS: tags[k] = f
        body = TAG_RE.sub("", body).rstrip()
        mm = list(MEME_END_RE.finditer(body))
        if mm:
            body = MEME_END_RE.sub("", body).strip()
            n = int(mm[-1].group(1))
            if n in MEME_FILES: memes[k] = n
            else: print(f"(meme [m{n}] memes/ folder me nahi mila - skip)")
        it = items[-1] if items and items[-1].get("k") == k else None
        if it is None: continue
        it["raw"] = (it["raw"] + ("\n" if it["raw"] else "") + body.strip()).strip()
        texts[k] = texts.get(k, "") + " " + body
    moods = dict(tags)
    if opts.get("auto", "on").lower() not in ("off", "no", "0", "false"):
        for i, t in texts.items():
            if i not in moods:
                g = auto_mood(t)
                if g: moods[i] = g
    vraw = {it["k"]: (it["role"], re.sub(r"\[\s*\d+\s*\]", " ", it["raw"])) for it in items if it.get("k") is not None}
    return items, opts, moods, memes, vraw, vemo, stags

def find_html(name):
    for p in (HERE / name, HERE / "tool.html"):
        if p.exists(): return p
    for c in sorted(HERE.glob("*.[hH][tT][mM][lL]")):
        if "typeInInputBox" in c.read_text(encoding="utf-8", errors="ignore"): return c
    sys.exit(f"tool ki html (tool.html) repo me nahi mili. Repo me ye files hain: {[x.name for x in HERE.iterdir()]}")

def tt(d): return np.arange(int(d * SR)) / SR
def midi(n): return 440.0 * 2 ** ((n - 69) / 12)

def tone(f, d, decay=4.0, harm=(1,), amps=None, attack=0.004, tremolo=0.0):
    t = tt(d)
    amps = amps or [1.0 / h for h in harm]
    x = sum(a * np.sin(2 * np.pi * f * h * t) for h, a in zip(harm, amps))
    x = x * np.minimum(1, t / attack) * np.exp(-decay * t)
    if tremolo:
        x = x * (0.75 + 0.25 * np.sin(2 * np.pi * tremolo * t))
    return x

def pad_note(f, d, attack=0.5, release=0.5, harm=(1, 2), amps=(1, 0.25)):
    t = tt(d)
    x = sum(a * np.sin(2 * np.pi * f * h * t) for h, a in zip(harm, amps))
    return x * np.minimum(1, t / attack) * np.clip((d - t) / release, 0, 1)

def noise(d, seed=1):
    return np.random.default_rng(seed).standard_normal(int(d * SR))

def put(out, x, t, g=1.0):
    s = int(round(t * SR))
    if s >= len(out) or s + len(x) <= 0: return
    a, b = max(0, -s), min(len(x), len(out) - s)
    out[s + a:s + b] += x[a:b] * g

def reverb(x, rt=1.2, mix=0.25, seed=3):
    n = int(rt * SR)
    rng = np.random.default_rng(seed)
    ir = rng.standard_normal(n) * np.exp(-6.9 * np.arange(n) / n)
    ir[0] = 0
    L = len(x) + n
    N = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:L]
    y *= (np.abs(x).max() + 1e-9) / (np.abs(y).max() + 1e-9)
    out = np.zeros(L)
    out[:len(x)] += x * (1 - mix)
    out += y * mix
    return out

def kick(amp=1.0):
    t = tt(0.32); f = 45 + 95 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 12) * amp

def hat(amp=1.0, seed=5):
    x = np.diff(noise(0.07, seed), prepend=0)
    return x * np.exp(-tt(0.07) * 70) * amp

BEDS = {
    "calm":    dict(bpm=72, chords=[[48, 52, 55, 59], [45, 48, 52, 55], [41, 45, 48, 52], [43, 47, 50, 53]],
                    pad=0.45, arp=[0, 1, 2, 3, 2, 1, 2, 1], arp_amp=0.22, bass=0.45, kick=0.35, hat=0.05, rev=0.3),
    "funny":   dict(bpm=116, chords=[[48, 52, 55], [53, 57, 60], [55, 59, 62], [48, 52, 55]],
                    pad=0.16, penta=[60, 62, 64, 67, 69, 72], pluck=0.3, bass=0.45, tick=0.07, rev=0.12),
    "scary":   dict(bpm=60, chords=[[33, 34, 45]] * 4, pad=0.5, tremolo=5.0, heart=0.8, shimmer=0.035, rev=0.4),
    "sad":     dict(bpm=58, chords=[[45, 48, 52, 57], [41, 45, 48, 53], [48, 52, 55, 60], [43, 47, 50, 55]],
                    pad=0.5, bells=[72, 71, 69, 67, 69, 67, 64, 62], bell_amp=0.28, rev=0.4),
    "mystery": dict(bpm=76, chords=[[50, 53, 57, 60], [46, 50, 53, 57], [43, 46, 50, 53], [45, 49, 52, 55]],
                    pad=0.42, pings=[74, 77, 79, 81, 84], ping_amp=0.2, rev=0.45),
    "hype":    dict(bpm=126, chords=[[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]],
                    pad=0.2, kick=0.6, hat=0.07, bass8=0.4, arp16=0.2, rev=0.12),
}

def make_bed(mood):
    sp = BEDS[mood]; spb = 60.0 / sp["bpm"]; bar = 4 * spb; ch = sp["chords"]; bars = len(ch)
    L = int(round(bars * bar * SR)); out = np.zeros(2 * L + 2 * SR); rng = np.random.default_rng(42); step = spb / 4
    for loop in range(2):
        for bi, chord in enumerate(ch):
            t0 = (loop * bars + bi) * bar
            for n in chord:
                x = pad_note(midi(n), bar + 0.6)
                if sp.get("tremolo"): x = x * (0.8 + 0.2 * np.sin(2 * np.pi * sp["tremolo"] * tt(bar + 0.6)))
                put(out, x, t0 - 0.1, sp["pad"] / max(1, len(chord) ** 0.5))
            root = chord[0]
            if "bass" in sp:
                for b in (0, 2): put(out, tone(midi(root - 12), spb * 1.8, decay=2.5), t0 + b * spb, sp["bass"])
            if "arp" in sp:
                for s in range(8):
                    n = chord[sp["arp"][s] % len(chord)] + 12
                    put(out, tone(midi(n), spb, decay=6), t0 + s * spb / 2, sp["arp_amp"])
            if "kick" in sp:
                beats = (0, 2) if mood == "calm" else (0, 1, 2, 3)
                for b in beats: put(out, kick(), t0 + b * spb, sp["kick"])
            if "hat" in sp:
                for s in range(8): put(out, hat(seed=s + 1), t0 + s * spb / 2 + spb / 4 if mood == "hype" else t0 + s * spb / 2 + spb / 2, sp["hat"])
            if "penta" in sp:
                for s in range(16):
                    if rng.random() < 0.62:
                        n = int(rng.choice(sp["penta"]))
                        put(out, tone(midi(n), 0.25, decay=14, harm=(1, 2), amps=(1, .3)), t0 + s * step, sp["pluck"])
                put(out, tone(midi(root - 12), spb, decay=7), t0, sp["bass"])
                put(out, tone(midi(root - 12 + 7), spb, decay=7), t0 + 2.5 * spb, sp["bass"])
            if "tick" in sp:
                for b in range(4): put(out, tone(1200, 0.06, decay=60), t0 + b * spb, sp["tick"])
            if "heart" in sp:
                for b in range(4):
                    put(out, kick(), t0 + b * spb, sp["heart"]); put(out, kick(), t0 + b * spb + 0.26, sp["heart"] * 0.6)
            if "shimmer" in sp and bi % 2 == 0:
                for f in (2093.0, 2217.5): put(out, pad_note(f, bar * 2, attack=bar, release=bar), t0, sp["shimmer"])
            if "bells" in sp:
                for k, b in enumerate((0, 2)):
                    n = sp["bells"][(bi * 2 + k) % len(sp["bells"])]
                    put(out, tone(midi(n), 2.5, decay=1.6, harm=(1, 2.76, 5.4), amps=(1, .35, .15)), t0 + b * spb, sp["bell_amp"])
            if "pings" in sp:
                for _ in range(2):
                    n = int(rng.choice(sp["pings"]))
                    put(out, tone(midi(n), 3.0, decay=1.8, harm=(1, 2.01), amps=(1, .3)), t0 + rng.uniform(0, bar - 0.5), sp["ping_amp"])
            if "bass8" in sp:
                for s in range(8): put(out, tone(midi(root - 24), spb / 2, decay=6, harm=(1, 2), amps=(1, .4)), t0 + s * spb / 2, sp["bass8"])
            if "arp16" in sp:
                for s in range(16):
                    n = chord[s % len(chord)] + 12 * (1 + (s // 4) % 2)
                    put(out, tone(midi(n), 0.2, decay=12), t0 + s * step, sp["arp16"])
    y = reverb(out[:2 * L + SR], rt=1.8, mix=sp["rev"]); bed = y[L:2 * L]
    return bed / (np.abs(bed).max() + 1e-9) * 0.9

def music_track(timeline, seconds, intro_s, vol):
    n = int(seconds * SR); t = np.arange(n) / SR; tl = [(0.0, "calm")]
    for tm, m in sorted(timeline):
        if m != tl[-1][1]: tl.append((max(tm, tl[-1][0] + 2.0), m))
    used = sorted({m for _, m in tl}); out = np.zeros(n)
    for m in used:
        bed = make_bed(m); sig = np.tile(bed, n // len(bed) + 1)[:n]
        xs, ys = [0.0], [1.0 if tl[0][1] == m else 0.0]
        for i in range(1, len(tl)):
            xs += [tl[i][0] - 0.5, tl[i][0] + 1.5]
            ys += [1.0 if tl[i - 1][1] == m else 0.0, 1.0 if tl[i][1] == m else 0.0]
        g = np.sin(np.interp(t, xs, ys) * np.pi / 2)
        out += sig * g
    fade = np.interp(t, [0, intro_s, intro_s + 1.5, seconds - 2.5, seconds], [0, 0, 1, 1, 0])
    return out * fade * vol

# ================================================================= SOUND EFFECTS (sab yahin code se bante hain - free, koi download nahi)
# ~85 awaazein, har mood ke liye kai tarah ki. Har baar thodi alag (pitch / speed), aur ek hi awaaz baar-baar nahi bajti.
# Script me khud bhi laga sakte ho: {boom} {airhorn} {rimshot} {crickets} ... (poori list README me), ya {roast} {fail} {win} jaisa
# group likho to us group ki koi bhi awaaz. {nosfx} = is message par koi effect nahi.
import zlib

SFX_LIB, SFX_RAW, SFX_GAIN = {}, set(), {}

def _reg(*names, raw=False, gain=1.0):
    def deco(fn):
        for nm in names:
            SFX_LIB[nm] = fn; SFX_GAIN[nm] = gain
            if raw: SFX_RAW.add(nm)
        return fn
    return deco

# ----------------------------------------------------------------- chhote DSP auzaar
def sx_t(d): return np.arange(max(1, int(round(d * SR)))) / SR
def sx_noise(n, rng): return rng.standard_normal(max(1, int(n)))
def sx_un(x): return x / (np.abs(x).max() + 1e-9)
def sx_sat(x, drive=2.0): return np.tanh(drive * x) / np.tanh(drive)
def sx_pick(rng, seq): return seq[int(rng.integers(len(seq)))]
def sx_fade(x, ms=10):
    k = min(len(x) // 4, int(ms / 1000 * SR))
    if k > 1: x = np.array(x, float); x[-k:] *= np.linspace(1, 0, k)
    return x

def sx_osc(f, kind="sine", n=None, duty=0.5):
    """sine / saw / square / pulse / tri (band-limited). f = Hz (number ya har sample ka array)"""
    if np.ndim(f) == 0: f = np.full(int(n), float(f))
    f = np.asarray(f, float); ph = 2 * np.pi * np.cumsum(f) / SR
    if kind == "sine": return np.sin(ph)
    H = int(max(1, min(48, (SR * 0.45) / max(30.0, float(f.max())))))
    if kind == "saw": return sum(np.sin(h * ph) / h for h in range(1, H + 1)) * 0.6
    if kind == "square": return sum(np.sin(h * ph) / h for h in range(1, H + 1, 2))
    if kind == "pulse": return sum((np.sin(h * ph) - np.sin(h * (ph - 2 * np.pi * duty))) / h for h in range(1, H + 1)) * 0.5
    return sum(((-1) ** ((h - 1) // 2)) * np.sin(h * ph) / h ** 2 for h in range(1, H + 1, 2)) * 0.8

def sx_fft(x, fn):
    n = len(x)
    if n < 16: return x
    N = 1 << int(np.ceil(np.log2(n + 2048)))
    f = np.fft.rfftfreq(N, 1 / SR)
    return np.fft.irfft(np.fft.rfft(x, N) * fn(f), N)[:n]

def sx_lp(x, fc, o=2): return sx_fft(x, lambda f: 1 / np.sqrt(1 + (f / fc) ** (2 * o)))
def sx_hp(x, fc, o=2): return sx_fft(x, lambda f: 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * o)))
def sx_bp(x, f0, q=1.0): return sx_fft(x, lambda f: 1 / np.sqrt(1 + q * q * (f / f0 - f0 / np.maximum(f, 1e-3)) ** 2))

def sx_peaks(x, peaks):
    """[(Hz, q, dB)] - awaaz me 'formant' / chamak"""
    def fn(f):
        g = np.ones_like(f)
        for f0, q, db in peaks: g = g + (10 ** (db / 20) - 1) / (1 + q * q * (f / f0 - f0 / np.maximum(f, 1e-3)) ** 2)
        return g
    return sx_fft(x, fn)

def sx_tv(x, fn, n=1024, hop=256):
    """samay ke saath badalta filter: fn(freq[1,F], time[T,1]) -> gain[T,F]"""
    L = len(x); win = np.hanning(n + 1)[:-1]
    pad = np.concatenate([np.zeros(n), x, np.zeros(n)])
    nf = 1 + (len(pad) - n) // hop
    idx = np.arange(n)[None, :] + hop * np.arange(nf)[:, None]
    F = np.fft.rfft(pad[idx] * win, axis=1)
    f = np.fft.rfftfreq(n, 1 / SR); t = (hop * np.arange(nf) + n / 2 - n) / SR
    Y = np.fft.irfft(F * fn(f[None, :], t[:, None]), n, axis=1) * win
    out = np.zeros(len(pad))
    for i in range(nf): out[i * hop:i * hop + n] += Y[i]
    return out[n:n + L] / ((win ** 2).sum() / hop)

def sx_conv(a, b):
    L = len(a) + len(b) - 1; N = 1 << (L - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(a, N) * np.fft.rfft(b, N), N)[:L]

def sx_rev(x, rt=1.2, mix=0.25, seed=3, damp=5000):
    """kamre / hall ki gunj"""
    x = sx_fade(x); n = int(rt * SR); rng = np.random.default_rng(seed); t = np.arange(n) / SR
    ir = sx_lp(rng.standard_normal(n) * np.exp(-6.9 * t / rt), damp, 1)
    k = int(0.006 * SR); ir[:k] *= np.linspace(0, 1, k)
    wet = sx_conv(x, ir); wet *= np.sqrt((x ** 2).sum() / ((wet ** 2).sum() + 1e-12))
    out = np.zeros(len(wet)); out[:len(x)] += x * (1 - 0.4 * mix); out += wet * mix
    return out

def sx_mix(parts):
    """[(start sec, awaaz, gain)] -> ek awaaz"""
    parts = [(s, np.asarray(a, float), g) for s, a, g in parts if len(np.atleast_1d(a))]
    end = max(int(round(s * SR)) + len(a) for s, a, g in parts)
    out = np.zeros(end + 1)
    for s, a, g in parts: put(out, sx_fade(a, 6), s, g)
    return out

def sx_level(x, target=0.12, peak=0.72):
    """sab effects ki zor barabar (50ms ki sabse tez jagah se)"""
    if len(x) < 64: return x
    w = min(len(x), int(0.05 * SR))
    def loud(z):
        c = np.concatenate([[0], np.cumsum(z * z)]); return float(np.sqrt(((c[w:] - c[:-w]) / w).max())) + 1e-9
    e = max(loud(sx_hp(x, 120, 1)), 0.45 * loud(x))      # phone speaker bass nahi bajata -> bass wali awaaz thodi tez
    y = x * (target / e); pk = np.abs(y).max()
    if pk > peak: y = np.tanh(y / pk * 1.15) / np.tanh(1.15) * peak
    f = min(len(y) // 4, int(0.012 * SR))
    if f > 1: y[-f:] *= np.linspace(1, 0, f)
    return y

def sx_limit(x, thr=0.93, blk=256, rel=0.15):
    """sirf tez jagah par awaaz dabao (pehle ek boom poori video ki awaaz kam kar deta tha)"""
    n = len(x)
    if n == 0 or np.abs(x).max() <= thr: return x
    nb = (n + blk - 1) // blk
    g = np.minimum(1.0, thr / np.maximum(np.abs(np.pad(x, (0, nb * blk - n))).reshape(nb, blk).max(1), 1e-9))
    g = np.minimum(g, np.minimum(np.r_[g[1:], 1.0], np.r_[1.0, g[:-1]]))
    a, cur, out = np.exp(-blk / (rel * SR)), 1.0, np.empty(nb)
    for i in range(nb):
        cur = g[i] if g[i] < cur else min(g[i], 1 - (1 - cur) * a); out[i] = cur
    return np.clip(x * np.interp(np.arange(n), np.arange(nb) * blk + blk / 2, out), -0.99, 0.99)

def sx_pluck(f, d, rng, decay=0.996, bright=0.7):
    """Karplus-Strong: asli taar jaisa pluck (harp / pizzicato)"""
    N = max(2, int(round(SR / f - 0.5))); n = int(d * SR); out = np.zeros(n + N + 1)
    buf = rng.uniform(-1, 1, N)
    if bright < 1: buf = buf * bright + np.convolve(buf, [0.5, 0.5], "same") * (1 - bright)
    out[:N] = buf
    for s in range(N, n, N):
        e = min(n, s + N); a = out[s - N:e - N]; b = np.concatenate([[out[s - N - 1] if s - N - 1 >= 0 else 0.0], out[s - N:e - N - 1]])
        out[s:e] = decay * 0.5 * (a + b)
    y = out[:n]; k = min(n // 4, int(0.01 * SR))
    if k > 1: y[-k:] *= np.linspace(1, 0, k)
    return y

def sx_bell(f, d, parts=((1, 1, 2.5), (2.0, .45, 4), (3.0, .22, 6), (4.2, .12, 9)), att=0.001):
    t = sx_t(d); x = np.zeros(len(t))
    for k, a, dk in parts:
        if f * k < 17000: x += a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * dk)
    return x * np.minimum(1, t / att)

def sx_snare(rng, d=0.25, tf=190, bright=1.0):
    t = sx_t(d); nz = sx_un(sx_bp(sx_noise(len(t), rng), 3500, 0.6)) * np.exp(-t * 26)
    body = sx_osc(tf * (1 + 0.3 * np.exp(-t * 60))) * np.exp(-t * 22) + 0.5 * sx_osc(tf * 1.75 * np.ones(len(t))) * np.exp(-t * 30)
    return (nz * 0.9 * bright + body * 0.6) * np.minimum(1, t / 0.001)

def sx_tom(rng, f=110, d=0.45):
    t = sx_t(d); x = sx_osc(f * (1 + 0.35 * np.exp(-t * 25))) * np.exp(-t * 9)
    return x + sx_un(sx_lp(sx_noise(len(t), rng), 1500)) * np.exp(-t * 60) * 0.3

def sx_cymbal(rng, d=1.4, k=2.6):
    t = sx_t(d); fs = np.array([205.3, 304.4, 369.6, 522.7, 540.0, 800.0]) * rng.uniform(0.95, 1.05)
    metal = sum(np.sign(np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))) for f in fs)
    return sx_un(sx_hp(metal * 0.3 + sx_noise(len(t), rng), 5000)) * np.exp(-t * k) * np.minimum(1, t / 0.002)

def sx_timp(rng, f, d=1.2):
    t = sx_t(d)
    x = sx_osc(f * (1 + 0.08 * np.exp(-t * 20))) * np.exp(-t * 3) + 0.4 * sx_osc(f * 1.5 * np.ones(len(t))) * np.exp(-t * 5) + 0.2 * sx_osc(f * 1.98 * np.ones(len(t))) * np.exp(-t * 6)
    return (x + sx_un(sx_lp(sx_noise(len(t), rng), 600)) * np.exp(-t * 30) * 0.5) * np.minimum(1, t / 0.002)

def sx_piano(f, d, rng, vel=1.0):
    t = sx_t(d); B = 0.00035; x = np.zeros(len(t)); kf = (f / 440) ** 0.4
    for n in range(1, 11):
        fn_ = f * n * np.sqrt(1 + B * n * n)
        if fn_ > 15000: break
        k = (0.7 + 0.45 * n) * kf
        x += vel / n ** 1.15 * (1 + 0.3 * np.sin(n * 1.7)) * np.sin(2 * np.pi * fn_ * t + rng.uniform(0, 6.28)) * (0.65 * np.exp(-t * k) + 0.35 * np.exp(-t * k * 0.25))
    ham = sx_un(sx_lp(sx_noise(len(t), rng), 3000)) * np.exp(-t * 150) * 0.12 * vel
    return (x + ham) * np.minimum(1, t / 0.002) * np.minimum(1, (d - t) / 0.05)

def sx_brass(f, d, rng, vib=0.0, att=0.03, voices=2, bright=1.0):
    t = sx_t(d); fv = f * (1 + vib * np.minimum(1, t / 0.25) * np.sin(2 * np.pi * 5.3 * t))
    x = sum(sx_osc(fv * (1 + 0.0035 * (v - (voices - 1) / 2)), "saw") for v in range(voices)) / voices
    fc0, fc1 = f * 2.5, min(9000, f * (9 + 6 * bright))
    x = sx_tv(x, lambda fr, tq: 1 / np.sqrt(1 + (fr / (fc0 + (fc1 - fc0) * np.minimum(1, np.maximum(tq, 0) / 0.06) * (0.75 + 0.25 * np.exp(-np.maximum(tq, 0) * 3)))) ** 4))
    return x * np.minimum(1, t / att) * (0.85 + 0.15 * np.exp(-t * 6)) * np.minimum(1, (d - t) / 0.06)

def sx_string(f, d, rng, vib=0.006, att=0.25):
    t = sx_t(d); vv = vib * np.minimum(1, np.maximum(0, t - 0.15) / 0.3)
    fv = f * (1 + vv * np.sin(2 * np.pi * rng.uniform(5.2, 5.8) * t))
    x = sum(sx_osc(fv * (1 + 0.003 * k), "saw") for k in (-1, 0, 1)) / 3
    x = sx_peaks(sx_lp(x, 3800), [(300, 2, 4), (480, 3, 3), (2900, 2, 4)])
    bow = sx_un(sx_bp(sx_noise(len(t), rng), 3500, 0.7)) * 0.03
    return (x + bow) * np.minimum(1, t / att) ** 1.5 * np.minimum(1, (d - t) / 0.35)

def sx_chip(f, d, duty=0.25, decay=0.0, vib=0.0):
    """8-bit game wali awaaz"""
    t = sx_t(d); fv = f * (1 + vib * np.sin(2 * np.pi * 7 * t))
    x = sx_osc(fv, "pulse", duty=duty)
    return x * np.minimum(1, t / 0.002) * (np.exp(-t * decay) if decay else 1) * np.minimum(1, (d - t) / 0.004)

def sx_whoosh(rng, d, peak, sharp=False, deep=False):
    t = sx_t(d)
    def fn(f, tq):
        u = np.clip(tq / d, 0, 1); fc = 250 + peak * np.sin(np.pi * u) ** 1.5
        g = 1 / (1 + 1.5 * (f / fc - fc / np.maximum(f, 1)) ** 2)
        return g / np.sqrt(1 + (f / 1200) ** 2) if deep else g
    return sx_un(sx_tv(sx_noise(len(t), rng), fn)) * np.sin(np.pi * t / d) ** (2.5 if sharp else 1.6)

# ----------------------------------------------------------------- UI awaazein (purani, waisi hi)
@_reg("send", raw=True)
def _s_send(rng, nm):
    t = tt(0.09); return np.sin(2 * np.pi * np.cumsum(700 - 3000 * t) / SR) * np.exp(-t * 35) * 0.30

@_reg("recv", raw=True)
def _s_recv(rng, nm):
    x = np.zeros(int(0.5 * SR)); put(x, tone(880, 0.4, decay=9), 0, 0.22); put(x, tone(1318.5, 0.4, decay=9), 0.07, 0.22); return x

@_reg("recv_gemini", "recv_grok", "recv_claude", raw=True)
def _s_recv_ai(rng, nm):
    if nm == "recv_gemini":       # chamakti 3 note
        return sx_mix([(i * 0.05, sx_bell(midi(n), 0.4, ((1, 1, 11), (2.0, .2, 20))), 0.13) for i, n in enumerate((88, 92, 95))])
    if nm == "recv_grok":         # neeche wala punchy blip
        t = sx_t(0.22); f = 190 + 260 * np.exp(-t * 14)
        x = (sx_osc(f) + 0.4 * sx_osc(2 * f) + 0.15 * sx_osc(3 * f)) * np.exp(-t * 15) * np.minimum(1, t / 0.002)
        return x * 0.2
    m = lambda f, d: sx_bell(f, d, ((1, 1, 9), (3.9, .3, 40)), 0.002)          # claude: naram marimba
    return sx_mix([(0, m(midi(79), 0.4), 0.2), (0.08, m(midi(86), 0.45), 0.18)])

@_reg("whoosh", raw=True)
def _s_whoosh0(rng, nm):
    d = 0.7; t = tt(d); w = np.diff(noise(d, 8), prepend=0) * np.sin(np.pi * t / d) ** 2
    return w / (np.abs(w).max() + 1e-9) * 0.4

@_reg("hit", raw=True)
def _s_hit0(rng, nm):
    t = tt(0.5); x = np.sin(2 * np.pi * 62 * t) * np.exp(-t * 9) + sx_lp(noise(0.5, 6), 900) * np.exp(-t * 30) * 2
    return x / (np.abs(x).max() + 1e-9) * 0.55

@_reg("pop2", raw=True)
def _s_pop2(rng, nm):
    t = tt(0.16); x = np.sin(2 * np.pi * np.cumsum(520 + 1500 * t) / SR) * np.exp(-t * 20) * np.minimum(1, t / 0.004)
    return x * 0.35

@_reg("subscribe", raw=True)
def _s_subscribe(rng, nm):
    x = np.zeros(int(0.5 * SR))
    put(x, tone(1800, 0.05, decay=90), 0, 0.5); put(x, tone(880, 0.35, decay=9), 0.06, 0.28); put(x, tone(1318.5, 0.35, decay=9), 0.13, 0.25)
    return x

@_reg("bell", raw=True)
def _s_bell0(rng, nm):
    d = 1.4; x = (tone(1568, d, decay=3.2, harm=(1, 2.4, 4.1), amps=(1, .4, .2)) + tone(1046.5, d, decay=3.6, harm=(1, 2.7), amps=(.7, .3)))
    y = np.zeros(int(1.8 * SR)); put(y, x, 0, 0.3); put(y, x, 0.38, 0.22); put(y, x, 0.76, 0.16)
    return reverb(y, rt=1.0, mix=0.2)

# ----------------------------------------------------------------- purane mood effects (naye naam se, group me bhi hain)
@_reg("boing0", "rumble", "growl", "bells_sad", "chime", "rise")
def _s_classic(rng, nm):
    k = rng.uniform(0.94, 1.06)
    if nm == "boing0":
        t = tt(0.55); f = (240 + 170 * np.sin(2 * np.pi * 9 * t) * np.exp(-5 * t) + 330 * np.exp(-6 * t)) * k
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    if nm in ("rumble", "growl"):
        d = 1.8 if nm == "rumble" else 0.7; t = tt(d); f = (55 if nm == "rumble" else 80) * k
        body = np.sin(2 * np.pi * f * t) * np.exp(-t * (2.2 if nm == "rumble" else 5))
        rum = np.convolve(sx_noise(len(t), rng), np.ones(60) / 60, mode="same") * np.exp(-t * 3) * 3
        x = body * 0.7 + rum * 0.4
        if nm == "growl":
            saw = sum(np.sin(2 * np.pi * f * h * t) / h for h in range(1, 9)) * np.exp(-t * 6)
            x = np.tanh(saw * 1.6) * 0.5 + body * 0.4
        return reverb(x, rt=1.2, mix=0.3)[:int(d * SR + SR)]
    if nm == "bells_sad":
        x = np.zeros(int(2.4 * SR))
        put(x, tone(midi(76) * k, 1.8, decay=2.2, harm=(1, 2.76), amps=(1, .3)), 0, 0.3)
        put(x, tone(midi(72) * k, 2.0, decay=2.0, harm=(1, 2.76), amps=(1, .3)), 0.45, 0.3)
        return reverb(x, rt=1.5, mix=0.35)
    if nm == "chime":
        d = 2.6
        x = (tone(1318.5 * k, d, decay=1.6, harm=(1, 1.5), amps=(1, .5), tremolo=6) + tone(1976 * k, d, decay=1.8, tremolo=4) * 0.6 + tone(2637 * k, d, decay=2.2) * 0.35)
        return reverb(x * 0.18, rt=2.0, mix=0.45)
    d = 0.65; t = tt(d); w = np.diff(sx_noise(len(t), rng), prepend=0) * np.sin(np.pi * t / d) ** 2 * 0.6
    x = w.copy()
    for i, n in enumerate((84, 88, 91, 96)): put(x, tone(midi(n) * k, 0.3, decay=12), 0.28 + i * 0.06, 0.66)
    return x

# ----------------------------------------------------------------- COMEDY
@_reg("boing", "boing_hi")
def _s_boing(rng, nm):                       # cartoon spring
    d = rng.uniform(0.6, 0.8); t = sx_t(d)
    f0 = rng.uniform(170, 230) * (1.6 if nm == "boing_hi" else 1)
    f = f0 * (1 + 0.9 * (1 - np.exp(-t * 28))) * (1 + 0.22 * np.sin(2 * np.pi * rng.uniform(13, 17) * t) * np.exp(-t * 3.2))
    return (sx_osc(f) + 0.35 * sx_osc(2 * f) + 0.12 * sx_osc(3 * f)) * np.minimum(1, t / 0.004) * np.exp(-t * 4.0)

@_reg("doing")
def _s_doing(rng, nm):                       # jaw harp "doyoyoyoing"
    d = 0.9; t = sx_t(d); f0 = rng.uniform(95, 125); rate = rng.uniform(6, 8.5); ph = rng.uniform(0, 6.28)
    src = sx_osc(f0, "saw", len(t))
    def fn(f, tq):
        fc = 1100 + 750 * np.sin(2 * np.pi * rate * tq + ph) * np.exp(-1.8 * np.maximum(tq, 0))
        return 0.15 + 3.0 / (1 + 25 * (f / fc - fc / np.maximum(f, 1)) ** 2)
    return sx_tv(src, fn) * np.minimum(1, t / 0.003) * np.exp(-t * 3.2)

@_reg("slide_up", "slide_down")
def _s_slide(rng, nm):                       # slide whistle
    d = rng.uniform(0.45, 0.65); t = sx_t(d); u = t / d
    lo, hi = rng.uniform(480, 600), rng.uniform(1500, 1900)
    k = u ** 0.85 if nm == "slide_up" else 1 - u ** 1.15
    f = lo * (hi / lo) ** k * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * t))
    air = sx_un(sx_bp(sx_noise(len(t), rng), 2200, 1.2)) * 0.06
    return (sx_osc(f) + 0.06 * sx_osc(2 * f) + air) * np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.05)

@_reg("honk", "honk2")
def _s_honk(rng, nm):                        # joker / cycle horn: honk honk
    f0 = rng.uniform(380, 440); parts, t0 = [], 0.0; nh = 2 if nm == "honk" else 3
    for i in range(nh):
        d = rng.uniform(0.16, 0.2) if i < nh - 1 else rng.uniform(0.22, 0.28); t = sx_t(d)
        f = f0 * (1 + 0.03 * i) * (0.93 + 0.07 * np.minimum(1, t / 0.035)) * (1 + 0.01 * np.sin(2 * np.pi * 47 * t))
        x = sx_peaks(sx_lp(sx_osc(f, "pulse", duty=0.3), 4200), [(1150, 2.5, 9), (2500, 3, 5)])
        x = sx_sat(sx_un(x) * 1.2, 1.8) * np.minimum(1, t / 0.008) * np.minimum(1, (d - t) / 0.025)
        parts.append((t0, x, 1.0)); t0 += d + rng.uniform(0.06, 0.09)
    return sx_mix(parts)

@_reg("bonk")
def _s_bonk(rng, nm):                        # sar par "bonk"
    d = 0.45; t = sx_t(d); f = rng.uniform(300, 360) * (1 + 0.55 * np.exp(-t * 40))
    x = sx_osc(f) * np.exp(-t * 14) + 0.5 * sx_osc(f * 1.62) * np.exp(-t * 22) + 0.25 * sx_osc(f * 2.43) * np.exp(-t * 30)
    click = sx_un(sx_hp(sx_noise(len(t), rng), 2000)) * np.exp(-t * 400) * 0.6
    thud = sx_osc(110 * (1 + 0.5 * np.exp(-t * 30))) * np.exp(-t * 18) * 0.6
    return (x + click + thud) * np.minimum(1, t / 0.001)

@_reg("rimshot")
def _s_rimshot(rng, nm):                     # ba-dum-tss
    a = rng.uniform(0.15, 0.18)
    return sx_mix([(0, sx_snare(rng), 0.9), (a, sx_tom(rng, rng.uniform(95, 115)), 0.9), (2 * a + 0.02, sx_cymbal(rng), 0.5)])

@_reg("pops")
def _s_pops(rng, nm):
    parts, t0 = [], 0.0
    for _ in range(int(rng.integers(3, 5))):
        t = sx_t(0.07); f0 = rng.uniform(260, 620)
        parts.append((t0, sx_osc(f0 * (1 + 2.2 * np.minimum(1, t / 0.025))) * np.minimum(1, t / 0.002) * np.exp(-t * 55), rng.uniform(0.7, 1)))
        t0 += rng.uniform(0.07, 0.12)
    return sx_mix(parts)

@_reg("squeak")
def _s_squeak(rng, nm):                      # rubber toy
    b = rng.uniform(1250, 1600); parts = []
    for st, d, k in ((0.0, rng.uniform(0.15, 0.19), 1.0), (rng.uniform(0.22, 0.27), rng.uniform(0.1, 0.13), 0.82)):
        t = sx_t(d); f = b * k * (1 + 0.28 * np.sin(np.pi * t / d)) * (1 + 0.02 * np.sin(2 * np.pi * 38 * t))
        x = sx_lp(sx_osc(f, "pulse", duty=0.35), 5000) + sx_un(sx_bp(sx_noise(len(t), rng), 3000, 1.5)) * 0.08
        parts.append((st, x * np.sin(np.pi * t / d) ** 0.6, 1.0))
    return sx_mix(parts)

@_reg("zip", "zip_down")
def _s_zip(rng, nm):                         # "zwip"
    d = rng.uniform(0.12, 0.16); t = sx_t(d); u = t / d
    f = 300 * 10 ** (u if nm == "zip" else 1 - u)
    return sx_osc(f) * np.sin(np.pi * u) ** 0.5 + sx_un(sx_hp(sx_noise(len(t), rng), 3000)) * np.sin(np.pi * u) * 0.12

def _xylo(f, d=0.35):
    t = sx_t(d)
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 9) + 0.35 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t * 35)
            + 0.12 * np.sin(2 * np.pi * f * 9.5 * t) * np.exp(-t * 70) * (f * 9.5 < 17000)) * np.minimum(1, t / 0.0015)

@_reg("xylo_up", "xylo_down")
def _s_xylo(rng, nm):
    r = int(sx_pick(rng, [72, 74, 76])); sp = rng.uniform(0.04, 0.055)
    notes = [r + s for s in (0, 2, 4, 5, 7, 9, 11, 12)] if nm == "xylo_up" else [r + 12 - s for s in (0, 1, 3, 5, 6, 8, 10, 12)]
    return sx_mix([(i * sp, _xylo(midi(n)), 0.8) for i, n in enumerate(notes)])

@_reg("sad_trombone")
def _s_trombone(rng, nm):                    # wah wah wah waaah
    b = int(sx_pick(rng, [53, 55, 56])); durs = [0.36, 0.36, 0.36, 1.1]; parts, pts, t0 = [], [], 0.0
    for i, d in enumerate(durs):
        t = sx_t(d); f = midi(b - i) * np.ones(len(t))
        if i == 3: f = f * (1 + np.minimum(1, t / 0.3) * 0.035 * np.sin(2 * np.pi * 5.2 * t)) * 2 ** (-np.clip((t - 0.55) / 0.5, 0, 1) / 12)
        parts.append((t0, sx_osc(f, "saw") * np.minimum(1, t / 0.02) * np.minimum(1, (d - t) / 0.05), 1.0))
        pts += [(t0, 350), (t0 + 0.09, 2000), (t0 + d * 0.7, 1300), (t0 + d, 450)]; t0 += d + 0.04
    ts, vs = zip(*pts); tl = t0 - 1.14
    def fn(f, tq):
        fc = np.interp(tq, ts, vs) * (1 + 0.25 * np.sin(2 * np.pi * 5.2 * tq) * (tq > tl))
        return 1 / np.sqrt(1 + (f / fc) ** 4) * (1 + 1.5 / (1 + 9 * (f / fc - fc / np.maximum(f, 1)) ** 2))
    return sx_tv(sx_mix(parts), fn)

@_reg("deflate")
def _s_deflate(rng, nm):                     # gubbara hawa nikalna
    d = rng.uniform(0.9, 1.2); t = sx_t(d); u = t / d
    jit = sx_lp(sx_noise(len(t), rng), 40); jit /= np.std(jit) + 1e-9
    f = 650 * (170 / 650) ** u * (1 + 0.07 * np.sin(2 * np.pi * rng.uniform(24, 32) * t) + 0.03 * jit)
    x = sx_lp(sx_osc(f, "pulse", duty=0.2), 3500) * 0.8 + sx_un(sx_bp(sx_noise(len(t), rng), 1800, 0.8)) * 0.25
    return x * np.minimum(1, t / 0.02) * (1 - u) ** 0.4

@_reg("fall")
def _s_fall(rng, nm):                        # girne ki seeti + dhamm
    d = rng.uniform(0.85, 1.05); t = sx_t(d); u = t / d
    f = 1900 * (380 / 1900) ** (u ** 1.3) * (1 + 0.012 * np.sin(2 * np.pi * 6 * t))
    w = sx_osc(f) * np.minimum(1, t / 0.05) * (0.6 + 0.4 * u)
    t2 = sx_t(0.5); thud = sx_osc(70 * (1 + 0.6 * np.exp(-t2 * 25))) * np.exp(-t2 * 10) + sx_un(sx_lp(sx_noise(len(t2), rng), 400)) * np.exp(-t2 * 14) * 0.8
    return sx_mix([(0, w, 0.6), (d + 0.02, thud, 1.0)])

@_reg("tada")
def _s_tada(rng, nm):
    r = int(sx_pick(rng, [60, 62, 63])); ch = (r, r + 4, r + 7, r + 12)
    a = sum(sx_brass(midi(n), 0.13, rng) for n in ch); b = sum(sx_brass(midi(n), 1.0, rng, vib=0.006) for n in ch)
    return sx_rev(sx_mix([(0, a, 0.5), (0.17, b, 0.5), (0.17, sx_cymbal(rng, 1.3, 2.2), 0.3)]), 1.4, 0.2)

@_reg("fanfare")
def _s_fanfare(rng, nm):                     # jeet ka baaja
    r = int(sx_pick(rng, [60, 62, 65]))
    parts = [(st, sx_brass(midi(n), d, rng, vib=0.006 if d > 0.5 else 0), 0.6) for n, st, d in ((r, 0, 0.12), (r + 4, 0.14, 0.12), (r + 7, 0.28, 0.12), (r + 12, 0.42, 0.9))]
    parts += [(0.42, sum(sx_brass(midi(n), 0.9, rng) for n in (r - 12, r, r + 4, r + 7)), 0.3), (0.42, sx_cymbal(rng, 1.4, 2.0), 0.3)]
    return sx_rev(sx_mix(parts), 1.6, 0.22)

# ----------------------------------------------------------------- ROAST / IMPACT
@_reg("boom", "boom2", gain=1.15)
def _s_boom(rng, nm):                        # bhaari meme "BOOM"
    big = nm == "boom"; d = 2.0 if big else 0.9; t = sx_t(d)
    f = rng.uniform(44, 52) + rng.uniform(60, 80) * np.exp(-t * (16 if big else 24))
    x = sx_sat(sx_osc(f) * np.exp(-t * (1.9 if big else 4.5)), 2.5) * 0.8      # saturation -> phone speaker par bhi
    x = x + sx_un(sx_lp(sx_noise(len(t), rng), 350)) * np.exp(-t * 7) * 0.35 + sx_un(sx_lp(sx_noise(len(t), rng), 3000)) * np.exp(-t * 90) * 0.3
    x *= np.minimum(1, t / 0.002)
    return sx_rev(x, 1.8, 0.28) if big else x

@_reg("airhorn", gain=0.9)
def _s_airhorn(rng, nm):
    f0 = rng.uniform(430, 470); parts, t0 = [], 0.0
    pat = [(0.17, 0), (0.17, 0), (0.7, 1)] if rng.random() < 0.7 else [(0.14, 0), (0.14, 0), (0.14, 0), (0.75, 1)]
    for d, lg in pat:
        t = sx_t(d); bend = (0.96 + 0.04 * np.minimum(1, t / 0.035)) * (1 - 0.03 * lg * np.clip((t - d + 0.18) / 0.18, 0, 1))
        x = sum(sx_osc(f0 * k * bend, "saw") for k in (1, 1.006, 1.26, 1.266, 1.5, 0.5))
        x = sx_peaks(sx_hp(x, 250), [(1700, 1.2, 6), (3200, 2, 3)])
        x = sx_sat(sx_un(x) * 1.3, 2.2) * np.minimum(1, t / 0.006) * np.minimum(1, (d - t) / 0.02)
        parts.append((t0, x, 1.0)); t0 += d + 0.06
    return sx_rev(sx_mix(parts), 0.9, 0.15)

@_reg("explosion")
def _s_explosion(rng, nm):
    d = 2.6; t = sx_t(d)
    roar = sx_un(sx_tv(sx_noise(len(t), rng), lambda f, tq: 1 / np.sqrt(1 + (f / (300 + 5000 * np.exp(-np.maximum(tq, 0) * 5))) ** 4)) * np.minimum(1, t / 0.004) * np.exp(-t * 1.9))
    sub = sx_sat(sx_osc(38 + 40 * np.exp(-t * 8)) * np.exp(-t * 3.5), 2)
    crack = np.zeros(len(t))
    for _ in range(int(rng.integers(30, 50))):
        s = int((0.02 + rng.exponential(0.35)) * SR)
        if s < len(t) - 400: crack[s:s + 200] += sx_hp(sx_noise(200, rng), 2500) * np.exp(-np.arange(200) / 25) * rng.uniform(0.2, 0.7)
    return sx_rev(roar * 0.9 + sub * 0.7 + sx_un(crack) * 0.4, 2.0, 0.3)

@_reg("burn")
def _s_burn(rng, nm):                        # aag ki "fwoosh" + chatak
    d = rng.uniform(0.9, 1.2); t = sx_t(d)
    def fn(f, tq):
        fc = 350 + 2600 * np.sin(np.pi * np.clip(tq / d, 0, 1)) ** 1.5
        return 1 / (1 + 4 * (f / fc - fc / np.maximum(f, 1)) ** 2) + 0.15 / np.sqrt(1 + (f / 800) ** 2)
    x = sx_un(sx_tv(sx_noise(len(t), rng), fn) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.2)
    cr = np.zeros(len(t))
    for _ in range(int(rng.integers(12, 22))):
        s = int(rng.uniform(0.1, d - 0.05) * SR); cr[s:s + 120] += sx_hp(sx_noise(120, rng), 3000) * np.exp(-np.arange(120) / 18) * rng.uniform(0.3, 1)
    return x + sx_un(cr) * 0.35

@_reg("slap")
def _s_slap(rng, nm):                        # thappad
    t = sx_t(0.25)
    x = (sx_un(sx_bp(sx_noise(len(t), rng), 2400, 0.5)) * np.exp(-t * 110) + sx_un(sx_lp(sx_noise(len(t), rng), 900)) * np.exp(-t * 60) * 0.7
         + sx_osc(240.0, n=len(t)) * np.exp(-t * 45) * 0.3) * np.minimum(1, t / 0.0006)
    return sx_rev(x, 0.5, 0.18)

@_reg("impact", "impact_deep", "impact_metal", "slam")
def _s_impact(rng, nm):                      # filmi dhamaka-hit
    d = 1.0 if nm == "slam" else 2.2; t = sx_t(d)
    low = sx_sat(sx_osc(rng.uniform(40, 48) * (1 + 0.8 * np.exp(-t * 20))) * np.exp(-t * (2.6 if nm == "impact_deep" else 4)), 2.0)
    mid = sx_un(sx_bp(sx_noise(len(t), rng), 420, 0.7)) * np.exp(-t * 14)
    top = sx_un(sx_hp(sx_noise(len(t), rng), 3000)) * np.exp(-t * 45)
    if nm == "slam":
        x = mid * 0.9 + sx_osc(90 * (1 + 0.6 * np.exp(-t * 30))) * np.exp(-t * 16) * 0.7 + top * 0.3
        return sx_rev(x * np.minimum(1, t / 0.0008), 0.7, 0.22)
    snap = sx_un(sx_bp(sx_noise(len(t), rng), 1800, 0.8)) * np.exp(-t * 28)
    x = low * 0.75 + mid * 0.8 + snap * 0.3 + top * (0.0 if nm == "impact_deep" else 0.3)
    if nm == "impact_metal":
        fm = rng.uniform(190, 230)
        x = x + sum(a * sx_osc(fm * k, n=len(t)) * np.exp(-t * (3 + i * 1.5)) for i, (k, a) in enumerate(((1, .5), (1.63, .4), (2.51, .3), (3.86, .22), (5.2, .15))))
    return sx_rev(x * np.minimum(1, t / 0.0008), 1.8, 0.3)

@_reg("ring")
def _s_ring(rng, nm):                        # hit ke baad kaan me "eeee" (emotional damage)
    t = sx_t(2.0); tin = sx_osc(rng.uniform(3500, 4100), n=len(t)) * np.interp(t, [0, 0.25, 1.3, 2.0], [0, 1, 0.8, 0]) * 0.18
    return sx_mix([(0, _s_impact(rng, "impact_deep"), 1.0), (0.12, tin, 1.0)])

@_reg("glass")
def _s_glass(rng, nm):                       # sheesha tootna
    d = 1.1; out = np.zeros(int(d * SR)); t = sx_t(0.25)
    put(out, sx_un(sx_hp(sx_noise(len(t), rng), 2500)) * np.exp(-t * 18) * np.minimum(1, t / 0.001), 0, 0.8)
    for _ in range(int(rng.integers(45, 70))):
        st = min(d - 0.15, rng.exponential(0.16)); tq = sx_t(rng.uniform(0.04, 0.13))
        p = sum(rng.uniform(0.3, 1) * sx_osc(rng.uniform(2500, 9000), n=len(tq)) for _ in range(2))
        put(out, p * np.exp(-tq * rng.uniform(25, 60)) * np.minimum(1, tq / 0.0005), st, rng.uniform(0.1, 0.35))
    return sx_rev(out, 0.8, 0.15)

@_reg("bass_drop", gain=1.1)
def _s_drop(rng, nm):
    d = 1.6; t = sx_t(d)
    x = sx_sat(sx_osc(36 + 140 * np.exp(-t * rng.uniform(3.5, 5))) * np.exp(-t * 1.6), 3.0)
    return (x * 0.85 + sx_un(sx_lp(sx_noise(len(t), rng), 2500)) * np.exp(-t * 80) * 0.5) * np.minimum(1, t / 0.002)

# ----------------------------------------------------------------- GUSSA
@_reg("punch")
def _s_punch(rng, nm):                       # ghoonsa
    t = sx_t(0.4)
    hit = (sx_osc(rng.uniform(95, 120) * (1 + 0.7 * np.exp(-t * 30))) * np.exp(-t * 16) * 0.9
           + sx_un(sx_lp(sx_noise(len(t), rng), 1500)) * np.exp(-t * 35) * 0.6 + sx_un(sx_hp(sx_noise(len(t), rng), 2500)) * np.exp(-t * 150) * 0.35) * np.minimum(1, t / 0.0008)
    return sx_mix([(0, sx_whoosh(rng, 0.12, 2500, sharp=True), 0.45), (0.1, hit, 1.0)]), 0.1

@_reg("clang")
def _s_clang(rng, nm):                       # loha / anvil
    d = 2.0; t = sx_t(d); f = rng.uniform(560, 700)
    x = sum(a * sx_osc(f * k * rng.uniform(0.995, 1.005), n=len(t)) * np.exp(-t * dk) for k, a, dk in ((1, 1, 2.2), (2.32, .7, 3.0), (4.25, .5, 4.5), (6.63, .35, 6), (9.38, .2, 8)))
    strike = sx_un(sx_hp(sx_noise(len(t), rng), 2000)) * np.exp(-t * 120) * 0.8
    return sx_rev((x * 0.5 + strike) * np.minimum(1, t / 0.0005), 1.4, 0.25)

@_reg("buzzer", gain=0.8)
def _s_buzzer(rng, nm):                      # galat jawab "ehhhh"
    d = rng.uniform(0.6, 0.8); t = sx_t(d); f = rng.uniform(140, 160)
    x = sx_osc(f, "square", len(t)) + sx_osc(f * 1.045, "square", len(t)) * 0.8
    return sx_sat(sx_lp(x, 3500) * 0.8, 2.5) * np.minimum(1, t / 0.006) * np.minimum(1, (d - t) / 0.015)

@_reg("thunder")
def _s_thunder(rng, nm):                     # bijli + gadgadahat
    d = 3.2; t = sx_t(d)
    crack = sx_hp(sx_noise(len(t), rng), 900) * np.exp(-t * 7) * np.minimum(1, t / 0.003)
    for _ in range(int(rng.integers(3, 7))):
        s = rng.uniform(0.02, 0.35); crack += sx_hp(sx_noise(len(t), rng), 1500) * np.exp(-np.maximum(0, t - s) * 30) * (t >= s) * rng.uniform(0.3, 0.8)
    rum = sx_un(sx_lp(sx_noise(len(t), rng), 180, 3))
    am = 0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(0.7, 1.4) * t + rng.uniform(0, 6)) * np.sin(2 * np.pi * rng.uniform(2, 3.5) * t)
    return sx_rev(sx_un(crack) * 0.6 + rum * am * np.interp(t, [0, 0.15, 1.0, d], [0, 1, 0.7, 0]) * 0.9, 2.2, 0.3)

@_reg("alarm", gain=0.8)
def _s_alarm(rng, nm):                       # "whoop whoop"
    parts = []
    for i in range(2):
        d = 0.38; t = sx_t(d); f = rng.uniform(480, 560) * 3.0 ** (t / d)
        parts.append((i * 0.44, sx_lp(sx_osc(f, "square"), 4000) * np.minimum(1, t / 0.01) * np.minimum(1, (d - t) / 0.02), 1.0))
    return sx_mix(parts)

@_reg("braam")
def _s_braam(rng, nm):                       # filmi "BRAAAM"
    r = int(sx_pick(rng, [36, 38, 40])); d = 2.4; t = sx_t(d)
    x = sum(sx_osc(midi(n) * (1 + 0.004 * v), "saw", len(t)) for n in (r - 12, r, r + 7, r + 12, r + 15) for v in (-1, 1)) / 6
    x = sx_tv(x, lambda f, tq: 1 / np.sqrt(1 + (f / (300 + 2200 * np.minimum(1, np.maximum(tq, 0) / 0.08) * np.exp(-np.maximum(tq, 0) * 1.2))) ** 4))
    x = sx_sat(sx_un(x) * 1.4, 1.8) * np.minimum(1, t / 0.03) * np.interp(t, [0, 0.1, 1.4, d], [1, 1, 0.6, 0])
    return sx_rev(x, 2.4, 0.33)

@_reg("sword")
def _s_sword(rng, nm):                       # talwar "shiiing"
    d = 1.3; t = sx_t(d)
    scrape = sx_un(sx_tv(sx_noise(len(t), rng), lambda f, tq: 1 / (1 + 6 * (f / (2500 + 5000 * np.clip(tq / 0.18, 0, 1)) - (2500 + 5000 * np.clip(tq / 0.18, 0, 1)) / np.maximum(f, 1)) ** 2)) * np.interp(t, [0, 0.03, 0.2, 0.35], [0, 1, 0.6, 0]))
    rf = rng.uniform(2600, 3200)
    ring_ = sum(a * sx_osc(rf * k * (1 + 0.002 * np.sin(2 * np.pi * 7 * t))) * np.exp(-t * dk) for k, a, dk in ((1, 1, 2.5), (1.47, .6, 3.5), (2.09, .4, 5)))
    return sx_rev(scrape * 0.7 + ring_ * np.minimum(1, t / 0.12) * 0.25, 1.2, 0.2)

# ----------------------------------------------------------------- SAD
@_reg("piano_sad", "piano_sad2", "piano_low")
def _s_piano(rng, nm):
    if nm == "piano_low":
        r = int(sx_pick(rng, [45, 43, 41]))
        return sx_rev(sx_mix([(0, sx_piano(midi(r - 12), 3.0, rng, 0.9), 0.6), (0, sx_piano(midi(r), 3.0, rng, 0.8), 0.5), (0.02, sx_piano(midi(r + 3), 2.8, rng, 0.6), 0.35)]), 2.4, 0.35)
    phr = sx_pick(rng, [[76, 72, 69], [74, 72, 69, 64], [72, 71, 69], [76, 74, 71, 69]] if nm == "piano_sad" else [[81, 76, 72], [77, 76, 72, 69], [79, 76, 74, 72]])
    sp = rng.uniform(0.42, 0.55); parts = [(0, sx_piano(midi(57), 2.6, rng, 0.55), 0.4), (0, sx_piano(midi(64), 2.6, rng, 0.5), 0.3)]
    parts += [(i * sp, sx_piano(midi(n), 2.2, rng, 0.9 - 0.1 * i), 0.55) for i, n in enumerate(phr)]
    return sx_rev(sx_mix(parts), 2.2, 0.35)

@_reg("violin")
def _s_violin(rng, nm):
    a, b = sx_pick(rng, [(76, 72), (76, 74), (79, 76), (74, 69)])
    return sx_rev(sx_mix([(0, sx_string(midi(a), 1.0, rng), 0.5), (0.85, sx_string(midi(b), 1.6, rng), 0.5),
                          (0, sx_string(midi(57), 2.5, rng, 0.003, 0.5), 0.22), (0, sx_string(midi(64), 2.5, rng, 0.003, 0.5), 0.18)]), 2.4, 0.38)

@_reg("musicbox")
def _s_mbox(rng, nm):
    phr = sx_pick(rng, [[81, 76, 72, 71, 69], [84, 81, 76, 77, 76], [76, 81, 79, 76, 72]]); sp = rng.uniform(0.26, 0.32)
    mb = lambda f: sx_bell(f, 1.2, ((1, 1, 3), (3.01, .25, 7), (5.43, .12, 14)))
    return sx_rev(sx_mix([(i * sp + rng.uniform(-0.01, 0.01) + 0.01, mb(midi(n)), 0.5) for i, n in enumerate(phr)]), 1.8, 0.3)

# ----------------------------------------------------------------- DARR / HORROR
@_reg("sting", "screech")
def _s_sting(rng, nm):                       # horror violin cheekh
    sc = nm == "screech"; d = 1.0 if sc else 1.6; t = sx_t(d); base = rng.uniform(86, 90) if sc else rng.uniform(78, 84)
    x = sum(sx_osc(midi(n) * (1 + 0.012 * np.sin(2 * np.pi * rng.uniform(6, 8) * t + rng.uniform(0, 6))) * (1 + (0.04 if sc else 0.015) * t), "saw") for n in (base, base + 1, base + 2.1, base - 0.9))
    x = sx_peaks(sx_hp(sx_lp(x, 7000), 400), [(2800, 1.5, 5)]) * (0.7 + 0.3 * np.sin(2 * np.pi * rng.uniform(10, 14) * t))
    env = np.minimum(1, t / (0.008 if sc else 0.02)) * np.interp(t, [0, 0.15, d * 0.7, d], [1, 0.75, 0.55, 0])
    return sx_rev((x / 4 + sx_un(sx_bp(sx_noise(len(t), rng), 4500, 0.6)) * 0.15) * env, 2.4, 0.4)

@_reg("sting_low")
def _s_sting_low(rng, nm):                   # bhaari darr wala hit
    d = 2.6; t = sx_t(d); r = rng.uniform(31, 36)
    x = sx_lp(sum(sx_osc(midi(n), "saw", len(t)) for n in (r, r + 1, r + 6, r + 12)) / 4, 900) * np.minimum(1, t / 0.015) * np.interp(t, [0, 0.2, 1.8, d], [1, 0.8, 0.5, 0])
    return sx_rev(sx_mix([(0, x, 0.8), (0, _s_impact(rng, "impact_deep"), 0.7)]), 2.6, 0.35)

@_reg("heartbeat", "heart_soft")
def _s_heart(rng, nm):                       # dhak-dhak
    soft = nm == "heart_soft"; per = 60 / (rng.uniform(60, 70) if soft else rng.uniform(68, 80)); parts = []
    def thump(a):
        t = sx_t(0.22)
        y = sx_sat(sx_osc(48 + 30 * np.exp(-t * 30)) * np.exp(-t * 16), 1.6) + sx_un(sx_lp(sx_noise(len(t), rng), 220)) * np.exp(-t * 25) * 0.6
        return y * np.minimum(1, t / 0.004) * a
    for b in range(2 if soft else 3): parts += [(b * per, thump(1.0), 1.0), (b * per + 0.28, thump(0.65), 1.0)]
    x = sx_lp(sx_mix(parts), 500)
    return sx_mix([(0, x, 0.7), (0.05, _s_classic(rng, "chime"), 2.0)]) if soft else x

@_reg("creak")
def _s_creak(rng, nm):                       # darwaza churrr
    d = rng.uniform(1.1, 1.5); n = int(d * SR); t = np.arange(n) / SR
    rate = np.interp(t, [0, d * 0.3, d * 0.6, d], [rng.uniform(25, 40), rng.uniform(110, 150), rng.uniform(60, 90), rng.uniform(30, 45)])
    jit = sx_lp(sx_noise(n, rng), 8); rate = rate * (1 + 0.15 * jit / (np.abs(jit).max() + 1e-9))
    idx = np.where(np.diff(np.floor(np.cumsum(rate) / SR)) > 0)[0]
    imp = np.zeros(n); imp[idx] = rng.uniform(0.6, 1.0, len(idx)) * np.interp(idx / SR, [0, 0.1, d - 0.15, d], [0.3, 1, 1, 0])
    it = sx_t(0.06)
    ir = sum(np.sin(2 * np.pi * f * it) * np.exp(-it * k) for f, k in ((rng.uniform(380, 450), 70), (rng.uniform(800, 900), 90), (rng.uniform(1400, 1600), 120), (rng.uniform(2500, 2900), 160)))
    return sx_rev(sx_conv(imp, ir)[:n], 1.0, 0.2)

@_reg("drone", gain=0.8)
def _s_drone(rng, nm):                       # andhera, bhaari gunjan
    d = 3.2; t = sx_t(d); r = rng.uniform(26, 31)
    x = sum(sx_osc(midi(n) * (1 + 0.003 * np.sin(2 * np.pi * 0.2 * t * (i + 1))), "saw") for i, n in enumerate((r, r + 0.12, r + 7, r + 12.1))) / 4
    x = sx_tv(x, lambda f, tq: 1 / np.sqrt(1 + (f / (250 + 350 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.35 * tq - 1.5)))) ** 4))
    return sx_rev((sx_un(x) + sx_un(sx_bp(sx_noise(len(t), rng), 700, 2)) * 0.12) * np.interp(t, [0, 0.8, d - 0.8, d], [0, 1, 1, 0]), 2.5, 0.3)

@_reg("ghost")
def _s_ghost(rng, nm):                       # bhoot "woooo"
    d = rng.uniform(1.8, 2.3); t = sx_t(d)
    f = np.interp(t, [0, d * 0.35, d * 0.7, d], [rng.uniform(420, 480), rng.uniform(720, 820), rng.uniform(560, 620), rng.uniform(380, 430)]) * (1 + 0.03 * np.sin(2 * np.pi * rng.uniform(4, 5.5) * t))
    x = sx_osc(f) + 0.18 * sx_osc(2 * f) + 0.05 * sx_osc(3 * f)
    return sx_rev((x * 0.6 + sx_un(sx_bp(sx_noise(len(t), rng), 900, 1.5)) * 0.08) * np.interp(t, [0, 0.35, d - 0.6, d], [0, 1, 0.8, 0]), 2.8, 0.5)

@_reg("swell_hit")
def _s_swell(rng, nm):                       # ulta cymbal chadhta hua -> HIT
    d = rng.uniform(0.9, 1.2); t = sx_t(d)
    return sx_mix([(0, sx_cymbal(rng, d, 2.5)[::-1] * (t / d) ** 1.5, 0.8), (d, _s_impact(rng, "impact"), 1.0)]), d

@_reg("toll")
def _s_toll(rng, nm):                        # mandir/church ka bhaari ghanta
    d = 4.0; t = sx_t(d); f = rng.uniform(150, 180)
    x = sum(a * sx_osc(f * k * rng.uniform(0.998, 1.002), n=len(t)) * np.exp(-t * dk) for k, a, dk in ((0.5, .55, 0.35), (1.0, .8, 0.6), (1.19, .55, 0.8), (1.5, .4, 0.9), (2.0, .9, 1.1), (2.52, .3, 1.5), (3.01, .25, 1.8), (4.1, .15, 2.4)))
    return sx_rev((x * 0.4 + sx_un(sx_bp(sx_noise(len(t), rng), 1500, 0.7)) * np.exp(-t * 60) * 0.4) * np.minimum(1, t / 0.002), 2.5, 0.3)

@_reg("wind", gain=0.75)
def _s_wind(rng, nm):                        # sunsaan hawa (tumbleweed)
    d = 2.6; t = sx_t(d); c1 = rng.uniform(0.2, 0.5)
    def fn(f, tq):
        fc = 650 + 300 * np.sin(2 * np.pi * c1 * tq + 1) + 150 * np.sin(2 * np.pi * 1.3 * c1 * tq)
        return 1 / (1 + 40 * (f / fc - fc / np.maximum(f, 1)) ** 2) + 0.08 / np.sqrt(1 + (f / 500) ** 2)
    return sx_un(sx_tv(sx_noise(len(t), rng), fn)) * np.interp(t, [0, 0.7, d - 0.7, d], [0, 1, 1, 0])

# ----------------------------------------------------------------- MYSTERY / SUSPENSE
@_reg("dun_dun", "dun_dun2")
def _s_dun(rng, nm):                         # "dun dun DUNNN"
    r = int(sx_pick(rng, [45, 47, 48])); seq = (r, r, r - 4) if nm == "dun_dun" else (r, r, r - 1); parts = []
    for n, st, d in zip(seq, (0, 0.3, 0.62), (0.22, 0.22, 1.8)):
        parts += [(st, sum(sx_brass(midi(n + o), d, rng, att=0.015) for o in (-12, 0)), 0.45),
                  (st, sx_piano(midi(n), d + 0.6, rng, 0.9) + sx_piano(midi(n - 12), d + 0.6, rng, 0.9), 0.35), (st, sx_timp(rng, midi(n - 12), 1.0), 0.5)]
    return sx_rev(sx_mix(parts), 2.0, 0.3)

@_reg("tick", "tick_fast", gain=0.75)
def _s_tick(rng, nm):                        # ghadi tik-tik
    per = rng.uniform(0.45, 0.55) if nm == "tick" else rng.uniform(0.22, 0.26); n = 5 if nm == "tick" else 8
    def blk(f):
        t = sx_t(0.08)
        return (sx_osc(f, n=len(t)) * np.exp(-t * 90) + 0.5 * sx_osc(f * 1.7, n=len(t)) * np.exp(-t * 140) + sx_un(sx_hp(sx_noise(len(t), rng), 3000)) * np.exp(-t * 400) * 0.4) * np.minimum(1, t / 0.0004)
    hi, lo = rng.uniform(2300, 2700), rng.uniform(1500, 1800)
    return sx_rev(sx_mix([(i * per, blk(hi if i % 2 == 0 else lo), 1.0) for i in range(n)]), 0.6, 0.15)

@_reg("sparkle", gain=0.85)
def _s_sparkle(rng, nm):                     # jaadu ki chamak
    pent = (0, 2, 4, 7, 9); r = int(sx_pick(rng, [79, 81, 84])); sp = rng.uniform(0.035, 0.05)
    notes = [r + pent[i % 5] + 12 * (i // 5) for i in range(int(rng.integers(7, 10)))]
    return sx_rev(sx_mix([(i * sp, sx_bell(midi(n), 0.9, ((1, 1, 5), (2.01, .25, 8), (3.9, .1, 14))) * (0.8 + 0.2 * np.sin(2 * np.pi * 7 * sx_t(0.9))), 0.5) for i, n in enumerate(notes)]), 2.0, 0.45)

@_reg("sneaky")
def _s_sneaky(rng, nm):                      # chupke chupke (pizzicato)
    r = int(sx_pick(rng, [40, 43, 45])); seq = (0, 3, 5, 6, 7, 6, 5, 3)[:int(rng.integers(5, 9))]; sp = rng.uniform(0.17, 0.21)
    return sx_rev(sx_mix([(i * sp, sx_pluck(midi(r + s), 0.5, rng, decay=0.985), 0.7 if i % 2 == 0 else 0.5) for i, s in enumerate(seq)]), 1.0, 0.2)

@_reg("riser")
def _s_riser(rng, nm):                       # tension chadhna (message aate hi khatam)
    d = rng.uniform(1.3, 1.8); t = sx_t(d); u = t / d
    nz = sx_un(sx_tv(sx_noise(len(t), rng), lambda f, tq: 1 / (1 + 3 * (f / (300 * 20 ** np.clip(tq / d, 0, 1)) - (300 * 20 ** np.clip(tq / d, 0, 1)) / np.maximum(f, 1)) ** 2)))
    f = 110 * 8 ** (u ** 1.2); tn = sx_lp(sx_osc(f, "saw") + sx_osc(f * 1.5, "saw") * 0.5, 6000)
    return (nz * 0.6 + sx_un(tn) * 0.35) * u ** 2.2 * np.minimum(1, (d - t) / 0.01), d

@_reg("sonar")
def _s_sonar(rng, nm):
    t = sx_t(0.6); p = sx_osc(rng.uniform(1000, 1300), n=len(t)) * np.minimum(1, t / 0.02) * np.exp(-t * 7)
    return sx_rev(sx_mix([(0, p, 1.0), (rng.uniform(0.9, 1.1), p, 0.35)]), 2.6, 0.5)

@_reg("vibes")
def _s_vibes(rng, nm):                       # "hmm... interesting"
    r = int(sx_pick(rng, [62, 64, 57])); sp = rng.uniform(0.08, 0.11); t = sx_t(2.2)
    vib = lambda f: sx_bell(f, 2.2, ((1, 1, 1.6), (3.9, .25, 6))) * (0.75 + 0.25 * np.sin(2 * np.pi * 5.5 * t))
    return sx_rev(sx_mix([(i * sp, vib(midi(r + c)), 0.5) for i, c in enumerate((0, 3, 7, 10, 14))]), 2.0, 0.35)

# ----------------------------------------------------------------- HYPE / JEET
@_reg("applause", gain=0.85)
def _s_applause(rng, nm):                    # taaliyan + shor
    d = rng.uniform(2.3, 2.9); n = int(d * SR); out = np.zeros(n); ct = sx_t(0.03)
    shapes = [sx_un(sx_bp(sx_noise(len(ct), rng), rng.uniform(900, 2600), rng.uniform(0.8, 1.6))) for _ in range(12)]
    tm = 0.0
    while True:
        tm += rng.exponential(1 / max(5.0, float(np.interp(tm, [0, 0.35, d - 0.9, d], [10, 70, 60, 0]))))
        if tm >= d - 0.03: break
        put(out, shapes[int(rng.integers(12))] * np.exp(-ct * rng.uniform(140, 260)) * np.minimum(1, ct / 0.0008), tm, rng.uniform(0.25, 0.8))
    cheer = sx_un(sx_peaks(sx_bp(sx_noise(n, rng), 1100, 0.5), [(600, 3, 6), (1500, 3, 6), (2600, 3, 4)]))
    am = sx_lp(sx_noise(n, rng), 3); am = 0.7 + 0.3 * am / (np.abs(am).max() + 1e-9)
    return sx_rev(out + cheer * am * np.interp(np.arange(n) / SR, [0, 0.3, d - 1.0, d], [0, 1, 0.8, 0]) * 0.25, 1.0, 0.25)

@_reg("levelup", gain=0.8)
def _s_levelup(rng, nm):                     # game level up
    r = int(sx_pick(rng, [72, 74, 76])); seq = (0, 4, 7, 12, 16, 19, 24); sp = rng.uniform(0.05, 0.06)
    parts = [(i * sp, sx_chip(midi(r + s), sp + 0.01), 0.35) for i, s in enumerate(seq)]
    return sx_mix(parts + [(len(seq) * sp, sx_chip(midi(r + 24), 0.35, vib=0.01, decay=3), 0.35)])

@_reg("coin", gain=0.8)
def _s_coin(rng, nm):
    a, b = (83, 88) if rng.random() < 0.6 else (81, 86)
    return sx_mix([(0, sx_chip(midi(a), 0.075, duty=0.5), 0.35), (0.075, sx_chip(midi(b), 0.45, duty=0.5, decay=7), 0.35)])

@_reg("coins")
def _s_coins(rng, nm):                       # sikke khanakna
    d = 1.0; out = np.zeros(int(d * SR)); t = sx_t(0.2)
    for _ in range(int(rng.integers(14, 22))):
        f = rng.uniform(2800, 5200)
        y = (sx_osc(f, n=len(t)) + 0.6 * sx_osc(f * 1.41, n=len(t)) + 0.3 * sx_osc(f * 2.3, n=len(t))) * np.exp(-t * rng.uniform(18, 35)) * np.minimum(1, t / 0.0005)
        put(out, y, rng.uniform(0, d - 0.25), rng.uniform(0.1, 0.35))
    return sx_rev(out, 0.5, 0.15)

@_reg("cash")
def _s_cash(rng, nm):                        # ka-ching
    t = sx_t(0.12)
    ka = (sx_un(sx_bp(sx_noise(len(t), rng), 1800, 1.0)) * np.exp(-t * 60) + sx_osc(160.0, n=len(t)) * np.exp(-t * 40) * 0.6) * np.minimum(1, t / 0.0005)
    t2 = sx_t(1.3); f = rng.uniform(2400, 2700)
    ching = sum(a * sx_osc(f * k, n=len(t2)) * np.exp(-t2 * dk) for k, a, dk in ((1, 1, 3.5), (1.34, .7, 4), (2.0, .4, 5), (2.68, .3, 6))) * (1 + 0.15 * np.sin(2 * np.pi * 9 * t2)) * np.minimum(1, t2 / 0.001)
    return sx_rev(sx_mix([(0, ka, 0.8), (0.11, ching, 0.35), (0.16, _s_coins(rng, "coins"), 0.6)]), 0.8, 0.15)

@_reg("fireworks")
def _s_fireworks(rng, nm):                   # aatishbazi
    d = rng.uniform(0.7, 0.9); t = sx_t(d); u = t / d
    wh = (sx_osc(700 * 3.2 ** u * (1 + 0.01 * np.sin(2 * np.pi * 9 * t))) * 0.5 + sx_un(sx_bp(sx_noise(len(t), rng), 3000, 1)) * 0.25) * np.minimum(1, t / 0.05) * (0.4 + 0.6 * u)
    tb = sx_t(1.6)
    bang = (sx_un(sx_lp(sx_noise(len(tb), rng), 2500)) * np.exp(-tb * 9) + sx_sat(sx_osc(55 * (1 + 0.8 * np.exp(-tb * 18))) * np.exp(-tb * 5), 2) * 0.8) * np.minimum(1, tb / 0.002)
    cr = np.zeros(int(1.8 * SR))
    for _ in range(int(rng.integers(70, 120))):
        st = 0.15 + rng.exponential(0.35)
        if st > 1.7: continue
        m = int(rng.uniform(0.002, 0.006) * SR); put(cr, sx_hp(sx_noise(m, rng), 3000) * np.exp(-np.arange(m) / (m / 4)), st, rng.uniform(0.1, 0.4))
    return sx_rev(sx_mix([(0, wh, 0.6), (d, bang, 0.9), (d, sx_un(cr), 0.5)]), 1.6, 0.25)

@_reg("power_up", "power_down")
def _s_power(rng, nm):
    up = nm == "power_up"; d = rng.uniform(0.6, 0.8) if up else rng.uniform(1.0, 1.3); t = sx_t(d); u = t / d
    if up: f = 160 * 7 ** (u ** 1.3); tr = 6 + 26 * u; env = np.minimum(1, t / 0.03) * (0.5 + 0.5 * u)
    else: f = 1100 * (55 / 1100) ** (u ** 0.8); tr = 30 - 26 * u; env = np.minimum(1, t / 0.01) * (1 - u) ** 0.6
    return (sx_osc(f) * 0.7 + sx_lp(sx_osc(f, "square"), 3500) * 0.3) * (0.7 + 0.3 * np.sin(2 * np.pi * np.cumsum(tr) / SR)) * env

@_reg("laser")
def _s_laser(rng, nm):                       # pew pew
    parts = []
    for i in range(int(rng.integers(2, 4))):
        d = rng.uniform(0.15, 0.22); t = sx_t(d); f = rng.uniform(1600, 2200) * 0.12 ** (t / d)
        parts.append((i * rng.uniform(0.16, 0.22), (sx_osc(f) * 0.7 + sx_lp(sx_osc(f, "square"), 5000) * 0.3) * np.exp(-t * 6) * np.minimum(1, t / 0.002), 1.0))
    return sx_mix(parts)

@_reg("drumroll")
def _s_drumroll(rng, nm):                    # drum roll... CRASH
    d = rng.uniform(1.4, 1.8); parts, tm = [], 0.0
    while tm < d:
        parts.append((tm, sx_snare(rng, 0.12, rng.uniform(180, 200), 0.8), (0.25 + 0.75 * (tm / d) ** 1.5) * rng.uniform(0.8, 1.0))); tm += rng.uniform(0.038, 0.046)
    return sx_rev(sx_mix(parts + [(d + 0.02, sx_snare(rng, 0.3), 1.2), (d + 0.02, sx_cymbal(rng, 1.6, 2.0), 0.7), (d + 0.02, kick(1.0), 0.6)]), 1.0, 0.18)

# ----------------------------------------------------------------- SURPRISE / SHOCK
@_reg("orch_hit")
def _s_orch(rng, nm):                        # orchestra ka jhatka
    r = int(sx_pick(rng, [48, 50, 53])); d = 0.5; t = sx_t(d)
    x = sum(sx_osc(midi(n) * (1 + 0.003 * v), "saw", len(t)) for n in (r - 12, r, r + 7, r + 12, r + 16, r + 19) for v in (-1, 1)) / 12
    x = sx_peaks(sx_lp(x, 6000), [(900, 1, 3)]) * np.minimum(1, t / 0.004) * np.exp(-t * 5)
    return sx_rev(sx_mix([(0, x, 1.0), (0, sx_timp(rng, midi(r - 12), 1.2), 0.5), (0, sx_cymbal(rng, 1.2, 2.5), 0.25)]), 2.0, 0.35)

@_reg("scratch")
def _s_scratch(rng, nm):                     # record scratch "wikka"
    ts = sx_t(1.5)
    src = sx_lp(sum(sx_osc(midi(n), "saw", len(ts)) for n in (48, 55, 60, 64)) / 4 + sx_un(sx_bp(sx_noise(len(ts), rng), 1200, 0.5)) * 0.5, 5000)
    d = rng.uniform(0.32, 0.4); n = int(d * SR); t = np.arange(n) / SR
    v = np.interp(t, [0, 0.04, 0.12, 0.2, 0.3, d], [1.0, 0.6, -2.4, 2.8, 0.5, 0.0])
    pos = np.clip(0.5 * SR + np.cumsum(v), 0, len(src) - 2)
    y = np.interp(pos, np.arange(len(src)), src) * np.minimum(1, np.abs(v) / 0.3)
    return (y + sx_un(sx_hp(sx_noise(n, rng), 2000)) * 0.15 * np.abs(v) / 3) * np.minimum(1, (d - t) / 0.02)

@_reg("zoom_hit")
def _s_zoom(rng, nm):                        # tezi se paas aana -> DHAM
    d = rng.uniform(0.3, 0.4); t = sx_t(d); u = t / d
    w = sx_un(sx_tv(sx_noise(len(t), rng), lambda f, tq: 1 / (1 + 2 * (f / (400 * 12 ** np.clip(tq / d, 0, 1)) - (400 * 12 ** np.clip(tq / d, 0, 1)) / np.maximum(f, 1)) ** 2))) * u ** 1.5
    return sx_mix([(0, w * 0.6 + sx_osc(200 * 6 ** u) * u ** 2 * 0.3, 1.0), (d, _s_impact(rng, "slam"), 1.0)]), d

@_reg("ding", "ding2", "ding_soft")
def _s_ding(rng, nm):
    if nm == "ding": return sx_rev(sx_bell(midi(int(sx_pick(rng, [88, 91]))), 1.4), 1.2, 0.2)
    if nm == "ding2":                        # sahi jawab: ding-ding
        a = int(sx_pick(rng, [84, 86])); return sx_rev(sx_mix([(0, sx_bell(midi(a), 0.9), 0.8), (0.13, sx_bell(midi(a + 4), 1.2), 0.8)]), 1.0, 0.2)
    return sx_bell(midi(int(sx_pick(rng, [79, 81, 84]))), 0.5, ((1, 1, 7), (4.0, .3, 30)))

@_reg("glitch", gain=0.8)
def _s_glitch(rng, nm):                      # digital gadbad
    out = np.zeros(int(0.6 * SR)); tm = 0.0
    while tm < 0.5:
        d = rng.uniform(0.025, 0.08); n = int(d * SR); k = rng.random()
        if k < 0.35: raw = rng.standard_normal(n); h = int(rng.integers(4, 40)); y = np.repeat(raw[::h], h)[:n] * 0.4
        elif k < 0.7: y = np.sign(np.sin(2 * np.pi * float(sx_pick(rng, [220, 330, 440, 660, 880, 1320])) * np.arange(n) / SR)) * 0.18
        else: g = sx_osc(rng.uniform(300, 2000), "square", int(0.015 * SR)) * 0.2; y = np.tile(g, n // len(g) + 1)[:n]
        put(out, y * np.minimum(1, np.arange(n) / 30), tm); tm += d + rng.uniform(0.0, 0.03)
    return out

# ----------------------------------------------------------------- AWKWARD / CRINGE / FAIL
@_reg("crickets", gain=0.6)
def _s_crickets(rng, nm):                    # jhingur... (sannata)
    d = rng.uniform(2.3, 2.8); n = int(d * SR); out = np.zeros(n); pt = sx_t(0.014)
    for f, per, amp, off in ((rng.uniform(4300, 4800), rng.uniform(0.38, 0.46), 1.0, 0.05), (rng.uniform(3800, 4200), rng.uniform(0.5, 0.6), 0.55, rng.uniform(0.15, 0.3))):
        pulse = np.sin(2 * np.pi * f * pt) * np.sin(np.pi * pt / 0.014) ** 2; tm = off
        while tm < d - 0.12:
            for p in range(int(rng.integers(3, 5))): put(out, pulse, tm + p * 0.024, amp)
            tm += per * rng.uniform(0.92, 1.08)
    return (out + sx_un(sx_lp(sx_noise(n, rng), 400)) * 0.02) * np.interp(np.arange(n) / SR, [0, 0.2, d - 0.4, d], [0, 1, 1, 0])

@_reg("bloop")
def _s_bloop(rng, nm):                       # "bwomp"
    d = rng.uniform(0.28, 0.36); t = sx_t(d); f = rng.uniform(220, 260) * 0.5 ** (t / d * 1.1)
    return (sx_osc(f) + 0.3 * sx_osc(2 * f) + 0.1 * sx_osc(3 * f)) * np.minimum(1, t / 0.01) * np.exp(-t * 5) * np.minimum(1, (d - t) / 0.03)

@_reg("beeps", gain=0.8)
def _s_beeps(rng, nm):                       # robot bleep-bloop
    parts, tm = [], 0.0
    for _ in range(int(rng.integers(7, 12))):
        d = rng.uniform(0.04, 0.09); t = sx_t(d); f = rng.uniform(700, 2600) * (1 + (rng.uniform(-0.5, 0.8) if rng.random() < 0.35 else 0) * t / d)
        y = (sx_osc(f) if rng.random() < 0.6 else sx_lp(sx_osc(f, "square"), 6000) * 0.6) * np.minimum(1, t / 0.003) * np.minimum(1, (d - t) / 0.005)
        parts.append((tm, y, rng.uniform(0.5, 1))); tm += d + rng.uniform(0.01, 0.05)
    return sx_mix(parts)

@_reg("error", gain=0.8)
def _s_error(rng, nm):
    a, b = (880, 587) if rng.random() < 0.5 else (784, 523)
    return sx_mix([(0, sx_lp(sx_chip(a, 0.13, 0.5), 4000), 0.5), (0.14, sx_lp(sx_chip(b, 0.28, 0.5, decay=3), 4000), 0.5)])

# ----------------------------------------------------------------- PYAAR / CUTE
@_reg("harp")
def _s_harp(rng, nm):
    pent = (0, 2, 4, 7, 9); r = int(sx_pick(rng, [60, 62, 65])); sp = rng.uniform(0.035, 0.045)
    return sx_rev(sx_mix([(i * sp, sx_pluck(midi(r + pent[i % 5] + 12 * (i // 5)), 1.6, rng, decay=0.997, bright=0.6), 0.35) for i in range(11)]), 2.2, 0.4)

# ----------------------------------------------------------------- TRANSITION / BATTLE
@_reg("whoosh_fast", "whoosh_deep", "swoosh", "whoosh_air")
def _s_whooshes(rng, nm):
    if nm == "whoosh_fast": return sx_whoosh(rng, rng.uniform(0.25, 0.32), 3500, sharp=True)
    if nm == "whoosh_deep": return sx_whoosh(rng, rng.uniform(0.7, 0.9), 700, deep=True)
    if nm == "whoosh_air": return sx_whoosh(rng, rng.uniform(0.55, 0.7), 1800)
    d = rng.uniform(0.35, 0.45); t = sx_t(d)
    return sx_un(sx_tv(sx_noise(len(t), rng), lambda f, tq: 1 / (1 + 5 * (f / (300 * 14 ** np.clip(tq / d, 0, 1)) - (300 * 14 ** np.clip(tq / d, 0, 1)) / np.maximum(f, 1)) ** 2))) * np.sin(np.pi * t / d) ** 1.4

@_reg("boxing_bell")
def _s_boxbell(rng, nm):                     # fight bell: ding ding ding
    f = rng.uniform(780, 860)
    def strike():
        t = sx_t(2.0)
        x = sum(a * sx_osc(f * k, n=len(t)) * np.exp(-t * dk) for k, a, dk in ((1, 1, 1.4), (2.03, .6, 2.0), (2.76, .5, 2.6), (3.91, .3, 3.5), (5.4, .2, 5)))
        return (x * 0.35 + sx_un(sx_hp(sx_noise(len(t), rng), 3000)) * np.exp(-t * 90) * 0.4) * np.minimum(1, t / 0.0005)
    return sx_rev(sx_mix([(i * 0.19, strike(), 1.0) for i in range(3)]), 1.2, 0.2)

@_reg("vs_hit")
def _s_vs(rng, nm):                          # battle ka "VS" dhamaka
    d = 0.8; t = sx_t(d)
    return sx_mix([(0, sx_cymbal(rng, d, 2.5)[::-1] * (t / d) ** 2, 0.6), (d, _s_impact(rng, "impact_metal"), 1.0)]), d

# ----------------------------------------------------------------- groups: har mood / feel ke liye kai awaazein
SFX_POOLS = {
    "funny":    ["boing", "doing", "slide_up", "slide_down", "honk", "bonk", "rimshot", "pops", "squeak", "xylo_up", "zip", "boing_hi", "boing0"],
    "roast":    ["boom", "airhorn", "burn", "explosion", "slap", "ring", "glass", "bass_drop", "impact_deep", "boom2"],
    "angry":    ["impact", "punch", "growl", "clang", "buzzer", "thunder", "braam", "alarm", "slam", "impact_metal"],
    "sad":      ["piano_sad", "piano_sad2", "violin", "musicbox", "piano_low", "bells_sad"],
    "scary":    ["sting", "sting_low", "heartbeat", "creak", "thunder", "drone", "ghost", "screech", "swell_hit", "toll", "rumble"],
    "mystery":  ["dun_dun", "tick", "sparkle", "sneaky", "riser", "sonar", "vibes", "chime", "dun_dun2"],
    "hype":     ["airhorn", "fanfare", "applause", "levelup", "fireworks", "bass_drop", "power_up", "rise"],
    "surprise": ["orch_hit", "scratch", "zoom_hit", "ding", "glitch", "swell_hit", "boing", "rise"],
    "awkward":  ["crickets", "bloop", "wind", "scratch"],
    "fail":     ["sad_trombone", "buzzer", "fall", "xylo_down", "error", "deflate"],
    "win":      ["ding2", "coin", "levelup", "fanfare", "tada", "applause"],
    "money":    ["cash", "coins", "coin"],
    "love":     ["harp", "chime", "heart_soft"],
    "tech":     ["beeps", "glitch", "error", "power_down"],
    "party":    ["fireworks", "applause", "tada", "airhorn"],
    "sarcastic": ["rimshot", "bloop", "boom2", "scratch", "crickets"],
    "dead":     ["boom", "boom2", "bass_drop", "impact_deep"],
    "clown":    ["honk", "honk2", "squeak", "boing"],
    "blast":    ["explosion", "boom", "bass_drop"],
    "spooky":   ["ghost", "wind", "toll"],
    "time":     ["tick", "tick_fast"],
    "magic":    ["sparkle", "harp", "chime"],
    "bells":    ["ding", "ding2", "boxing_bell"],
    "fight":    ["punch", "slap", "impact"],
    "blade":    ["sword", "clang"],
    "storm":    ["thunder"],
    "launch":   ["power_up", "riser", "fireworks"],
    "oof":      ["bonk", "punch", "slap"],
    "dun":      ["dun_dun", "dun_dun2", "sting_low"],
    "idea":     ["ding", "sparkle"],
    "evil":     ["braam", "sting_low", "toll", "thunder"],
    "transition": ["whoosh", "whoosh_fast", "whoosh_deep", "swoosh", "whoosh_air"],
    "caption":  ["pop2", "swoosh", "ding_soft", "whoosh_fast"],
    "calm":     [],
}
# ye awaazein message padhne / bolne ke BAAD bajti hain (punchline ke baad); baaki message aate hi
SFX_AFTER = {"boing", "doing", "slide_up", "slide_down", "honk", "honk2", "bonk", "rimshot", "pops", "squeak", "xylo_up", "zip", "zip_down",
             "boing_hi", "boing0", "boom", "boom2", "airhorn", "burn", "explosion", "slap", "ring", "glass", "bass_drop", "sad_trombone",
             "deflate", "fall", "xylo_down", "buzzer", "crickets", "bloop", "wind", "applause", "tada", "ding2", "coin", "coins", "cash",
             "fireworks", "dun_dun", "dun_dun2", "drumroll", "laser"}
# keyword / emoji -> group   (tone: comic / bright = khush wale, sad ya darr wale message par nahi lagte)
SFX_TRIGGERS = [(re.compile(rx, re.I), grp, tone) for rx, grp, tone in (
    (r"\U0001F941|\bdrum\s*roll\b", "drumroll", "neutral"),
    (r"\U0001F3A4|\bmic\s*drop\b", "dead", "neutral"),
    (r"\U0001F480|☠|\b(?:i'?m|im) dead\b|\bbruh+\b", "dead", "comic"),
    (r"\bemotional damage\b", "ring", "comic"),
    (r"\U0001F921|\bclowns?\b", "clown", "comic"),
    (r"\U0001F997|\bcrickets?\b|\bawkward\b|\bcringe\b|[\U0001F610\U0001F611\U0001F636\U0001F62C\U0001FAE0]", "awkward", "comic"),
    (r"\U0001F525\s*\U0001F525|\U0001F9EF|\U0001F975|\b(?:roast(?:ed|ing)?|burn(?:ed|t)?|savage|destroyed|cooked|ratio(?:ed)?|rekt|owned|violated)\b", "roast", "comic"),
    (r"[\U0001F4A5\U0001F4A3\U0001F92F]|\b(?:ka)?boom\b|\bexplod\w*|\bmind\s*blown\b|\bdhamaka\b", "blast", "neutral"),
    (r"\U0001F47B|\bghosts?\b|\bbhoot\b|\bhaunted\b", "spooky", "dark"),
    (r"[⏰⏳⌛⏱]|\btick\s*tock\b|\btime'?s up\b|\bhurry\b|\bcountdown\b", "time", "neutral"),
    (r"✨|\U0001FA84|\bmagic\b|\babracadabra\b|\bjaadu\b", "magic", "bright"),
    (r"\U0001F514|\bding\b", "bells", "neutral"),
    (r"[\U0001F4B0\U0001F4B5\U0001F4B8\U0001F911\U0001F4B2]|\$\s?\d|\b(?:money|cash|paisa|paise|rupees?|dollars?|salary|rich)\b", "money", "comic"),
    (r"[❤\U0001F60D\U0001F970\U0001F495\U0001F496\U0001F498\U0001F618\U0001F49E]|\b(?:i love you|crush|pyaa?r|romantic)\b", "love", "bright"),
    (r"\U0001F916|⚠|\b(?:robot|glitch(?:ed)?|error|bug|crash(?:ed)?|reboot|beep|boop|system failure|virus|hack(?:ed|er)?)\b", "tech", "neutral"),
    (r"[❌\U0001F44E]|\b(?:wrong answer|incorrect|fail(?:ed)?|loser|you lose|took the l|game over|epic fail)\b", "fail", "comic"),
    (r"[✅\U0001F3C6\U0001F947\U0001F451\U0001F410\U0001F3AF]|\b(?:correct|right answer|you win|winner|victory|champion|nailed it|goat)\b", "win", "bright"),
    (r"[\U0001F389\U0001F973\U0001F38A\U0001F37E]|\b(?:congrats|congratulations|party|celebrat\w*)\b", "party", "bright"),
    (r"[\U0001F44A\U0001F94A\U0001F91C]|\b(?:punch(?:ed)?|slap(?:ped)?|thappad|knock(?:ed)? out)\b", "fight", "neutral"),
    (r"[⚔\U0001F5E1\U0001F52A]|\b(?:sword|knife|stab(?:bed)?)\b", "blade", "dark"),
    (r"[⚡\U0001F329⛈]|\b(?:thunder|lightning|storm)\b", "storm", "dark"),
    (r"\U0001F680|\b(?:launch(?:ed|ing)?|lift\s?off|to the moon|blast off)\b", "launch", "bright"),
    (r"[\U0001F634\U0001F4A4\U0001F971]|\bzzz+\b|\b(?:boring|bored|sleepy)\b", "awkward", "comic"),
    (r"\U0001F915|\b(?:oof|ouch|ow+)\b", "oof", "comic"),
    (r"\U0001F575|\bplot twist\b|\bdun dun\b|\bsuspense\b", "dun", "dark"),
    (r"\U0001F92B|\bsecret\b|\bshh+\b", "mystery", "dark"),
    (r"[\U0001F9E0\U0001F4A1]|\bgenius\b|\bbig brain\b", "idea", "bright"),
    (r"\U0001F608|\bevil\b|\bvillain\b", "evil", "dark"),
)]
EMO_POOL = {"funny": "funny", "angry": "angry", "shout": "angry", "sad": "sad", "cry": "sad", "scared": "scary", "scary": "scary",
            "mystery": "mystery", "excited": "hype", "surprise": "surprise", "nervous": "awkward", "sarcastic": "sarcastic"}
SFX_NO_TONE = {"comic": ("sad", "cry", "scared", "scary", "angry", "shout"), "bright": ("sad", "cry", "scared", "scary", "angry", "shout")}
BATTLE_COMBOS = [[("vs_hit", 0.0), ("boxing_bell", 0.45)], [("swell_hit", 0.0), ("boxing_bell", 0.5)],
                 [("sword", 0.0), ("braam", 0.3)], [("riser", 0.0), ("impact_metal", 0.0), ("boxing_bell", 0.4)]]

_sfx_cache = {}
def sfx_full(name, var=0):
    """naam -> (awaaz, anchor sec). anchor = awaaz ka wo pal jo message ke saath milna chahiye (jaise riser ka end)"""
    key = (name, var)
    if key in _sfx_cache: return _sfx_cache[key]
    fn = SFX_LIB.get(name)
    if fn is None:
        pool = SFX_POOLS.get(name)
        if pool: return sfx_full(pool[var % len(pool)], var // len(pool))
        return np.zeros(10), 0.0
    r = fn(np.random.default_rng((zlib.crc32(name.encode()) + 7919 * var) & 0xffffffff), name)
    x, anchor = r if isinstance(r, tuple) else (r, 0.0)
    x = np.nan_to_num(np.asarray(x, float))
    if name not in SFX_RAW: x = sx_level(x) * SFX_GAIN.get(name, 1.0)
    _sfx_cache[key] = (x, float(anchor))
    return _sfx_cache[key]

def sfx(name, var=0): return sfx_full(name, var)[0]

TAG_NAMES = sorted(set(MOODS) | set(SFX_POOLS) | {n for n in SFX_LIB if n not in SFX_RAW or n in ("whoosh", "hit", "bell", "pop2")}
                   | set(CUSTOM_SFX) | {"nosfx"}, key=len, reverse=True)
TAG_RE = re.compile(r"\s*\{\s*(%s)\s*\}" % "|".join(map(re.escape, TAG_NAMES)), re.I)

class SfxDJ:
    """group se awaaz chuno: patte ki tarah shuffle, jab tak saari na baj jaayein koi dobara nahi, lagatar same kabhi nahi"""
    def __init__(self, seed):
        self.rng = np.random.default_rng(seed); self.decks, self.uses, self.last = {}, {}, None
    def pool(self, grp):
        if grp in CUSTOM_SFX: return [grp]                       # sounds/funny.mp3 -> sirf tumhari file
        mine = sorted(n for n in CUSTOM_SFX if re.fullmatch(re.escape(grp) + r"[_-]?\w+", n) and n not in SFX_LIB)
        return list(SFX_POOLS.get(grp, [])) + mine               # sounds/funny_2.mp3 -> group me ek aur option
    def pick(self, grp):
        pool = self.pool(grp)
        if not pool: return None
        d = self.decks.get(grp)
        if not d:
            d = [pool[i] for i in self.rng.permutation(len(pool))]
            if len(d) > 1 and d[0] == self.last: d.append(d.pop(0))
            self.decks[grp] = d
        name = d.pop(0); return self.use(name)
    def use(self, name):
        var = self.uses.get(name, 0); self.uses[name] = var + 1; self.last = name
        return name, var

def _sfx_target(k, raw, role, S):
    """message ka feel -> [(group ya awaaz ka naam, khud likha tha?)]"""
    tags = S.get("stags", {}).get(k, [])
    if "nosfx" in tags: return []
    own = [t for t in tags if t not in MOODS and t != "nosfx"]
    if own: return [(t, True) for t in own[:2]]
    tm = [t for t in tags if t in MOODS]
    if tm: return [(tm[-1], True)]
    vtag = S.get("vemo", {}).get(k)
    if vtag and EMO_POOL.get(EMO_ALIAS.get(vtag, "")): return [(EMO_POOL[EMO_ALIAS[vtag]], True)]      # {v:sarcastic} jaisa khud likha
    if not S.get("sfx_auto", True): return []
    emo = pick_emotion(raw, vtag, S["moods"].get(k), role)
    letters = "".join(w for w in re.findall(r"[A-Za-z']+", raw) if w not in ACRONYMS)
    letters = [c for c in letters if c.isalpha()]
    if emo in ("none", "calm") and (re.search(r"!!|\?!|!\?", raw) or (len(letters) >= 8 and sum(c.isupper() for c in letters) / len(letters) > 0.6)):
        emo = "shout"
    for rx, grp, tone in SFX_TRIGGERS:
        if rx.search(raw) and emo not in SFX_NO_TONE.get(tone, ()): return [(grp, False)]
    mood = S["moods"].get(k)
    if mood and mood != "calm": return [(mood, False)]
    grp = EMO_POOL.get(emo)
    return [(grp, False)] if grp else []

def plan_sfx(cfg, S, plan, sh, t0):
    """poori video ke sound effects: [(time, naam, variation, gain, voice ke neeche dabana?)] + voice ke windows"""
    items = {it["k"]: it for it in cfg["items"] if it.get("k") is not None}
    vdur = {int(k): x["dur"] for k, x in (plan.get("voice") or {}).items()} if S["voice"]["on"] else {}
    vs = {int(k): v / 1000 for k, v in (plan.get("vstarts") or {}).items()}
    vwin = [(sh(vs[k]), sh(vs[k]) + d) for k, d in vdur.items() if k in vs]
    log = [dict(e, ts=(e["t"] - t0) / 1000) for e in plan["log"]]
    dj = SfxDJ(zlib.crc32(cfg["name"].encode())); ev = []; last_feel = -9.0
    ev_t = lambda x: sh(x["ts"])
    marks = sorted([ev_t(x) for x in log if x["n"] in ("send", "show", "cmd", "think")] + [sh(a / 1000) for a, _ in plan.get("typing", [])])
    for i, e in enumerate(log):
        nxt = next((m for m in marks if m > ev_t(e) + 0.05), None)          # agla message / typing kab shuru
        if e["n"] == "cmd":
            c = e.get("c"); t_ = sh(e["ts"])
            if c == "intro": ev += [(t_ + 0.02, "whoosh", 0, 1.0, False), (t_ + 0.4, "hit", 0, 1.0, False)]
            elif c in ("caption", "level"): nm, var = dj.pick("caption"); ev.append((t_ + 0.02 - sfx_full(nm, var)[1], nm, var, 0.9, False))
            elif c == "end": ev += [(t_ + 1.5, "subscribe", 0, 1.0, False), (t_ + 1.85, "bell", 0, 1.0, False)]
            continue
        if e["n"] == "think":                            # Battle: naya AI aaya
            t_ = ev_t(e)
            if e.get("first"):
                for nm, off in BATTLE_COMBOS[zlib.crc32(cfg["name"].encode()) % len(BATTLE_COMBOS)]:
                    var = dj.use(nm)[1]; ev.append((t_ + off - sfx_full(nm, var)[1], nm, var, 0.95, False))
            else:
                nm, var = dj.pick("transition"); ev.append((t_ - sfx_full(nm, var)[1], nm, var, 0.8, False))
            continue
        if e["n"] not in ("send", "show"): continue
        k = e.get("k"); it = items.get(k, {}); raw = it.get("raw", ""); role = e.get("role", "user"); t_ = ev_t(e)
        if e["n"] == "send": ev.append((t_, "send", 0, 1.0, False))
        else:
            rv = f"recv_{role}"
            ev.append((t_, rv if (rv in CUSTOM_SFX or rv in SFX_LIB) else "recv", 0, 1.0, False))
        if S.get("vol_sfx", 1) <= 0: continue
        clean = VOICE_TAG_RE.sub("", raw)
        for j, (tgt, mine) in enumerate(_sfx_target(k, clean, role, S)):
            grp = tgt in SFX_POOLS or (tgt in MOODS)
            got = dj.pick(tgt) if grp else dj.use(tgt) if (tgt in SFX_LIB or tgt in CUSTOM_SFX) else None
            if not got: continue
            nm, var = got; x, anc = sfx_full(nm, var) if nm not in CUSTOM_SFX else (None, 0.0)
            after = nm in SFX_AFTER
            if tgt == "funny":                           # "lol / 😂" message ke shuru me = jawab me hasi -> turant
                m = LAUGH_RE.search(clean) or CHUCKLE_RE.search(clean)
                if m and m.start() <= 0.4 * max(1, len(clean)): after = False
            if e["n"] == "send":
                when = t_ + (0.18 if after else 0.02)
            elif after:
                d = vdur.get(k)
                when = t_ + (d + 0.05 if d else min(2.5, max(0.5, 0.35 + len(tts_clean(clean)) / 22)))
                if nxt is not None: when = min(when, nxt - 0.3)
                when = max(when, t_ + 0.25)
            else:
                when = t_ - 0.02
            when = max(0.0, when - (0 if after else anc)) + 0.12 * j
            if not mine and when - last_feel < 0.9: continue        # bahut paas-paas nahi
            ev.append((when, nm, var, 0.85, True)); last_feel = when
    return ev, vwin

_custom_cache = {}
def load_custom(name):
    if name in _custom_cache: return _custom_cache[name]
    x = None
    f = CUSTOM_SFX.get(name)
    if f is not None:
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(f), "-t", str(SFX_MAX_S),
                              "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
        y = np.frombuffer(raw, dtype="<f4").astype(float)
        if len(y) < 64:
            print(f"(sounds/{f.name} padh nahi paaya, built-in awaaz use ho rahi hai)")
        else:
            y = y / (np.abs(y).max() + 1e-9) * SFX_PEAK
            fd = min(len(y) // 4, int(0.03 * SR)); y[-fd:] *= np.linspace(1, 0, fd)
            x = y
    _custom_cache[name] = x
    return x

def get_sfx(name, var=0):
    x = load_custom(name)
    return x if x is not None else sfx(name, var)

def intro_sfx():
    rng = np.random.default_rng(11); out = np.zeros(int((INTRO_S + 0.8) * SR))
    for t0 in (0.05, 0.24, 0.41, 0.53, 0.9, 1.12, 1.31):
        d = rng.uniform(0.03, 0.09); raw = rng.standard_normal(int(d * SR)); hold = int(rng.integers(4, 40))
        crush = np.repeat(raw[::hold], hold)[:len(raw)] * 0.3; put(out, crush, t0)
        sq = np.sign(np.sin(2 * np.pi * float(rng.choice([220, 440, 660, 880])) * tt(d))) * 0.12; put(out, sq, t0)
    t = tt(0.65); sweep = np.sin(2 * np.pi * np.cumsum(200 * 8 ** (t / 0.65)) / SR) * (t / 0.65) * 0.16
    put(out, sweep, 0.9); put(out, sfx("rumble")[:int(2.2 * SR)], 1.55, 0.7)
    return out

KEY_STYLES = ["iphone", "mech", "thock", "bubble", "typewriter", "glass"]

def _hp(x): return np.diff(x, prepend=0)
def _bp(x): return np.convolve(np.diff(x, prepend=0), np.ones(4) / 4, mode="same")
def _lp(x, n): return np.convolve(x, np.ones(n) / n, mode="same")

def _key(style, rng):
    if style == "iphone":
        t = tt(0.05); f = rng.uniform(330, 420)
        v = (np.sin(2 * np.pi * f * t) * np.exp(-t * 140) * 0.9
             + _bp(rng.standard_normal(len(t))) * np.exp(-t * 600) * 0.45
             + np.sin(2 * np.pi * f * 2.3 * t) * np.exp(-t * 260) * 0.35)
    elif style == "mech":
        t = tt(0.09); v = np.zeros(len(t))
        v += (_bp(rng.standard_normal(len(t))) * np.exp(-t * 480) * 0.9 + np.sin(2 * np.pi * rng.uniform(2400, 2900) * t) * np.exp(-t * 800) * 0.30)
        s2 = int(0.012 * SR); tb = t[:len(t) - s2]
        v[s2:] += np.sin(2 * np.pi * rng.uniform(190, 250) * tb) * np.exp(-tb * 85) * 0.9 + _lp(rng.standard_normal(len(tb)), 6) * np.exp(-tb * 220) * 0.6
    elif style == "thock":
        t = tt(0.10); f = 190 * np.exp(-t * 9) + rng.uniform(105, 125)
        v = (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 48) * 1.0
             + _lp(rng.standard_normal(len(t)), 22) * np.exp(-t * 180) * 1.2
             + np.sin(2 * np.pi * rng.uniform(1800, 2300) * t) * np.exp(-t * 800) * 0.12)
    elif style == "bubble":
        t = tt(0.10); f = rng.uniform(340, 420) + rng.uniform(480, 600) * np.exp(-t * 62)
        v = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 42) * np.minimum(1, t / 0.002) + np.sin(2 * np.pi * np.cumsum(2 * f) / SR) * np.exp(-t * 90) * 0.18
    elif style == "typewriter":
        t = tt(0.14)
        v = (_bp(rng.standard_normal(len(t))) * np.exp(-t * 300) * 0.8
             + (np.sin(2 * np.pi * 1450 * t) * np.exp(-t * 95) + np.sin(2 * np.pi * 2210 * t) * np.exp(-t * 140) * 0.7
                + np.sin(2 * np.pi * 3320 * t) * np.exp(-t * 190) * 0.4) * 0.28
             + np.sin(2 * np.pi * rng.uniform(88, 104) * t) * np.exp(-t * 65) * 1.0)
    else:
        t = tt(0.14); f = rng.uniform(2300, 3100)
        v = (_bp(rng.standard_normal(len(t))) * np.exp(-t * 800) * 0.3
             + np.sin(2 * np.pi * f * t) * np.exp(-t * 75) * 0.8 + np.sin(2 * np.pi * f * 1.51 * t) * np.exp(-t * 115) * 0.35
             + np.sin(2 * np.pi * 520 * t) * np.exp(-t * 120) * 0.3)
    v = v / (np.sqrt((v ** 2).mean()) + 1e-9) * 0.11
    v = v / max(1.0, np.abs(v).max() / 0.7)
    return v * rng.uniform(0.88, 1.0)

def norm_style(k):
    k = str(k).lower().strip()
    if k in ("tool", "loop", "custom", "7"):
        if "typing" in CUSTOM_SFX: return "tool"
        print("(keys=tool: sounds/typing.mp3 nahi mili - 'iphone' use kar raha hoon)"); return "iphone"
    if k.isdigit() and 1 <= int(k) <= len(KEY_STYLES): return KEY_STYLES[int(k) - 1]
    if k in KEY_STYLES: return k
    print(f"(keys='{k}' nahi mila, 'iphone' use kar raha hoon. Options: {', '.join(KEY_STYLES)} ya 1-6)")
    return "iphone"

def key_variants(style, n=8, seed=7):
    rng = np.random.default_rng(seed)
    return [_key(style, rng) for _ in range(n)]

def bgm_track(b, seconds, intro_s):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(b["start"]), "-i", b["path"],
                          "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype="<f4").astype(float)
    n = int(seconds * SR)
    if len(x) < SR:
        print("(bgm file se audio nahi mila)")
        return np.zeros(n)
    cf = int(0.4 * SR); y = x.copy()
    while len(y) < n:
        if len(x) > 2 * cf:
            a = y[-cf:] * np.cos(np.linspace(0, np.pi / 2, cf)); c = x[:cf] * np.sin(np.linspace(0, np.pi / 2, cf))
            y = np.concatenate([y[:-cf], a + c, x[cf:]])
        else:
            y = np.concatenate([y, x])
    y = y[:n] / (np.abs(y[:n]).max() + 1e-9); t = np.arange(n) / SR
    fade = np.interp(t, [0, intro_s, intro_s + 1.5, max(seconds - 3.0, intro_s + 1.5), seconds], [0, 0, 1, 1, 0])
    return y * fade * b["vol"]

def duck_env(n, windows, ramp=0.12):
    env = np.ones(n)
    for a, b in windows:
        i0, i1 = max(0, int((a - ramp) * SR)), min(n, int((b + ramp) * SR) + 1)
        if i1 <= i0: continue
        t = np.arange(i0, i1) / SR
        env[i0:i1] = np.minimum(env[i0:i1], np.interp(t, [a - ramp, a, b, b + ramp], [1, 0, 0, 1]))
    return env

def make_audio(clicks_s, events, music_tl, seconds, intro_s, path, vol_click, vol_sfx, vol_music, use_intro, keys="iphone", bgm=None, extra=None, duck=None, spans=None, vduck=None):
    out = np.zeros(int(seconds * SR)); rng = np.random.default_rng(7)
    loop = load_custom("typing") if keys == "tool" else None
    if loop is not None and spans:
        for a, b in spans:
            n = int((b - a) * SR)
            if n <= 0: continue
            seg = np.tile(loop, n // len(loop) + 1)[:n].copy(); fd = min(n // 3, int(0.04 * SR))
            if fd > 0: seg[:fd] *= np.linspace(0, 1, fd); seg[-fd:] *= np.linspace(1, 0, fd)
            put(out, seg, a, vol_click)
    else:
        variants = key_variants(norm_style("iphone" if keys == "tool" else keys))
        for c in clicks_s:
            put(out, variants[int(rng.integers(0, 8))], c, vol_click)
    if vol_sfx > 0:
        cache, fxb = {}, np.zeros(len(out))
        for ev in events:
            tm, name = ev[0], ev[1]; var = ev[2] if len(ev) > 2 else 0; g = ev[3] if len(ev) > 3 else 1.0
            if (name, var) not in cache: cache[(name, var)] = get_sfx(name, var)
            put(fxb if len(ev) > 4 and ev[4] else out, cache[(name, var)], tm, vol_sfx * g)
        if vduck:                    # awaaz ke shuru ka jhatka poora, baaki voice ke neeche aadha
            fxb *= 1 - 0.5 * (1 - duck_env(len(out), [(a + 0.15, b) for a, b in vduck if b > a + 0.15], 0.1))
        out += fxb
        if use_intro == "text":
            put(out, intro_sfx(), 0.0, vol_sfx)
    bed = None
    if bgm:
        bed = bgm_track(bgm, seconds, intro_s)
    elif vol_music > 0:
        bed = music_track(music_tl, seconds, intro_s, vol_music)
    if bed is not None:
        out += bed * duck_env(len(out), duck) if duck else bed
    for st, arr, gain in (extra or []):
        put(out, arr, st, gain)
    out = sx_limit(out)
    pcm = (np.clip(out, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

# ================================================================= INTRO (frames)
INTRO_HTML = """<!doctype html><meta charset=utf-8><style>
html,body{margin:0;height:100%%;background:#04060a;overflow:hidden}
body{display:flex;align-items:center;justify-content:center;flex-direction:column;
 background:radial-gradient(ellipse at center,#0b1018 0%%,#04060a 70%%)}
.scan{position:fixed;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.035) 0 2px,transparent 2px 5px);pointer-events:none}
.w{position:relative;font:800 150px/1 'Roboto Mono','DejaVu Sans Mono',monospace;letter-spacing:.06em;text-transform:uppercase;
 white-space:nowrap;animation:flick %(d)ss steps(1,end) both}
.w span{display:block}
.l1,.l2{position:absolute;left:0;top:0}
.l0{color:#fff}
.l1{color:#00f0ff;mix-blend-mode:screen;animation:g1 %(d)ss steps(1,end) both}
.l2{color:#ff2a6d;mix-blend-mode:screen;animation:g2 %(d)ss steps(1,end) both}
.bar{margin-top:46px;height:6px;background:linear-gradient(90deg,#00f0ff,#ff2a6d);box-shadow:0 0 24px #00f0ff88;
 animation:bar %(d)ss linear both}
.fade{position:fixed;inset:0;background:#000;animation:fade %(d)ss linear both}
@keyframes flick{0%%{opacity:0}2%%{opacity:1}7%%{opacity:0}9%%{opacity:1}15%%{opacity:.2}17%%{opacity:1}30%%{opacity:.6}32%%{opacity:1}100%%{opacity:1}}
@keyframes g1{0%%{transform:translate(-18px,0);clip-path:inset(10%% 0 62%% 0)}6%%{transform:translate(14px,-4px);clip-path:inset(55%% 0 20%% 0)}
 12%%{transform:translate(-9px,3px);clip-path:inset(30%% 0 45%% 0)}19%%{transform:translate(22px,0);clip-path:inset(5%% 0 80%% 0)}
 27%%{transform:translate(-12px,0);clip-path:inset(60%% 0 10%% 0)}34%%{transform:translate(8px,2px);clip-path:inset(20%% 0 55%% 0)}
 42%%{transform:translate(-5px,0);clip-path:inset(40%% 0 40%% 0)}50%%{transform:translate(0,0);clip-path:inset(0 0 100%% 0)}100%%{transform:translate(0,0);clip-path:inset(0 0 100%% 0)}}
@keyframes g2{0%%{transform:translate(16px,2px);clip-path:inset(45%% 0 30%% 0)}6%%{transform:translate(-20px,0);clip-path:inset(8%% 0 70%% 0)}
 12%%{transform:translate(11px,-3px);clip-path:inset(62%% 0 8%% 0)}19%%{transform:translate(-14px,0);clip-path:inset(25%% 0 50%% 0)}
 27%%{transform:translate(19px,0);clip-path:inset(70%% 0 5%% 0)}34%%{transform:translate(-7px,2px);clip-path:inset(12%% 0 66%% 0)}
 42%%{transform:translate(6px,0);clip-path:inset(35%% 0 42%% 0)}50%%{transform:translate(0,0);clip-path:inset(0 0 100%% 0)}100%%{transform:translate(0,0);clip-path:inset(0 0 100%% 0)}}
@keyframes bar{0%%{width:0}20%%{width:0}60%%{width:620px}100%%{width:620px}}
@keyframes fade{0%%{opacity:0}88%%{opacity:0}100%%{opacity:1}}
</style><div class=scan></div>
<div class=w><span class=l0>@@NAME@@</span><span class=l1>@@NAME@@</span><span class=l2>@@NAME@@</span></div>
<div class=bar></div><div class=fade></div>"""

def render_intro(browser, ff, fps, dsf, brand=BRAND):
    bw, bh = (1920, 1080) if W >= H else (1080, 1920)
    page = browser.new_context(viewport={"width": bw, "height": bh}, device_scale_factor=W / bw).new_page()
    brand = (brand or BRAND).strip()[:40]
    fs = max(40, min(150, int((bw - 220) / (0.66 * max(1, len(brand))))))
    esc = brand.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    page.set_content((INTRO_HTML % {"d": INTRO_S}).replace("font:800 150px/1", f"font:800 {fs}px/1").replace("@@NAME@@", esc))
    page.evaluate("document.fonts.ready.then(()=>1)")
    n = int(round(INTRO_S * fps))
    for k in range(n):
        page.evaluate("T=>document.getAnimations().forEach(a=>{a.pause();a.currentTime=T})", k * 1000.0 / fps)
        ff.stdin.write(page.screenshot(type="jpeg", quality=95))
    page.close()
    return n

# ================================================================= RENDER
def start_ffmpeg(out, fps, crf, preset, size):
    return subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
        "-vf", f"scale={size[0]}:{size[1]}:in_range=full:out_range=tv:out_color_matrix=bt709:flags=lanczos,format=yuv420p",
        "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-r", str(fps),
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
        "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)

def open_page(b, cfg):
    global W, H, VW, VH
    W, H = cfg["osize"]; VW, VH = cfg["view"]
    page = b.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=W / VW).new_page()
    page.add_init_script(INIT_JS)
    page.add_init_script("""(ls => {
        try { Object.defineProperty(window, 'indexedDB', {value: undefined, configurable: true}); } catch (e) {}
        try { localStorage.clear(); for (const [k, v] of Object.entries(ls)) localStorage.setItem(k, String(v)); } catch (e) {}
    })(%s)""" % json.dumps(cfg["ls"]))
    page.clock.install(time=0)
    page.goto(find_html(cfg["html"]).as_uri())
    page.add_style_tag(content=PAGE_CSS % cfg["font"])
    page.add_style_tag(content=OVERLAY_CSS)
    page.evaluate("""async () => {
        const fams = ['Inter', 'Roboto', 'Noto Sans'], ws = ['400', '500', '600', '700'];
        try { await Promise.race([Promise.all(fams.flatMap(f => ws.map(w => document.fonts.load(w + ' 16px "' + f + '"', 'Aa😀')))),
                                  new Promise(r => setTimeout(r, 8000))]); } catch (e) {}
        await document.fonts.ready; return 1;
    }""")
    page.evaluate(DRIVER_JS, [cfg["items"], cfg["jsopts"], cfg["ui"]])
    page.evaluate("m => { window.__memes = m; }", {str(k): v for k, v in cfg.get("memes", {}).items()})
    page.evaluate("m => { window.__vdur = m; }", {str(k): v for k, v in cfg.get("vdur", {}).items()})
    page.clock.pause_at(60000)
    t0 = page.evaluate("performance.now()")
    page.evaluate("() => { window.__p = window.__play().then(() => { window.__done = true; }, e => { console.error(e); window.__err = String(e); window.__done = true; }); }")
    return page, t0

def dry_run(cfg):
    from playwright.sync_api import sync_playwright
    fps = cfg["fps"]; step = 1000.0 / fps
    gaps = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=LAUNCH_ARGS)
        page, t0 = open_page(b, cfg)
        ck, g, prev, tail, max_frames = 0, 0, 0, None, fps * 60 * 25
        while True:
            done, hold, hold_t = page.evaluate("[window.__done, window.__hold || 0, window.__holdT || 0]")
            g += 1                                    # chat frame ck
            if hold:
                G = clip_frames(meme_path(hold), fps)
                gaps.append(dict(ck=ck, g=g, G=G, meme=int(hold), t=hold_t))
                g += G
                page.evaluate("window.__release()")
            if done and tail is None:
                tail = ck + 1 + fps
            if (tail is not None and ck + 1 >= tail) or ck + 1 >= max_frames:
                break
            ck += 1
            target = round(ck * step)
            page.clock.run_for(target - prev); prev = target
        clicks = [c - t0 for c in page.evaluate("window.__clicks")]
        log = page.evaluate("window.__ev || []")
        typing = [[a - t0, (e if e is not None else a) - t0] for a, e in page.evaluate("window.__typing || []")]
        vstarts = {str(k): v - t0 for k, v in page.evaluate("window.__vstarts || {}").items()}
        err = page.evaluate("window.__err || ''")
        if err: print(f"(page error: {err})", flush=True)
        b.close()
    return ck + 1, gaps, t0, clicks, log, vstarts, typing

def segment_task(t):
    from playwright.sync_api import sync_playwright
    global W, H
    W, H = t["osize"]
    fps = t["fps"]; step = 1000.0 / fps; size = out_size()
    ff = start_ffmpeg(t["out"], fps, t["crf"], t["preset"], size)
    with sync_playwright() as p:
        b = p.chromium.launch(args=LAUNCH_ARGS)
        if t["kind"] == "intro":
            render_intro(b, ff, fps, t["dsf"], t.get("brand", BRAND))
        elif t["kind"] in ("introvid", "endvid"):
            for jpg in video_frames(t["clip"], fps, 0, t["n"], size):
                ff.stdin.write(jpg)
        else:
            page, _ = open_page(b, t)
            f0, f1, t_start = t["f0"], t["f1"], time.time()
            gaps = {x["ck"]: x for x in t.get("gaps", [])}
            g, ck, prev = 0, 0, 0
            while g < f1:
                hold = page.evaluate("([T, s]) => window.__sync(T, s)", [ck * step, step])
                if g >= f0:
                    ff.stdin.write(page.screenshot(type="jpeg", quality=95))
                    n = g - f0 + 1
                    if n % (fps * 5) == 0:
                        print(f"[{t['name']}] part {t['idx']}: {n}/{f1 - f0} frames ({n/(time.time()-t_start):.1f} f/s)", flush=True)
                g += 1
                if hold:
                    gp = gaps.get(ck)
                    if gp is None or gp["g"] != g:
                        sys.exit(f"meme gap plan se match nahi hua (ck={ck}) - plan dobara banao")
                    a, e = g, g + gp["G"]
                    lo, hi = max(a, f0), min(e, f1)
                    if hi > lo:
                        for jpg in video_frames(meme_path(gp["meme"]), fps, lo - a, hi - a, size):
                            ff.stdin.write(jpg)
                    g = e
                    page.evaluate("window.__release()")
                if g < f1:
                    ck += 1
                    target = round(ck * step)
                    page.clock.run_for(target - prev); prev = target
        b.close()
    ff.stdin.close(); ff.wait()
    if ff.returncode:
        sys.exit("ffmpeg fail ho gaya")
    return t["out"]

def find_bgm(opts):
    name = opts.get("bgm")
    if not name or str(name).lower() in ("off", "no", "0", "false"): return None
    vol = float(opts.get("bgm_vol", 0.12)); start = float(opts.get("bgm_start", 0))
    for p in (MUSIC_DIR / name, HERE / name):
        if p.is_file(): return dict(path=str(p), start=start, vol=vol)
    f = find_media(MUSIC_DIR, Path(name).stem, SFX_EXT)
    if f: return dict(path=str(f), start=start, vol=vol)
    print(f"(bgm '{name}' nahi mili - music/ folder me upload karo. Abhi built-in music use ho raha hai)")
    return None

EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF\u2190-\u21FF\u2300-\u23FF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200B-\u200F\u2060]")

def tts_clean(t):
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"https?://\S+", " ", t)
    t = EMOJI_RE.sub(" ", t)
    t = re.sub(r"[*`]+", "", t)
    t = re.sub(r"[_#>~|]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

# ================================================================= VOICE + EMOTION (free: edge-tts + jugaad)
# Microsoft ki free awaaz me "angry / cheerful" style allowed nahi hai, isliye insaani emotion yahan banaya jaata hai:
#   - har sentence ki speed / pitch / volume emotion ke hisaab se; gussa / excitement sentence dar sentence chadhta hai
#   - shabd par zor (CAPS, *shabd*, "so / never / worst ..."), sad / darr me shabdon ke beech ruk-ruk ke bolna,
#     darr / nervous me hakla ke bolna ("w-w-what"), sarcasm / sad me aakhri shabd khinch ke
#   - saans: sentences ke beech saans lena, gusse me jhallahat ki "hhh", rone me sisakiyan + naak sudakna,
#     sad me aah, darr / surprise me saans kheenchna, funny me hasi (usi awaaz se bani)
#   - awaaz par effect: gussa = kadak + bhaari, sad / darr = saans bhari kaanpti awaaz, scary = gunj, whisper = phusphusahat
# Script me khud bhi bata sakte ho: {v:angry} {v:funny} {v:sad} {v:cry} {v:scared} {v:scary} {v:shout} {v:whisper} {v:excited}
#   {v:surprise} {v:nervous} {v:sarcastic} {v:calm} {v:normal}   (ye tag screen par nahi dikhta)
VOICE_TAG_RE = re.compile(r"\s*\{\s*(?:v|voice)\s*:\s*([a-z_]+)\s*\}", re.I)
LAUGH_RE = re.compile(r"(?i)(?<![a-z])(?:a?ha(?:\s?ha)+h?|l+o+l+(?:o+l+)*|lmf?ao+|rofl(?:mao)?|bwa+h?a+(?:ha)*h?|m[wu]a+h?a*(?:ha)+h?)(?![a-z])|[\U0001F602\U0001F923\U0001F606\U0001F639\U0001F480]")
CHUCKLE_RE = re.compile(r"(?i)(?<![a-z])(?:he(?:\s?he)+h?|heh|hi(?:\s?hi)+|hee(?:\s?hee)+|tee\s?hee|x+d+)(?![a-z])|[\U0001F605\U0001F60F\U0001F61C\U0001F61D\U0001F92D]")
SIGH_RE = re.compile(r"(?i)\*?(?<![a-z])(?:sigh+s?|uff+|ugh+)(?![a-z])\*?|\U0001F62E‍\U0001F4A8|[\U0001F614\U0001F61E\U0001F629\U0001F97A\U0001F613]")
GASP_RE = re.compile(r"(?i)(?<![a-z])(?:omg|oh my god|oh my gosh|no way|wait what|whoa+)(?![a-z])|[\U0001F631\U0001F628\U0001F632\U0001F92F\U0001F633]|\U0001F62E(?!‍)")
CRY_RE = re.compile(r"[\U0001F62D\U0001F622]")
def has_voice_cue(t): return any(r.search(t) for r in (LAUGH_RE, CHUCKLE_RE, SIGH_RE))
SENT_RE = re.compile(r"[^.!?…]+(?:[.!?…]+|$)")
EMO_ALIAS = {"funny": "funny", "laugh": "funny", "haha": "funny", "angry": "angry", "gussa": "angry", "shout": "shout", "chilla": "shout",
             "sad": "sad", "cry": "cry", "rona": "cry", "scared": "scared", "darr": "scared", "dar": "scared", "fear": "scared",
             "scary": "scary", "horror": "scary", "eerie": "scary", "mystery": "mystery", "hype": "excited", "excited": "excited",
             "khush": "excited", "happy": "excited", "surprise": "surprise", "shock": "surprise", "whisper": "whisper",
             "nervous": "nervous", "sarcastic": "sarcastic", "calm": "calm", "normal": "none", "none": "none", "off": "none"}
MOOD_EMO = {"funny": "funny", "angry": "angry", "sad": "sad", "scary": "scary", "mystery": "mystery", "hype": "excited", "surprise": "surprise", "calm": "calm"}
#             rate %, pitch (semitone), volume %, saans-bhari awaaz (0-1), awaaz par effect (ffmpeg)
EMO = {
    "none":      (0, 0.0, 0, 0.0, ""),
    "calm":      (-6, -0.5, -6, 0.08, "lowpass=f=7000"),
    "funny":     (10, 2.0, 8, 0.0, "equalizer=f=3400:t=q:w=1.2:g=3"),
    "excited":   (18, 3.0, 22, 0.0, "equalizer=f=3000:t=q:w=1:g=4,acompressor=threshold=0.14:ratio=3.5:attack=5:release=100:makeup=2.2"),
    "surprise":  (8, 3.5, 12, 0.05, "equalizer=f=3000:t=q:w=1:g=3"),
    "angry":     (14, 1.0, 35, 0.0, "highpass=f=100,equalizer=f=2800:t=q:w=1.2:g=6,acompressor=threshold=0.1:ratio=6:attack=3:release=70:makeup=3,asoftclip=type=tanh"),
    "shout":     (8, 3.0, 55, 0.0, "highpass=f=120,equalizer=f=2600:t=q:w=1.1:g=8,acompressor=threshold=0.08:ratio=8:attack=2:release=60:makeup=3.5,asoftclip=type=tanh"),
    "sad":       (-22, -2.0, -15, 0.28, "lowpass=f=3400,vibrato=f=5.5:d=0.18"),
    "cry":       (-18, 1.2, -12, 0.32, "lowpass=f=3300,vibrato=f=6.5:d=0.4,tremolo=f=5:d=0.35"),
    "scared":    (8, 1.8, -6, 0.30, "vibrato=f=7.5:d=0.25"),
    "scary":     (-18, -2.5, -10, 0.22, "lowpass=f=3000,aecho=0.8:0.6:70|160:0.3|0.18"),
    "mystery":   (-12, -1.2, -6, 0.12, "aecho=0.8:0.55:90:0.22"),
    "whisper":   (-6, -0.5, -30, 1.0, "highpass=f=250"),
    "nervous":   (16, 1.5, -6, 0.15, "vibrato=f=7.5:d=0.15"),
    "sarcastic": (-14, -1.0, 0, 0.0, ""),
}
SLOW_EMO = ("sad", "cry", "scary", "mystery", "sarcastic", "calm")
FAST_EMO = ("excited", "angry", "shout", "funny", "nervous", "scared")
SPLIT_EMO = ("angry", "shout", "excited")            # har sentence alag bolo taaki emotion chadhta jaaye
#            sentences ke beech saans: (kitni baar, kitni zor se)
BREATH = {"angry": (0.8, 0.5), "shout": (0.9, 0.6), "excited": (0.8, 0.5), "scared": (1.0, 0.6), "sad": (0.7, 0.35), "cry": (1.0, 0.45),
          "nervous": (0.9, 0.5), "scary": (0.6, 0.3), "surprise": (0.6, 0.4), "funny": (0.3, 0.3), "none": (0.35, 0.25),
          "calm": (0.3, 0.2), "mystery": (0.5, 0.3), "whisper": (0.7, 0.35), "sarcastic": (0.3, 0.25)}
INTENSIFIERS = {"so", "really", "very", "never", "ever", "worst", "best", "hate", "love", "stop", "seriously", "literally", "totally", "always",
                "nothing", "everything", "everyone", "nobody", "no", "what", "why", "how", "dare", "insane", "crazy", "amazing", "terrible",
                "horrible", "awesome", "huge", "biggest", "obviously", "absolutely", "completely", "done", "enough", "now", "right", "sure", "great"}
ACRONYMS = {"AI", "GPT", "USA", "UK", "OK", "TV", "ID", "FBI", "CIA", "NASA", "CEO", "DM", "PC", "IQ", "NYC", "LA", "EU", "UN", "PM", "AM",
            "CPU", "GPU", "API", "URL", "HTML", "CSS", "JS", "X", "I", "A", "UFO", "DNA", "VR", "AR", "GTA", "NBA", "NFL"}
MALE_VOICES = ("Guy", "Davis", "Jason", "Tony", "Brandon", "Christopher", "Eric", "Roger", "Steffan", "Andrew", "Brian", "Jacob", "Ryan",
               "Thomas", "William", "Liam", "Prabhat", "Connor", "Luke", "Madhur", "Ken", "Mitchell", "Wayne", "Sam", "Elliot", "Duncan")
SLANG = {"omg": "oh my god", "omfg": "oh my god", "idk": "I don't know", "tbh": "to be honest", "ngl": "not gonna lie", "btw": "by the way",
         "imo": "in my opinion", "imho": "in my honest opinion", "rn": "right now", "smh": "shaking my head", "brb": "be right back",
         "pls": "please", "plz": "please", "thx": "thanks", "ty": "thank you", "np": "no problem", "fr": "for real", "wtf": "what the heck",
         "wth": "what the heck", "nvm": "never mind", "ikr": "I know right", "irl": "in real life", "afk": "away from keyboard",
         "gg": "good game", "dm": "D M", "asap": "as soon as possible", "jk": "just kidding", "ofc": "of course", "u": "you", "ur": "your", "r": "are"}
SLANG_RE = re.compile(r"(?i)(?<![\w'])(" + "|".join(sorted(map(re.escape, SLANG), key=len, reverse=True)) + r")(?![\w'])")

def pick_emotion(raw, vtag, mood, role="user"):
    if vtag: e = EMO_ALIAS.get(vtag.lower(), "none")
    else:
        e = MOOD_EMO.get(mood, "none")
        if CRY_RE.search(raw) and e in ("none", "sad", "calm"): e = "cry"
        if e == "none":
            if LAUGH_RE.search(raw) or CHUCKLE_RE.search(raw): e = "funny"
            elif SIGH_RE.search(raw): e = "sad"
            elif GASP_RE.search(raw): e = "surprise"
    if e == "scary" and role == "user" and not vtag: e = "scared"      # user darta hai, AI daraata hai
    return e

def emphasis_words(raw):
    """jin shabdon par zor dena hai: CAPS wale (acronym nahi) aur *shabd* / **shabd** / _shabd_"""
    out = {w.lower() for w in re.findall(r"\b([A-Z][A-Z']+)\b", raw) if w not in ACRONYMS and len(w) >= 2}
    out |= {w.lower() for w in re.findall(r"[*_]{1,2}([A-Za-z']+)[*_]{1,2}", raw)}
    return {re.sub(r"[^a-z']", "", w) for w in out}

def _tweak(t, e):
    """text ki chhoti tricks taaki neural awaaz khud bhi emotion me bole"""
    t = SLANG_RE.sub(lambda m: SLANG[m.group(1).lower()], t)
    t = re.sub(r"\b([A-Z][A-Z']{1,})\b", lambda m: m.group(1) if m.group(1) in ACRONYMS else m.group(1).lower(), t)   # CAPS spell na hon
    if e in ("excited", "angry", "shout"):
        t = re.sub(r"\.+$", "!", t) if re.search(r"[.!?]$", t) else t + "!"
    elif e in ("sad", "cry"):
        t = re.sub(r",\s*", "... ", t.replace("!", "."))
        if not re.search(r"[.!?]$", t): t += "..."
    elif e in ("scary", "mystery"):
        t = re.sub(r",\s*", "... ", t); t = re.sub(r"(?<!\.)\.$", "...", t)
    return t[:1].upper() + t[1:] if t else t

def say_chunks(text, emo):
    out = []
    for sent in SENT_RE.findall(text):
        t = tts_clean(sent)
        if not re.search(r"\w", t): continue
        letters = [c for c in t if c.isalpha()]
        caps = len(letters) >= 4 and sum(c.isupper() for c in letters) / len(letters) > 0.7
        loud = caps or bool(re.search(r"!!|\?!|!\?", sent))
        e = emo
        if loud and e in ("none", "angry", "calm", "sarcastic"): e, loud = "shout", False
        if GASP_RE.search(sent): out.append(("gasp", "", e, False))
        out.append(("say", _tweak(t, e), e, loud))
    return out

def voice_plan(raw, emo, strength=1.0, rng=None):
    """message -> [(kind, text, emotion, loud)]  kind: say / laugh / chuckle / sigh / gasp / huff / sniffle / breath"""
    rng = rng or np.random.default_rng(1)
    marks, last = [], -1
    for s, e_, kind in sorted([(m.start(), m.end(), kd) for rx, kd in ((SIGH_RE, "sigh"), (LAUGH_RE, "laugh"), (CHUCKLE_RE, "chuckle"))
                               for m in rx.finditer(raw)]):
        if s >= last: marks.append((s, e_, kind)); last = e_
    mm = []                                              # "Hahaha 🤣" / "lol 😂" = ek hi hasi (poori cue se style)
    for s, e_, kind in marks:
        if mm and kind != "sigh" and mm[-1][2] != "sigh" and not re.search(r"[A-Za-z0-9]", raw[mm[-1][1]:s]):
            mm[-1] = (mm[-1][0], e_, "laugh" if "laugh" in (kind, mm[-1][2]) else "chuckle"); continue
        mm.append((s, e_, kind))
    marks = mm
    out, pos = [], 0
    for s, e_, kind in marks:
        out += say_chunks(raw[pos:s], emo); out.append((kind, raw[s:e_], emo, False)); pos = e_
    out += say_chunks(raw[pos:], emo)
    if emo == "none" and any(x[0] == "say" and x[2] == "shout" for x in out):            # chillane wala baaki bhi gusse me
        out = [("say", _tweak(x[1], "angry"), "angry", x[3]) if x[0] == "say" and x[2] == "none" else x for x in out]
        emo = "angry"
    merged = []
    for seg in out:
        if merged and seg[0] != "say" and merged[-1][0] == seg[0]: continue
        if (merged and seg[0] == "say" and merged[-1][0] == "say" and merged[-1][2:] == seg[2:] and seg[2] not in SPLIT_EMO):
            merged[-1] = ("say", merged[-1][1] + " " + seg[1], seg[2], seg[3]); continue
        merged.append(seg)
    seen = set()
    for i, seg in enumerate(merged):                 # har cue (hasi / aah / gasp) ek message me ek hi baar
        if seg[0] != "say":
            if seg[0] in seen or (seg[0] == "chuckle" and "laugh" in seen) or (seg[0] == "laugh" and "chuckle" in seen): merged[i] = None
            seen.add(seg[0])
    merged = [x for x in merged if x]
    if strength >= 0.8 and any(x[0] == "say" for x in merged):     # emotion ke hisaab se apne aap aawaazein
        kinds = {x[0] for x in merged}
        lead = lambda k: merged.insert(0, (k, "", emo, False))
        if emo == "funny" and not ({"laugh", "chuckle"} & kinds): merged.append(("chuckle", "", emo, False))
        elif emo == "angry" and "huff" not in kinds: lead("huff")
        elif emo == "sad" and "sigh" not in kinds: lead("sigh")
        elif emo == "cry": lead("sniffle")
        elif emo in ("surprise", "scared") and "gasp" not in kinds: lead("gasp")
        elif emo in ("excited", "whisper", "shout"): lead("breath")
        elif emo == "nervous" and not ({"laugh", "chuckle"} & kinds) and rng.random() < 0.5: merged.append(("chuckle", "", emo, False))
    return merged

def _prosody(sp, e, loud, strength, rng, step=0):
    dr, dst, dv = EMO.get(e, EMO["none"])[:3]
    if loud: dr, dst, dv = dr + 4, dst + 0.8, dv + 18
    if e in SPLIT_EMO and step: dst, dv = dst + min(1.2, 0.4 * step), dv + min(18, 6 * step)      # chadhta hua gussa
    st = dst * strength + rng.uniform(-0.3, 0.3)
    f0 = 120 if any(nm in sp["voice"] for nm in MALE_VOICES) else 210
    rate = int(sp["rate"][:-1]) + round(dr * strength + rng.uniform(-2.5, 2.5))
    hz = int(sp["pitch"][:-2]) + round(f0 * (2 ** (st / 12) - 1))
    vol = round(dv * strength)
    rate, hz, vol = max(-60, min(100, rate)), max(-80, min(90, hz)), max(-80, min(100, vol))
    return f"{rate:+d}%", f"{vol:+d}%", f"{hz:+d}Hz"

def _decode(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype="<f4").astype(float)

def _trim2(x, keep=0.02):
    """aage-peeche ki khamoshi hatao -> (audio, kitne sample aage se kate)"""
    if len(x) == 0: return x, 0
    thr = max(0.012, np.abs(x).max() * 0.04)
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx): return x[:0], 0
    a, b = max(0, idx[0] - int(keep * SR)), min(len(x), idx[-1] + int(keep * 2 * SR))
    y = x[a:b].copy(); f = min(len(y) // 4, int(0.008 * SR))
    if f > 1: y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y, a

def _trim(x, keep=0.02): return _trim2(x, keep)[0]

_fx_warned = set()
def _fx(x, chain, keep_len=True):
    if not chain or len(x) < 64: return x
    pad = np.concatenate([x, np.zeros(int(0.35 * SR))]) if "aecho" in chain else x
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", chain,
                        "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"], input=pad.astype("<f4").tobytes(), capture_output=True)
    if p.returncode or len(p.stdout) < 64:
        if chain not in _fx_warned:
            _fx_warned.add(chain); print(f"(voice effect nahi chala, bina effect: {chain[:40]} {p.stderr[-120:]!r})", flush=True)
        return x
    y = np.frombuffer(p.stdout, dtype="<f4").astype(float)
    if "aecho" in chain: return _trim(y)
    return y[:len(x)] if keep_len else y

def _bandnoise(n, rng, centre, width):
    F = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR)
    y = np.fft.irfft(F * np.exp(-((f - centre) / width) ** 2), n); return y / (np.abs(y).max() + 1e-9)

def _rms(x): return float(np.sqrt((x ** 2).mean())) + 1e-9 if len(x) else 1e-9

def _whisper(x, rng):
    n = len(x)
    if n < 256: return x
    w = int(0.012 * SR); env = np.convolve(np.abs(x), np.ones(w) / w, mode="same")
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X[f < 450] = 0; hp = np.fft.irfft(X, n)
    y = 0.3 * hp + 2.4 * (_bandnoise(n, rng, 3600, 2200)) * env
    return y * (_rms(x) * 0.8 / _rms(y))

def _breathy(x, rng, r):
    """saans-bhari awaaz: asli awaaz + uski phusphusahat mila do"""
    if r >= 0.99: return _whisper(x, rng)
    if r <= 0 or len(x) < 256: return x
    return x * (1 - 0.45 * r) + _whisper(x, rng) * r

def _shape(n, a, rel):
    t = np.arange(n) / SR; T = n / SR
    env = np.where(t < a * T, (t / max(a * T, 1e-4)) ** 1.3, np.exp(-rel * (t - a * T)))
    f = min(n // 3, int(0.006 * SR))
    if f > 1: env[-f:] *= np.linspace(1, 0, f)
    return env

def _nv(kind, rng, ref, amt=1.0):
    """bina shabd wali insaani aawaazein: saans, aah, jhallahat, sisaki, naak sudakna"""
    if kind == "breath":      # saans andar lena
        n = int(rng.uniform(0.22, 0.34) * SR); y = (_bandnoise(n, rng, 1600, 1000) + 0.4 * _bandnoise(n, rng, 600, 300)) * _shape(n, 0.75, 18); lv = 0.5
    elif kind == "sigh":      # aah... (lambi saans bahar)
        n = int(rng.uniform(0.62, 0.8) * SR); y = (_bandnoise(n, rng, 900, 600) + 0.3 * _bandnoise(n, rng, 2400, 900)) * _shape(n, 0.18, 2.6); lv = 0.55
    elif kind == "gasp":      # saans kheenchna
        n = int(rng.uniform(0.26, 0.34) * SR); y = _bandnoise(n, rng, 2200, 1100) * _shape(n, 0.97, 30); lv = 0.6
    elif kind == "huff":      # gusse wali "hhh"
        n = int(rng.uniform(0.16, 0.22) * SR); y = _bandnoise(n, rng, 700, 450) * _shape(n, 0.07, 14); lv = 0.75
    elif kind == "sniffle":   # naak sudakna
        parts = []
        for _ in range(2):
            m = int(rng.uniform(0.045, 0.065) * SR); parts += [_bandnoise(m, rng, 3500, 1500) * _shape(m, 0.5, 40), np.zeros(int(0.07 * SR))]
        y = np.concatenate(parts); lv = 0.4
    elif kind == "sob":       # sisaki: tez tez chhoti saansein
        parts = []
        for _ in range(int(rng.integers(2, 4))):
            m = int(rng.uniform(0.06, 0.09) * SR); parts += [_bandnoise(m, rng, 1800, 900) * _shape(m, 0.8, 30), np.zeros(int(0.035 * SR))]
        y = np.concatenate(parts); lv = 0.55
    else:
        return np.zeros(0)
    return y * (ref * lv * amt / _rms(y))

def _speed(x, k):
    if len(x) < 4 or abs(k - 1) < 1e-3: return x
    return np.interp(np.arange(0, len(x) - 1, k), np.arange(len(x)), x)

def _syllables(x):
    """'Ha ha ha' ko alag alag 'ha' me kaato"""
    if len(x) < 64: return [x]
    w = int(0.02 * SR); env = np.sqrt(np.convolve(x ** 2, np.ones(w) / w, mode="same"))
    on = env > env.max() * 0.18
    segs, s = [], None
    for i, v in enumerate(on):
        if v and s is None: s = i
        if not v and s is not None:
            if i - s > int(0.06 * SR): segs.append(x[max(0, s - w // 2):i + w // 2])
            s = None
    if s is not None and len(x) - s > int(0.06 * SR): segs.append(x[s:])
    return segs or [x]

def _laugh(syl, rng, ref, big=True):
    if not syl: return np.zeros(1)
    pat = ([(0, 1.0, 1.0), (1, 0.9, 1.06), (2, 0.8, 1.1), (1, 0.68, 1.12), (2, 0.55, 1.15), (1, 0.42, 1.18)] if big else [(0, 0.72, 1.04), (1, 0.56, 1.08)])
    if big and rng.random() < 0.4: pat = pat[:5]
    parts = []
    for i, g, k in pat:
        y = _speed(syl[i % len(syl)][: int(0.26 * SR)], k * rng.uniform(0.96, 1.04)) * g
        f = min(len(y) // 3, int(0.03 * SR))
        if f > 1: y[-f:] *= np.linspace(1, 0, f)
        parts += [y, np.zeros(int(rng.uniform(0.028, 0.055) * SR))]
    y = _breathy(np.concatenate(parts), rng, 0.18)
    if big: y = np.concatenate([y, np.zeros(int(0.04 * SR)), _nv("breath", rng, ref, 0.8)])      # hasi ke baad saans
    return y

# ---- asli jaisi hasi: TTS ki awaaz se ek-ek "ha" lekar, insaani hasi ke rhythm / pitch me dobara banana
#   (har "ha" ~80ms, pehle "h" ki saans, pitch upar se girta, har ha thoda dheema + halka, aakhir me saans andar)
LAUGH_SRC = {"ha": ("Ha! Hah! Ha!", 4.0, 10), "lo": ("Hah! Ha! Hah!", -3.0, -8), "heh": ("Heh! Heh!", 0.5, 5), "hee": ("Hee! Hee!", 6.0, 10)}
#              src    calls   IOI shuru/aakhir  vowel shuru/aakhir  pitch  girna  andar  zor-ghate  saans shuru/aakhir  inhale  zor
LAUGH_STYLE = {
    "intense":   ("ha",  (7, 9), (0.175, 0.235), (0.085, 0.06), 1.5, 0.45, -2.2, 0.88, (0.25, 0.8), 1.0, 1.0),
    "big":       ("ha",  (5, 7), (0.185, 0.23), (0.09, 0.065), 1.0, 0.5, -2.0, 0.86, (0.2, 0.55), 0.8, 0.95),
    "med":       ("ha",  (3, 4), (0.19, 0.22), (0.085, 0.07), 0.5, 0.6, -1.8, 0.82, (0.2, 0.45), 0.3, 0.85),
    "chuckle":   ("heh", (2, 3), (0.17, 0.19), (0.06, 0.05), 0.0, 0.8, -1.5, 0.75, (0.45, 0.65), 0.0, 0.62),
    "giggle":    ("hee", (4, 6), (0.14, 0.165), (0.055, 0.045), 0.8, 0.35, -1.2, 0.86, (0.3, 0.5), 0.35, 0.72),
    "nervous":   ("heh", (2, 2), (0.30, 0.34), (0.06, 0.05), 0.0, 1.0, -1.5, 0.7, (0.5, 0.7), 0.0, 0.55),
    "sarcastic": ("ha",  (2, 2), (0.42, 0.45), (0.11, 0.10), -3.5, 0.25, -0.6, 0.95, (0.1, 0.12), 0.0, 0.8),
    "evil":      ("lo",  (5, 6), (0.27, 0.25), (0.15, 0.12), 0.0, 0.25, -1.0, 0.93, (0.1, 0.25), 0.6, 1.0),
    "wheeze":    ("ha",  (3, 4), (0.16, 0.18), (0.07, 0.06), 2.0, 0.3, -1.5, 0.85, (0.85, 0.95), 1.0, 0.7),
}

def laugh_style(kind, cue, emo, rng):
    """kaun si hasi: 😂 / hahaha = badi, 🤣 / lmao = zor ki, lol / haha = normal, heh = chuckle, hehe = giggle, 😅 = nervous,
    mwahaha = villain, 💀 = saans wali, sarcasm me "ha. ha." """
    c = (cue or "").lower()
    if re.search(r"m[wu]a+h?a|bwa+h?a", c) or (kind == "laugh" and emo in ("scary", "mystery")): return "evil"
    if "\U0001F480" in c: return "wheeze"
    if emo == "sarcastic": return "sarcastic"
    if emo in ("nervous", "scared") or "\U0001F605" in c: return "nervous"
    if kind == "chuckle":
        if not c: return "chuckle" if rng.random() < 0.55 else "med"
        return "chuckle" if (c.strip() == "heh" or "\U0001F60F" in c) else "giggle"
    if re.search("lmf?ao|rofl|\U0001F923", c) or c.count("ha") >= 4: return "intense"
    if re.search("[\U0001F602\U0001F606\U0001F639]", c) or c.count("ha") >= 3: return "big"
    return "med"

def _f0_track(x, fmin=75, fmax=700, frame=0.032, hop=0.005):
    """har 5ms par pitch (Hz), kitni sur-wali (0-1) aur zor"""
    n, h = int(frame * SR), int(hop * SR)
    if len(x) < n + h: return np.zeros(0), np.zeros(0), np.zeros(0)
    nf = 1 + (len(x) - n) // h
    w = np.hanning(n); fr = x[np.arange(n)[None, :] + h * np.arange(nf)[:, None]] * w
    ac = np.fft.irfft(np.abs(np.fft.rfft(fr, 2 * n, axis=1)) ** 2, axis=1)[:, :n]
    wac = np.fft.irfft(np.abs(np.fft.rfft(w, 2 * n)) ** 2)[:n]
    lo, hi = int(SR / fmax), min(n - 2, int(SR / fmin))
    r = ac[:, lo:hi] / (ac[:, :1] + 1e-12) / (wac[lo:hi] / wac[0])
    lag, vv = np.zeros(nf), np.zeros(nf)
    for i in range(nf):
        j = int(np.where(r[i] >= 0.88 * r[i].max())[0][0])          # pehla uncha peak (octave galti se bacho)
        while j + 1 < r.shape[1] and r[i, j + 1] > r[i, j]: j += 1
        dd = 0.0
        if 0 < j < r.shape[1] - 1:
            a, b, c = r[i, j - 1], r[i, j], r[i, j + 1]; dd = (a - c) / (2 * (a - 2 * b + c) - 1e-12) if (a - 2 * b + c) else 0.0
        lag[i], vv[i] = lo + j + max(-0.5, min(0.5, dd)), r[i, j]
    return SR / lag, np.clip(vv, 0, 1), np.sqrt((fr ** 2).mean(1))

def _pitch_marks(seg, fr, h):
    pos = np.arange(len(fr)) * h + h / 2
    Pf = lambda i: SR / float(np.interp(i, pos, fr))
    P0 = Pf(0); m = int(np.argmax(seg[:int(min(len(seg), P0 * 1.3))])); marks = [m]
    while True:
        P = Pf(marks[-1]); c = int(round(marks[-1] + P)); r = max(2, int(P * 0.18))
        if c + r >= len(seg): break
        marks.append(c - r + int(np.argmax(seg[c - r:c + r])))
    marks = np.array(marks)
    if len(marks) < 3: return marks, np.full(len(marks), P0)
    d = np.diff(marks).astype(float)
    return marks, np.concatenate([[d[0]], (d[:-1] + d[1:]) / 2, [d[-1]]])

def _psola(seg, marks, per, f_fn, n_out, k=1.0):
    """awaaz ko naye pitch f_fn(t) par le jao, aawaz ka rang (formant) wahi rehta hai"""
    y = np.zeros(n_out + 4096); pos = float(marks[0])
    while pos < n_out:
        tin = pos * k; i = int(np.searchsorted(marks, tin))
        if i >= len(marks): i = len(marks) - 1
        elif i > 0 and tin - marks[i - 1] < marks[i] - tin: i -= 1
        p, m = max(8, int(per[i])), int(marks[i])
        a, b = max(0, m - p), min(len(seg), m + p)
        g = seg[a:b] * np.hanning(2 * p + 2)[1:-1][a - (m - p):a - (m - p) + (b - a)]
        pout = SR / max(40.0, f_fn(pos / SR)); s0 = int(round(pos)) - (m - a)
        if s0 >= 0: y[s0:s0 + len(g)] += g * min(1.0, pout / p)
        pos += pout
    return y[:n_out]

def _env_noise(nuc, n, rng, bright=0.0):
    """usi vowel jaisi 'hhh' saans: noise ko awaaz ke formant (spectral envelope) se filter"""
    N = 2048; seg = nuc[:N]
    if len(seg) < N: seg = np.pad(seg, (0, N - len(seg)))
    S = np.abs(np.fft.rfft(seg * np.hanning(N))) + 1e-7
    c = np.fft.irfft(np.log(S)); L = int(0.0022 * SR); c[L:N - L] = 0
    env, f = np.exp(np.fft.rfft(c).real), np.fft.rfftfreq(N, 1 / SR)
    M = 1 << max(11, int(np.ceil(np.log2(n + 1)))); fz = np.fft.rfftfreq(M, 1 / SR)
    E = np.interp(fz, f, env) / np.sqrt(1 + (400 / np.maximum(fz, 1)) ** 4) * (1 + bright * np.clip(fz / 4000, 0, 2))
    y = np.fft.irfft(np.fft.rfft(rng.standard_normal(M)) * E, M)[:n]
    return y / (np.sqrt((y ** 2).mean()) + 1e-9)

def _laugh_nuclei(x):
    """TTS ki 'Ha! Hah! Ha!' se har 'ha' ka sur-wala hissa (pitch marks ke saath)"""
    f0, v, e = _f0_track(x)
    if not len(f0): return []
    h, n = int(0.005 * SR), int(0.032 * SR)
    ok = (v > 0.55) & (e > 0.1 * e.max()) & (f0 > 75) & (f0 < 700)
    out, i = [], 0
    while i < len(ok):
        if not ok[i]: i += 1; continue
        j = i
        while j < len(ok) and ok[j]: j += 1
        if j - i >= 7:
            a = i * h + n // 2 - h // 2; b = (j - 1) * h + n // 2 + h // 2
            seg, fr = x[a:b].copy(), f0[i:j]; fm = float(np.median(fr))
            marks, per = _pitch_marks(seg, np.clip(fr, fm / 1.5, fm * 1.5), h)
            if len(marks) >= 4: out.append(dict(x=seg, marks=marks, per=per, f0=fm))
        i = j
    return out

def _laugh_call(nuc, f_start, glide, vd, asp_d, br, rng, voiced=1.0):
    """ek 'ha' = [h ki saans][chhota vowel, girta pitch][peeche halki saans] -> (awaaz, vowel kahan se shuru)"""
    jr, jp = rng.uniform(8, 14), rng.uniform(0, 6.28)
    f_fn = lambda tq: f_start * 2 ** (glide * min(1.0, tq / max(vd, 1e-3)) / 12) * (1 + 0.012 * np.sin(2 * np.pi * jr * tq + jp))
    nv = int((vd + 0.03) * SR)
    v = _psola(nuc["x"], nuc["marks"], nuc["per"], f_fn, nv)
    v = v / (np.sqrt((v[:max(1, int(vd * SR))] ** 2).mean()) + 1e-9)
    tv = np.arange(nv) / SR
    v = v * np.minimum(1, tv / 0.006) * np.interp(tv, [0, vd * 0.35, vd, vd + 0.03], [1.0, 0.95, 0.65, 0.0])
    na, nt = int(asp_d * SR), int(0.04 * SR); tot = na + nv + nt; ta = np.arange(tot) / SR
    y = _env_noise(nuc["x"], tot, rng, 0.15) * np.interp(ta, [0, 0.004, asp_d, asp_d + 0.01, asp_d + vd, tot / SR],
                                                         [0, 0.45, 0.38, br * 0.42, br * 0.38, 0]) * 0.9
    y[na:na + nv] += v * voiced
    return y, na

def _laugh2(src, style, rng, ref):
    nucs = _laugh_nuclei(src)
    if not nucs: return None
    sk, (n0, n1), (i0, i1), (v0, v1), st0, drop, glide, dec, (b0, b1), p_in, gain = LAUGH_STYLE[style]
    fsrc = float(np.median([u["f0"] for u in nucs]))
    nucs = [u for u in nucs if abs(np.log2(u["f0"] / fsrc)) < 0.45] or nucs          # galat pitch wale tukde hatao
    y = np.zeros(int(8 * SR)); mask = np.zeros(len(y), bool)
    def place(arr, at, vs=None, vn=0):
        s = max(0, int(at * SR)); e = min(len(y), s + len(arr)); y[s:e] += arr[:e - s]
        if vs is not None: mask[s + vs:min(len(y), s + vs + vn)] = True
    def bout(n_calls, t, st_base, g0, br_add=0.0):
        last = t
        for i in range(n_calls):
            u = i / max(1, n_calls - 1)
            ioi = (i0 + (i1 - i0) * u) * rng.uniform(0.94, 1.06); vd = (v0 + (v1 - v0) * u) * rng.uniform(0.9, 1.1)
            br = min(1.0, b0 + (b1 - b0) * u + br_add); gl = glide
            st = st_base + (0.5 * min(i, 2) - 0.35 * max(0, i - 2) if style == "evil" else -drop * i) + rng.uniform(-0.35, 0.35)
            if style == "evil" and i == n_calls - 1: vd, gl = 0.42, -4.0
            vo = 0.18 if style == "wheeze" else (0.65 if style == "intense" and u > 0.75 else 1.0)
            asp = rng.uniform(0.03, 0.05) * (1.3 if style in ("chuckle", "nervous", "wheeze") else 0.8 if style == "giggle" else 1.0)
            nuc = nucs[int(rng.integers(len(nucs)))]
            call, na = _laugh_call(nuc, fsrc * 2 ** (st / 12), gl, vd, asp, br, rng, vo)
            place(call * g0 * dec ** i * rng.uniform(0.9, 1.08), t - na / SR, na, int(vd * SR))
            last = t + vd + 0.07; t += ioi
        return last
    end = bout(int(rng.integers(n0, n1 + 1)), 0.07, st0, 1.0)
    if rng.random() < p_in:                         # hasi ke baad saans andar
        d = rng.uniform(0.28, 0.36) if style in ("intense", "wheeze") else rng.uniform(0.2, 0.28); n = int(d * SR); t = np.arange(n) / SR
        place(_env_noise(nucs[0]["x"], n, rng, 1.0) * np.interp(t, [0, d * 0.75, d], [0, 1, 0]) ** 1.5 * 0.22, end + 0.05); end += 0.05 + d
        if style == "intense" and rng.random() < 0.55:       # ek aur chhoti hasi
            end = bout(int(rng.integers(2, 4)), end + 0.08, st0 - 1.5, 0.55, 0.15)
    y = y[:int((end + 0.04) * SR)]
    if not mask[:len(y)].any(): return None
    y = y * (ref * 1.25 * gain / (np.sqrt((y[mask[:len(y)]] ** 2).mean()) + 1e-9))
    if style == "evil": y = _fx(y, "aecho=0.8:0.7:90|200:0.32|0.2")
    return y

def _snap(x, i, win=0.06):
    """i ke aas-paas sabse shaant jagah (shabdon ke beech) dhundo"""
    n = len(x); a, b = max(0, i - int(win * SR)), min(n, i + int(win * SR))
    if b - a < 64: return max(0, min(n, i))
    w = int(0.008 * SR); seg = x[a:b] ** 2
    e = np.convolve(seg, np.ones(w) / w, mode="same")
    return a + int(np.argmin(e))

def _word_edit(x, words, e, emph, rng, strength, ref):
    """shabdon ke time (edge-tts WordBoundary) se: zor, ruk-ruk ke, hakla ke, khinch ke"""
    n = len(x)
    if not words or n < 512 or strength < 0.4: return x
    spans = [(max(0, int(s * SR)), min(n, int(t * SR)), w) for s, t, w in words if t > s and s * SR < n]
    if not spans: return x
    # 1) shabd par zor
    db = {"angry": 5.5, "shout": 4.5, "excited": 4.5, "funny": 3.0, "surprise": 3.5, "sarcastic": 4.0}.get(e, 2.5)
    strong = e in ("angry", "shout", "excited", "sarcastic", "surprise", "funny")
    g = np.ones(n); r = int(0.015 * SR)
    for a, b, w in spans:
        key = re.sub(r"[^a-z']", "", w.lower())
        if key and (key in emph or (strong and key in INTENSIFIERS)):
            a2, b2 = max(0, a - int(0.02 * SR)), min(n, b + int(0.03 * SR))
            env = np.ones(b2 - a2)
            if len(env) > 2 * r: env[:r] = np.linspace(0, 1, r); env[-r:] = np.linspace(1, 0, r)
            g[a2:b2] = np.maximum(g[a2:b2], 1 + (10 ** (db * min(1.5, strength) / 20) - 1) * env)
    x = x * g
    # 2) aakhri shabd khinch ke (sarcasm / sad)
    if e in ("sarcastic", "sad", "cry") and len(spans) >= 2:
        a, b, w = spans[-1]
        a2 = _snap(x, a); b2 = min(n, b + int(0.06 * SR))
        if b2 - a2 > int(0.12 * SR):
            k = {"sarcastic": 0.7, "sad": 0.8, "cry": 0.78}[e] ** min(1.4, max(0.5, strength))
            x = np.concatenate([x[:a2], _fx(x[a2:b2], f"atempo={max(0.5, k):.3f}", keep_len=False)]); n = len(x)
    # 3) ruk-ruk ke bolna (sad / cry / darr / nervous) + sisakiyan
    ins = {}
    p = {"sad": 0.28, "cry": 0.32, "scared": 0.22, "nervous": 0.3, "scary": 0.2}.get(e, 0) * min(1.3, strength)
    if p and len(spans) >= 4:
        last_i = -9
        for i in range(1, len(spans) - 1):
            if i - last_i >= 2 and rng.random() < p and spans[i][0] < n:
                c = _snap(x, spans[i][0]); last_i = i
                if e == "cry" and rng.random() < 0.5: ins[c] = np.concatenate([np.zeros(int(0.05 * SR)), _nv("sob", rng, ref, 0.8), np.zeros(int(0.04 * SR))])
                else: ins[c] = np.zeros(int(rng.uniform(0.09, 0.22) * SR))
    # 4) hakla ke (darr / nervous): "w-w-what"
    if e in ("nervous", "scared") and strength >= 0.7:
        a, b, w = spans[0]
        if b - a > int(0.12 * SR) and w[:1].isalpha():
            a2 = _snap(x, a, 0.04); piece = x[a2:a2 + int(rng.uniform(0.07, 0.1) * SR)].copy()
            f = min(len(piece) // 3, int(0.012 * SR))
            if f > 1: piece[-f:] *= np.linspace(1, 0, f)
            rep = [piece, np.zeros(int(0.045 * SR))] * (2 if rng.random() < 0.5 else 1)
            ins[a2] = np.concatenate([ins.get(a2, np.zeros(0))] + rep)
    if not ins: return x
    out, last = [], 0
    for c in sorted(ins):
        out += [x[last:c], ins[c]]; last = c
    out.append(x[last:])
    return np.concatenate(out)

def _gap(prev_text, e):
    g = 0.36 if prev_text.endswith(("...", "…")) else 0.25 if prev_text.endswith("?") else 0.2 if prev_text.endswith("!") else 0.22 if prev_text.endswith(".") else 0.16
    return g * (1.35 if e in SLOW_EMO else 0.75 if e in FAST_EMO else 1.0)

def gen_voice(S, out_dir):
    """har message ki awaaz (edge-tts, free) + emotion -> {k: {file, dur}}"""
    v = S["voice"]
    if not v["on"] or not S["vtexts"]: return {}
    try:
        import asyncio, edge_tts
    except ImportError:
        print("(voice: edge-tts install nahi hai - bina voice ke render hoga)"); return {}
    import hashlib
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True); tmp = out_dir / ".tts"; tmp.mkdir(exist_ok=True)
    strength = max(0.0, min(2.0, float(v.get("emo", 1.0))))
    # ---- jo voice free service me nahi hai (sirf paid Azure me hoti hai) uski jagah usi jaisi doosri
    FALLBACK = {"Davis": "en-US-ChristopherNeural", "Tony": "en-US-EricNeural", "Jason": "en-US-BrianNeural", "Brandon": "en-US-AndrewNeural",
                "Jacob": "en-US-RogerNeural", "Sara": "en-US-AvaNeural", "Nancy": "en-US-MichelleNeural", "Jane": "en-US-EmmaNeural",
                "Amber": "en-US-AriaNeural", "Ashley": "en-US-EmmaNeural", "Cora": "en-US-MichelleNeural", "Elizabeth": "en-US-JennyNeural",
                "Monica": "en-US-AriaNeural"}
    try:
        avail = {x["ShortName"] for x in asyncio.run(edge_tts.list_voices())}
    except Exception as e:
        avail = set(); print(f"(voice list nahi mili, check skip: {str(e)[:80]})", flush=True)
    if avail:
        for who in ("user", "ai", "chatgpt", "gemini", "grok", "claude"):
            sp = v.get(who)
            if not sp or sp["voice"] in avail: continue
            nm = re.sub(r"^[a-z]{2}-[A-Z]{2}-|(Multilingual)?Neural$", "", sp["voice"])
            alt = FALLBACK.get(nm) or ("en-US-GuyNeural" if any(m in sp["voice"] for m in MALE_VOICES) else "en-US-JennyNeural")
            if alt not in avail: alt = "en-US-GuyNeural" if "en-US-GuyNeural" in avail else sorted(avail)[0]
            print(f"(voice {sp['voice']} free service me nahi hai -> {alt} use ho rahi hai)", flush=True)
            v[who] = dict(sp, voice=alt)
    # ---- har message ka plan (emotion + tukde)
    plans, jobs = {}, {}
    def job(text, sp, rate, vol, pitch):
        key = hashlib.md5(f"{sp['voice']}|{rate}|{vol}|{pitch}|{text}".encode()).hexdigest()[:16]
        jobs[key] = (text, sp["voice"], rate, vol, pitch); return key
    for k, (role, raw) in S["vtexts"].items():
        sp = v.get(role) or v["ai"]
        rng = np.random.default_rng(1000 + k)
        emo = pick_emotion(raw, S.get("vemo", {}).get(k), S["moods"].get(k), role) if strength > 0 else "none"
        segs = voice_plan(raw, emo, strength, rng) if strength > 0 else [("say", tts_clean(raw), "none", False)]
        steps, step_i = [], 0
        for kind, text, e, loud in segs:
            if kind == "say":
                rate, vol, pitch = _prosody(sp, e, loud, strength, rng, step_i) if strength > 0 else (sp["rate"], "+0%", sp["pitch"])
                steps.append(("say", job(text, sp, rate, vol, pitch), text, e, loud)); step_i += 1
            elif kind in ("laugh", "chuckle"):
                style = laugh_style(kind, text, e, rng)
                ltxt, lst, lrt = LAUGH_SRC[LAUGH_STYLE[style][0]]
                f0b = 120 if any(nm in sp["voice"] for nm in MALE_VOICES) else 210
                rate = f"{max(-50, min(80, int(sp['rate'][:-1]) + lrt)):+d}%"
                pitch = f"{max(-80, min(90, int(sp['pitch'][:-2]) + round(f0b * (2 ** (lst / 12) - 1)))):+d}Hz"
                steps.append((kind, job(ltxt, sp, rate, "+10%", pitch), style, e, False))
            else:
                steps.append((kind, None, "", e, False))
        plain = job(tts_clean(raw), sp, sp["rate"], "+0%", sp["pitch"]) if re.search(r"\w", tts_clean(raw)) else None
        plans[k] = (role, emo, steps, plain, emphasis_words(raw))
    # ---- saari TTS ek saath (4-4 karke), shabdon ke time ke saath, dobara koshish ke saath
    got = {}
    async def one(sem, key):
        text, voice, rate, vol, pitch = jobs[key]; path = tmp / f"{key}.mp3"
        for attempt in range(4):
            try:
                async with sem:
                    try: com = edge_tts.Communicate(text, voice, rate=rate, volume=vol, pitch=pitch, boundary="WordBoundary")
                    except TypeError: com = edge_tts.Communicate(text, voice, rate=rate, volume=vol, pitch=pitch)
                    audio, words = bytearray(), []
                    async for ch in com.stream():
                        if ch.get("type") == "audio": audio += ch["data"]
                        elif ch.get("type") == "WordBoundary":
                            words.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, str(ch.get("text", ""))))
                if len(audio) > 300:
                    path.write_bytes(bytes(audio)); return key, path, words
            except Exception as e:
                print(f"(voice '{text[:30]}': koshish {attempt + 1} fail: {str(e)[:90]})", flush=True)
            await asyncio.sleep(1.5 * (attempt + 1))
        return key, None, []
    async def run(keys):
        sem = asyncio.Semaphore(4)
        return await asyncio.gather(*[one(sem, kk) for kk in keys])
    def load(key, path, words):
        y, cut = _trim2(_decode(path))
        got[key] = (y, [(s - cut / SR, t - cut / SR, w) for s, t, w in words])
    needed = {s[1] for _, _, st, _, _ in plans.values() for s in st if s[1]}
    nwords = 0
    for key, path, words in asyncio.run(run(sorted(needed))):
        if path: load(key, path, words); nwords += len(words)
    # ---- har message jodo
    out = {}
    for k, (role, emo, steps, plain, emph) in plans.items():
        rng = np.random.default_rng(5000 + k)
        if any(s[1] and s[1] not in got and s[0] == "say" for s in steps):      # koi tukda nahi bana -> seedhi awaaz
            if plain and plain not in got:
                r = asyncio.run(run([plain]))[0]
                if r[1]: load(*r)
            steps = [("say", plain, "", "none", False)] if plain in got else []
        speech = [got[s[1]][0] for s in steps if s[0] == "say" and s[1] in got and len(got[s[1]][0])]
        ref = float(np.mean([_rms(x) for x in speech])) if speech else 0.08
        parts, prev, used, n_say = [np.zeros(int(0.03 * SR))], None, [], 0
        for kind, key, text, e, loud in steps:
            if kind == "say":
                if key not in got or not len(got[key][0]): continue
                x, words = got[key]
                if strength > 0:
                    x = _word_edit(x, words, e, emph, rng, strength, ref)
                    x = _breathy(x, rng, EMO.get(e, EMO["none"])[3] * min(1.0, strength) if e != "whisper" else 1.0)
                    fx = EMO.get(e, EMO["none"])[4] if strength >= 0.5 else ""
                    x = _fx(x, fx)
                    if loud and "acompressor" not in fx: x = _fx(x, "acompressor=threshold=0.15:ratio=3:attack=5:release=90:makeup=2")
                if prev is not None:
                    g = _gap(prev, e); bp, bl = BREATH.get(e, BREATH["none"])
                    if strength > 0 and rng.random() < bp * min(1.0, strength):
                        nv = _nv("sob" if e == "cry" else "breath", rng, ref, bl * min(1.4, strength) / 0.5)
                        parts += [np.zeros(int(max(0.03, g - len(nv) / SR - 0.05) * SR)), nv, np.zeros(int(0.05 * SR))]
                    else:
                        parts.append(np.zeros(int(g * SR)))
                parts.append(x); prev = text or "."; n_say += 1; used.append(e + ("!" if loud else ""))
            elif kind in ("laugh", "chuckle"):
                if key not in got: continue
                try: lg = _laugh2(got[key][0], text, rng, ref)
                except Exception as ex: print(f"(hasi: naya tareeka fail, purana use: {ex})", flush=True); lg = None
                if lg is None: lg = _laugh(_syllables(got[key][0]), rng, ref, kind == "laugh")
                parts += [np.zeros(int(0.06 * SR)), lg, np.zeros(int(0.06 * SR))]; prev = None; used.append(f"{kind}:{text}")
            else:
                nv = _nv(kind, rng, ref, min(1.4, max(0.6, strength)))
                if len(nv):
                    pre = 0.04 if kind in ("gasp", "huff") else 0.0
                    post = {"sigh": 0.12, "gasp": 0.07, "huff": 0.06, "sniffle": 0.1, "breath": 0.05}.get(kind, 0.08)
                    parts += [np.zeros(int(pre * SR)), nv, np.zeros(int(post * SR))]; prev = None; used.append(kind)
        if not n_say and not any(u in ("laugh", "chuckle") for u in used): continue
        y = np.concatenate(parts)
        if len(y) < int(0.2 * SR): continue
        y = np.concatenate([y, np.zeros(int(0.05 * SR))])
        pk = np.abs(y).max()
        if pk > 0.97: y = np.tanh(y / pk * 1.4) / np.tanh(1.4) * 0.97
        path = out_dir / f"{k}.wav"
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())
        out[k] = dict(file=path.name, dur=round(len(y) / SR, 3))
        print(f"[voice] msg {k} ({role}): {emo} -> {' + '.join(used) or '-'} ({len(y) / SR:.1f}s)", flush=True)
    import shutil; shutil.rmtree(tmp, ignore_errors=True)
    print(f"[voice] {len(out)}/{len(S['vtexts'])} message ki awaaz ban gayi (emotion {'off' if strength == 0 else strength}, "
          f"shabd-time {'mila' if nwords else 'nahi mila'})", flush=True)
    return out

QUALITY = {"4k": 2160, "2160p": 2160, "2k": 1440, "1440p": 1440, "1080p": 1080, "720p": 720}
TRUE = ("on", "yes", "1", "true")

def load_ui(ratio="16:9"):
    """ui/auto.json (screenshots se bane topbar/footer ke size) -> ui/settings.json (tool se Sync) +
    topbar/footer images (9:16 me pehle *_916 wali) + message images"""
    tall, ls, saved = ratio == "9:16", {}, {}
    def read(name):
        f = UI_DIR / name
        if not f.is_file(): return {}
        try:
            return {str(k): str(v) for k, v in json.loads(f.read_text(encoding="utf-8")).items() if v is not None}
        except Exception as e:
            print(f"(ui/{name} padh nahi paaya: {e})"); return {}
    ls.update(read("auto_916.json") if tall and (UI_DIR / "auto_916.json").is_file() else read("auto.json"))
    ls.update(read("settings.json"))
    got = scan_media(UI_DIR, IMG_EXT)
    for key in UI_KEYS:
        v = (got.get(key + "_916") if tall else None) or got.get(key.lower())
        if v: saved[key] = materialize(next(iter(v.values()))).resolve().as_uri()
    def numbered(folder):
        arr = {}
        for stem, v in scan_media(folder, IMG_EXT).items():
            if stem.isdigit(): arr[int(stem)] = materialize(next(iter(v.values()))).resolve().as_uri()
        return [arr.get(i) for i in range(1, max(arr) + 1)] if arr else []
    return ls, dict(saved=saved, user=numbered(UIMG_DIR), ai=numbered(AIMG_DIR))

def settings(script, a):
    global W, H, VW, VH
    items, opts, moods, memes, vraw, vemo, stags = parse_script(script)
    if not any(x.get("k") is not None for x in items): sys.exit(f"{script}: script me koi message nahi mila (User: / ChatGPT: / Gemini: / Grok: / Claude:)")
    off = lambda k, d="on": str(opts.get(k, d)).lower() in ("off", "no", "0", "false")
    on = lambda k, d="off": str(opts.get(k, d)).lower() in TRUE
    fl = lambda k, d: float(opts[k]) if re.fullmatch(r"\d+(\.\d+)?", str(opts.get(k, ""))) else d
    # ---- size: ratio + quality
    ratio = str(opts.get("ratio", "16:9")).lower()
    if ratio not in ("16:9", "9:16", "full"): print(f"(ratio='{ratio}' samajh nahi aaya, 16:9 use ho raha hai)"); ratio = "16:9"
    q = str(opts.get("quality", "")).lower()
    short = QUALITY.get(q) or int(round(1080 * a.dsf / 2)) // 2 * 2
    if q and q not in QUALITY: print(f"(quality='{q}' samajh nahi aayi. Options: 4k, 2k, 1080p, 720p)")
    base = 720 if ratio == "9:16" else 342       # 16:9 / full = phone preview jaisa (tool 608x342 par chalta hai)
    vh = fl("view", 0) or base / max(0.3, min(3.0, fl("ui", 100) / 100))
    vh = int(round(max(180, min(1400, vh))))
    if ratio == "9:16":
        W, H = short, int(round(short * 16 / 9)) // 2 * 2; VW, VH = int(round(vh * 9 / 16)), vh
    else:
        W, H = int(round(short * 16 / 9)) // 2 * 2, short; VW, VH = int(round(vh * 16 / 9)), vh
    fps = int(fl("fps", a.fps))
    if fps not in (24, 25, 30, 50, 60): print(f"(fps={fps} unusual hai, 30 ya 60 lo)")
    brand = opts.get("intro_text") or BRAND
    # ---- intro: off / on (text) / video
    intro_mode = str(opts.get("intro", "off")).lower()
    intro_video = None
    if intro_mode == "video":
        intro_video = find_media(MEDIA_DIR, "intro", VID_EXT)
        if not intro_video: print("(intro video media/ folder me nahi mili - text intro use ho raha hai)")
    use_intro = ("video" if intro_video else "text") if intro_mode not in ("off", "no", "0", "false") else None
    n_intro = (clip_frames(intro_video, fps, opts.get("intro_len")) if intro_video else int(round(INTRO_S * fps))) if use_intro else 0
    # ---- end: on / off / video
    end_video, end_on = None, not off("end")
    if str(opts.get("end", "on")).lower() == "video":
        end_video = find_media(MEDIA_DIR, "end", VID_EXT)
        if not end_video: print("(end video media/ folder me nahi mili - normal end screen use ho raha hai)")
        else:
            end_on = False; items = [x for x in items if not (x["role"] == "cmd" and x["cmd"] == "end")]
    n_end = clip_frames(end_video, fps, opts.get("end_len")) if end_video else 0
    # ---- voice
    def vsp(who, dflt):
        v = str(opts.get(f"voice_{who}", dflt)); r = str(opts.get(f"voice_{who}_rate", "+0%")); pt = str(opts.get(f"voice_{who}_pitch", "+0Hz"))
        return dict(voice=v if re.fullmatch(r"[A-Za-z0-9-]{5,60}", v) else dflt,
                    rate=r if re.fullmatch(r"[+-]\d{1,3}%", r) else "+0%", pitch=pt if re.fullmatch(r"[+-]\d{1,3}Hz", pt) else "+0Hz")
    ai = vsp("ai", "en-US-JennyNeural")
    def other(who):
        v = str(opts.get(f"voice_{who}", "same"))
        return dict(ai, voice=v) if re.fullmatch(r"[A-Za-z]{2}-[A-Za-z]{2,4}-[A-Za-z0-9]+Neural", v) else ai
    emo_s = 0.0 if off("voice_emotion") else (1.0 if str(opts.get("voice_emotion", "on")).lower() in TRUE else fl("voice_emotion", 1.0))
    voice = dict(on=on("voice"), vol=fl("voice_vol", 1.0), emo=emo_s, user=vsp("user", "en-US-GuyNeural"), ai=ai, chatgpt=ai,
                 gemini=other("gemini"), grok=other("grok"), claude=other("claude"))
    vtexts = {k: (r, t) for k, (r, t) in vraw.items() if re.search(r"\w", tts_clean(t)) or has_voice_cue(t)}
    # ---- tool settings (dashboard sync) + script header
    ls, ui = load_ui(ratio)
    for key, lk in (("gpt_delay", "dA"), ("opp_delay", "dG"), ("user_delay", "dU"), ("send_delay", "dSend"), ("chat_size", "chat_font_size"),
                    ("think_gpt", "gptBThink"), ("think_gemini", "geminiBThink"), ("think_grok", "grokBThink"), ("think_claude", "claudeBThink")):
        if re.fullmatch(r"\d+(\.\d+)?", str(opts.get(key, ""))): ls[lk] = str(opts[key])
    accent = str(opts.get("accent", "")).lower()
    jsopts = dict(ratio=ratio, light=on("light"), accent=accent if accent in ("blue", "green", "yellow", "pink", "orange", "purple", "black") else None,
                  typing=max(0.1, min(3.0, fl("typing", 1.0))), speed=max(0.25, min(3.0, fl("speed", 1.0))),
                  human=on("human"), laptop=on("laptop"), end=end_on, endText=opts.get("end_text") or "Thanks for watching!",
                  brand=opts.get("end_sub") or brand, start=int(fl("start_delay", 2.0) * 1000))
    S = dict(
        voice=voice, vtexts=vtexts, vroles={k: r for k, (r, _) in vtexts.items()}, vemo=vemo,
        stags=stags, sfx_auto=not off("auto") and not off("sfx_auto"),
        moods=moods, memes=memes, name=Path(script).stem, use_intro=use_intro, brand=brand,
        intro_video=str(intro_video) if intro_video else None, n_intro=n_intro,
        end_video=str(end_video) if end_video else None, n_end=n_end,
        vol_intro=fl("intro_vol", 1.0), vol_end=fl("end_vol", 1.0), vol_meme=fl("meme_vol", 1.0),
        keys=norm_style(opts.get("keys", "iphone")),
        vol_click=0.0 if off("click") else a.volume * (1.0 if str(opts.get("click", "on")).lower() == "on" else float(opts["click"])),
        vol_music=0.0 if off("music") else (0.12 if str(opts.get("music", "on")).lower() == "on" else float(opts["music"])),
        vol_sfx=0.0 if off("sfx") else (1.0 if str(opts.get("sfx", "on")).lower() == "on" else float(opts["sfx"])),
        want_shorts=(not off("shorts", "off")) and ratio != "9:16", bgm=find_bgm(opts))
    cfg = dict(items=items, opts=opts, jsopts=jsopts, ls=ls, ui=ui, html=a.html, font=a.font, osize=(W, H), view=(VW, VH),
               dsf=W / VW, fps=fps, crf=a.crf, preset=a.preset, name=S["name"], brand=brand, memes=memes, vdur={})
    print(f"[{S['name']}] {ratio} {W}x{H} @ {fps}fps (tool size {VW}x{VH}), {sum(1 for x in items if x.get('k') is not None)} messages, "
          f"ui images: {sorted(ui['saved'])}, user imgs: {len(ui['user'])}, ai imgs: {len(ui['ai'])}, settings: {len(ls)}", flush=True)
    return S, cfg

def render_range(cfg, S, plan, f0, f1, with_intro, workers, out_dir, tag):
    name = cfg["name"]; out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    n = f1 - f0; workers = max(1, min(workers, n))
    bounds = [f0 + round(i * n / workers) for i in range(workers + 1)]
    tasks = []
    if with_intro:
        if S["use_intro"] == "video":
            tasks.append(dict(cfg, kind="introvid", idx=-1, clip=S["intro_video"], n=S["n_intro"],
                              out=str(out_dir / f"{name}.sub_{tag}_intro.mp4")))
        else:
            tasks.append(dict(cfg, kind="intro", idx=-1, out=str(out_dir / f"{name}.sub_{tag}_intro.mp4")))
    for i in range(workers):
        tasks.append(dict(cfg, kind="seg", idx=i, f0=bounds[i], f1=bounds[i + 1], total=plan["total"],
                          gaps=plan.get("gaps", []), out=str(out_dir / f"{name}.sub_{tag}_{i:02d}.mp4")))
    print(f"[{name}] frames {f0}-{f1}: {workers} worker ek saath", flush=True)
    if len(tasks) == 1:
        parts = [segment_task(tasks[0])]
    else:
        with multiprocessing.get_context("spawn").Pool(min(workers, len(tasks))) as pool:
            parts = pool.map(segment_task, tasks, chunksize=1)
    return concat_videos(parts, out_dir / f"{name}.part_{tag}.mp4", delete=True)

def concat_videos(parts, out_path, delete=False):
    out_path = Path(out_path); lst = out_path.with_suffix(".txt")
    lst.write_text("".join(f"file '{Path(p).resolve()}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(out_path)], check=True)
    lst.unlink()
    if delete:
        for p in parts: Path(p).unlink()
    return str(out_path)

def finish(cfg, S, plan, video_path, out_dir):
    global W, H
    W, H = cfg["osize"]
    name, fps, k = cfg["name"], cfg["fps"], plan["total"]
    out_dir = Path(out_dir); tmp_audio, final = out_dir / f"{name}.wav", out_dir / f"{name}.mp4"
    n_intro, n_end = S["n_intro"], S["n_end"]; intro_s = n_intro / fps
    t0, gaps, events, music_tl, extra, duck = plan["t0"], plan.get("gaps", []), [], [], [], []
    def sh(t):                      # chat-time (sec) -> final timeline (meme gaps jodkar, intro se pehle)
        return t + sum(g["G"] / fps for g in gaps if t >= (g["t"] - t0) / 1000 - 0.002) + intro_s
    events, vwin = plan_sfx(cfg, S, plan, sh, t0)
    for e in plan["log"]:
        mood = S["moods"].get(e.get("k")) if e["n"] in ("send", "show") else None
        if mood in MUSIC_OF: music_tl.append((sh((e["t"] - t0) / 1000), MUSIC_OF[mood]))
    fx_used = [f"{tm:.1f}s {nm}" for tm, nm, *r in events if r and r[-1]]
    if fx_used: print(f"[{name}] sound effects ({len(fx_used)}): " + ", ".join(fx_used), flush=True)
    clicks_s = [sh(c / 1000) for c in plan["clicks"]]
    seconds = (n_intro + k + n_end) / fps
    for gp in gaps:                 # meme ki apni awaaz + music dabana
        st = intro_s + gp["g"] / fps; d = gp["G"] / fps
        a_ = clip_audio(meme_path(gp["meme"]), d)
        if len(a_) > 64: extra.append((st, a_, S["vol_meme"]))
        duck.append((st, st + d))
    vdir = plan.get("voice_dir")
    if S["voice"]["on"] and plan.get("voice") and vdir:
        vs = plan.get("vstarts", {})
        for ks, info in plan["voice"].items():
            st_c = vs.get(str(ks))
            if st_c is None: continue
            st_c /= 1000
            a_ = clip_audio(Path(vdir) / info["file"], info["dur"] + 0.5)
            if len(a_) > 64: extra.append((sh(st_c), a_, S["voice"]["vol"]))
    if S["use_intro"] == "video":
        a_ = clip_audio(S["intro_video"], intro_s)
        if len(a_) > 64: extra.append((0.0, a_, S["vol_intro"]))
    if n_end:
        a_ = clip_audio(S["end_video"], n_end / fps)
        if len(a_) > 64: extra.append(((n_intro + k) / fps, a_, S["vol_end"]))
    if CUSTOM_SFX: print(f"[{name}] custom sounds: {sorted(CUSTOM_SFX)}")
    print(f"[{name}] {len(clicks_s)} clicks, {len(events)} sfx, {len(gaps)} meme, moods: {sorted(set(m for _, m in music_tl)) or ['calm']}")
    make_audio(clicks_s, events, music_tl, seconds, intro_s, tmp_audio, S["vol_click"], S["vol_sfx"], S["vol_music"],
               S["use_intro"], S["keys"], S["bgm"], extra, duck, [(sh(a_ / 1000), sh(b_ / 1000)) for a_, b_ in plan.get("typing", [])], vwin)
    if n_end:
        endseg = out_dir / f"{name}.endclip.mp4"
        ff = start_ffmpeg(endseg, fps, cfg["crf"], cfg["preset"], out_size())
        for jpg in video_frames(S["end_video"], fps, 0, n_end, out_size()): ff.stdin.write(jpg)
        ff.stdin.close(); ff.wait()
        if ff.returncode: sys.exit("end video encode fail ho gaya")
        joined = concat_videos([video_path, endseg], out_dir / f"{name}.withend.mp4")
        Path(video_path).unlink(); endseg.unlink(); video_path = joined
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video_path), "-i", str(tmp_audio),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest",
                    "-movflags", "+faststart", str(final)], check=True)
    Path(video_path).unlink(); tmp_audio.unlink()
    print(f"[{name}] DONE  {seconds:.1f}s, {final.stat().st_size/1e6:.0f} MB -> {final}")
    if S["want_shorts"]:
        sh = out_dir / f"{name}_shorts.mp4"
        vf = ("[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              "boxblur=40:5,eq=brightness=-0.18[bg];[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(final), "-filter_complex", vf,
                        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "copy",
                        "-movflags", "+faststart", str(sh)], check=True)
        print(f"[{name}] SHORTS -> {sh}" + ("" if seconds <= 180 else "  (dhyan: Shorts 3 minute se chhoti honi chahiye)"))

def make_plan(cfg):
    t = time.time()
    chat, gaps, t0, clicks, log, vstarts, typing = dry_run(cfg)
    total = chat + sum(x["G"] for x in gaps)
    print(f"[{cfg['name']}] timeline ready: {total/cfg['fps']:.1f}s = {total} frames, {len(gaps)} meme ({time.time()-t:.0f}s)", flush=True)
    return dict(total=total, chat=chat, gaps=gaps, t0=t0, clicks=clicks, log=log, fps=cfg["fps"], vstarts=vstarts, typing=typing)

def make_key_samples(out_dir):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(3); t, clicks = 0.4, []
    for ch in "Hey ChatGPT, tell me a joke":
        if ch != " ": clicks.append(t)
        t += float(rng.uniform(0.065, 0.115)) * (2.2 if ch == " " else 1)
    seconds = t + 1.6
    for i, st in enumerate(KEY_STYLES, 1):
        wav = out_dir / f"{i}_{st}.wav"
        make_audio(clicks, [(t + 0.2, "send"), (t + 0.75, "recv")], [], seconds, 0, wav, 1.0, 1.0, 0.0, False, st)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-ac", "2", "-b:a", "192k", str(out_dir / f"{i}_{st}.mp3")], check=True)
    lst = out_dir / "all.txt"; gap = out_dir / "gap.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "1.2", str(gap)], check=True)
    lst.write_text("".join(f"file '{(out_dir / f'{i}_{st}.wav').resolve()}'\nfile '{gap.resolve()}'\n" for i, st in enumerate(KEY_STYLES, 1)))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-ac", "2", "-b:a", "192k", str(out_dir / "all_6_in_order.mp3")], check=True)
    for p in list(out_dir.glob("*.wav")) + [lst]: p.unlink()
    print("samples ban gaye:", sorted(x.name for x in out_dir.iterdir()))

def plan_path(plan_dir, name): return Path(plan_dir) / f"{name}.plan.json"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("script", nargs="?"); ap.add_argument("--out", default="out")
    ap.add_argument("--sample-keys", metavar="DIR", help="6 typing-sound styles ke sunne wale sample banao")
    ap.add_argument("--fps", type=int, default=int(os.environ.get("FPS", 30)))
    ap.add_argument("--crf", type=int, default=15); ap.add_argument("--preset", default="veryfast")
    ap.add_argument("--workers", type=int, default=int(os.environ.get("WORKERS", min(os.cpu_count() or 1, 4))),
                    help="ek machine par kitne hisse ek saath render hon")
    ap.add_argument("--volume", type=float, default=1.0, help="typing click volume")
    ap.add_argument("--font", default='Inter,"SF Pro Text","Helvetica Neue",Roboto,"Noto Sans",EMO,sans-serif')
    ap.add_argument("--html", default="tool.html")
    ap.add_argument("--dsf", type=float, default=2, help="script me quality na ho to: 2 = 1080p, 4 = 4K, 1 = 540p (test)")
    ap.add_argument("--plan", metavar="DIR", help="sirf timeline banao aur DIR me plan.json likho")
    ap.add_argument("--part", type=int, help="plan ka ye hissa render karo")
    ap.add_argument("--merge", action="store_true", help="saare parts jodkar audio ke saath final video banao")
    ap.add_argument("--plan-dir", default="plan"); ap.add_argument("--parts-dir", default="parts")
    
    # PEHLE YAHAN 1800 THA (60 seconds), AB MAINE ISKO 60 FRAMES (2 seconds) KAR DIYA HAI
    ap.add_argument("--frames-per-part", type=int, default=60, help="ek machine ko kitne frames milen")
    a = ap.parse_args()

    if a.sample_keys:
        make_key_samples(a.sample_keys)
        sys.exit(0)
    if not a.script:
        sys.exit("script ka path do, jaise: python3 render.py scripts/video1.txt")
    S, cfg = settings(a.script, a)
    name = cfg["name"]
    
    def load_voice(plan, plan_dir):
        cfg["vdur"] = {int(k): x["dur"] for k, x in plan.get("voice", {}).items()}
        plan["voice_dir"] = str(Path(plan_dir) / "voice")

    if a.plan:
        voice = gen_voice(S, Path(a.plan) / "voice")
        cfg["vdur"] = {k: x["dur"] for k, x in voice.items()}
        plan = make_plan(cfg); plan["voice"] = voice
        # YAHAN MAX LIMIT 8 SE BADHAKAR 60 KAR DI HAI 
        parts = max(1, min(60, math.ceil(plan["total"] / a.frames_per_part)))
        plan["parts"] = parts
        Path(a.plan).mkdir(parents=True, exist_ok=True)
        plan_path(a.plan, name).write_text(json.dumps(plan))
        print(f"[{name}] {parts} part(s) banenge")
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as o:
                o.write("parts=" + json.dumps(list(range(parts))) + "\n")
    elif a.part is not None:
        plan = json.loads(plan_path(a.plan_dir, name).read_text()); load_voice(plan, a.plan_dir)
        P, i = plan["parts"], a.part
        f0, f1 = round(i * plan["total"] / P), round((i + 1) * plan["total"] / P)
        render_range(cfg, S, plan, f0, f1, S["use_intro"] and i == 0, a.workers, a.out, f"{i:02d}")
    elif a.merge:
        plan = json.loads(plan_path(a.plan_dir, name).read_text()); load_voice(plan, a.plan_dir)
        files = sorted(Path(a.parts_dir).glob(f"{name}.part_*.mp4"))
        if len(files) != plan["parts"]:
            sys.exit(f"{len(files)} part mile, {plan['parts']} chahiye the")
        Path(a.out).mkdir(parents=True, exist_ok=True)
        video = concat_videos(files, Path(a.out) / f"{name}.noaudio.mp4")
        finish(cfg, S, plan, video, a.out)
    else:
        import shutil
        vdir = Path(a.out) / f".voice_{name}"
        voice = gen_voice(S, vdir)
        cfg["vdur"] = {k: x["dur"] for k, x in voice.items()}
        plan = make_plan(cfg); plan["voice"] = voice; plan["voice_dir"] = str(vdir)
        video = render_range(cfg, S, plan, 0, plan["total"], S["use_intro"], a.workers, a.out, "all")
        finish(cfg, S, plan, video, a.out)
        shutil.rmtree(vdir, ignore_errors=True)
