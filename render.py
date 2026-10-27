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

OPT_RE = re.compile(r"^\s*#\s*(typing|speed|human|laptop|light|accent|ratio|view|ui|music|sfx|click|keys|intro|shorts|auto|end|bgm|bgm_start|bgm_vol|quality|fps|intro_len|end_len|intro_vol|end_vol|meme_vol|"
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
TAG_RE = re.compile(r"\s*\{\s*(%s)\s*\}" % "|".join(MOODS + [n for n in CUSTOM_SFX if n not in MOODS]), re.I)

AUTO = [
    ("funny", "😂🤣😆😹", r"\b(lol|lmao|rofl|haha+)\b"),
    ("scary", "😱😨😰👻💀🩸🔪🕷", r"\b(scary|ghost|haunted|creepy)\b"),
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
        if mr:
            k += 1; body = mr.group(2)
            items.append(dict(k=k, role=ROLE_OF[mr.group(1).lower()], raw="", phase=phase))
        elif k < 0 or line.lstrip().startswith("#"):
            continue
        else:
            body = line.strip()
        mv = list(VOICE_TAG_RE.finditer(body))
        if mv: vemo[k] = mv[-1].group(1).lower(); body = VOICE_TAG_RE.sub("", body)
        found = TAG_RE.findall(body)
        if found: tags[k] = found[-1].lower()
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
    return items, opts, moods, memes, vraw, vemo

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

def sfx(name):
    if name == "send":
        t = tt(0.09); return np.sin(2 * np.pi * np.cumsum(700 - 3000 * t) / SR) * np.exp(-t * 35) * 0.30
    if name == "recv":
        x = np.zeros(int(0.5 * SR)); put(x, tone(880, 0.4, decay=9), 0, 0.22); put(x, tone(1318.5, 0.4, decay=9), 0.07, 0.22); return x
    if name == "funny":
        t = tt(0.55); f = 240 + 170 * np.sin(2 * np.pi * 9 * t) * np.exp(-5 * t) + 330 * np.exp(-6 * t)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5) * 0.5
    if name in ("scary", "angry"):
        d = 1.8 if name == "scary" else 0.7; t = tt(d)
        body = np.sin(2 * np.pi * (55 if name == "scary" else 80) * t) * np.exp(-t * (2.2 if name == "scary" else 5))
        rumble = np.convolve(noise(d, 9), np.ones(60) / 60, mode="same") * np.exp(-t * 3) * 3
        x = (body * 0.7 + rumble * 0.4)
        if name == "angry":
            saw = sum(np.sin(2 * np.pi * 80 * h * t) / h for h in range(1, 9)) * np.exp(-t * 6)
            x = np.tanh(saw * 1.6) * 0.5 + body * 0.4
        return reverb(x, rt=1.2, mix=0.3)[:int(d * SR + SR)] * 0.9
    if name == "sad":
        x = np.zeros(int(2.4 * SR))
        put(x, tone(midi(76), 1.8, decay=2.2, harm=(1, 2.76), amps=(1, .3)), 0, 0.3)
        put(x, tone(midi(72), 2.0, decay=2.0, harm=(1, 2.76), amps=(1, .3)), 0.45, 0.3)
        return reverb(x, rt=1.5, mix=0.35)
    if name == "mystery":
        d = 2.6
        x = (tone(1318.5, d, decay=1.6, harm=(1, 1.5), amps=(1, .5), tremolo=6) +
             tone(1976, d, decay=1.8, tremolo=4) * 0.6 + tone(2637, d, decay=2.2) * 0.35)
        return reverb(x * 0.18, rt=2.0, mix=0.45)
    if name == "whoosh":
        d = 0.7; t = tt(d); w = np.diff(noise(d, 8), prepend=0) * np.sin(np.pi * t / d) ** 2
        return w / (np.abs(w).max() + 1e-9) * 0.4
    if name == "hit":
        t = tt(0.5); x = np.sin(2 * np.pi * 62 * t) * np.exp(-t * 9) + _lp(noise(0.5, 6), 18) * np.exp(-t * 30) * 2
        return x / (np.abs(x).max() + 1e-9) * 0.55
    if name == "pop2":
        t = tt(0.16); x = np.sin(2 * np.pi * np.cumsum(520 + 1500 * t) / SR) * np.exp(-t * 20) * np.minimum(1, t / 0.004)
        return x * 0.35
    if name == "subscribe":
        x = np.zeros(int(0.5 * SR))
        put(x, tone(1800, 0.05, decay=90), 0, 0.5); put(x, tone(880, 0.35, decay=9), 0.06, 0.28); put(x, tone(1318.5, 0.35, decay=9), 0.13, 0.25)
        return x
    if name == "bell":
        d = 1.4; x = (tone(1568, d, decay=3.2, harm=(1, 2.4, 4.1), amps=(1, .4, .2)) + tone(1046.5, d, decay=3.6, harm=(1, 2.7), amps=(.7, .3)))
        y = np.zeros(int(1.8 * SR)); put(y, x, 0, 0.3); put(y, x, 0.38, 0.22); put(y, x, 0.76, 0.16)
        return reverb(y, rt=1.0, mix=0.2)
    if name in ("hype", "surprise"):
        d = 0.65; t = tt(d); w = np.diff(noise(d, 4), prepend=0) * np.sin(np.pi * t / d) ** 2 * 0.6
        x = w.copy()
        for k, n in enumerate((84, 88, 91, 96)): put(x, tone(midi(n), 0.3, decay=12), 0.28 + k * 0.06, 0.22 * 3)
        return x / (np.abs(x).max() + 1e-9) * 0.45
    return np.zeros(10)

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

def get_sfx(name):
    x = load_custom(name)
    return x if x is not None else sfx(name)

def intro_sfx():
    rng = np.random.default_rng(11); out = np.zeros(int((INTRO_S + 0.8) * SR))
    for t0 in (0.05, 0.24, 0.41, 0.53, 0.9, 1.12, 1.31):
        d = rng.uniform(0.03, 0.09); raw = rng.standard_normal(int(d * SR)); hold = int(rng.integers(4, 40))
        crush = np.repeat(raw[::hold], hold)[:len(raw)] * 0.3; put(out, crush, t0)
        sq = np.sign(np.sin(2 * np.pi * float(rng.choice([220, 440, 660, 880])) * tt(d))) * 0.12; put(out, sq, t0)
    t = tt(0.65); sweep = np.sin(2 * np.pi * np.cumsum(200 * 8 ** (t / 0.65)) / SR) * (t / 0.65) * 0.16
    put(out, sweep, 0.9); put(out, sfx("scary")[:int(2.2 * SR)], 1.55, 0.7)
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

def make_audio(clicks_s, events, music_tl, seconds, intro_s, path, vol_click, vol_sfx, vol_music, use_intro, keys="iphone", bgm=None, extra=None, duck=None, spans=None):
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
        cache = {}
        for tm, name in events:
            if name not in cache: cache[name] = get_sfx(name)
            put(out, cache[name], tm, vol_sfx)
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
    peak = np.abs(out).max()
    if peak > 0.95: out *= 0.95 / peak
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
# Microsoft ki free awaaz me "angry / cheerful" style allowed nahi hai, isliye emotion yahan banaya jaata hai:
#   - har sentence ki speed / pitch / volume emotion ke hisaab se (gussa = tez + zor se, sad = dheema + neecha ...)
#   - text ki chhoti tricks (gusse me "!" , sad me "..." pause)
#   - CAPS ya "!!" wala sentence = chillahat
#   - "haha / lol / 😂" = usi awaaz se bani hasi, "hehe / 😅" = halki hasi, "sigh / uff / 😔" = aah ki saans, "omg / 😱" = saans kheenchna
#   - awaaz par effect: gussa = bhaari + kadak, sad / cry = kaanpti awaaz, scary = gunj, whisper = phusphusahat
# Script me khud bhi bata sakte ho: {v:angry} {v:funny} {v:sad} {v:cry} {v:scary} {v:shout} {v:whisper} {v:excited}
#   {v:surprise} {v:nervous} {v:sarcastic} {v:calm} {v:normal}   (ye tag screen par nahi dikhta)
VOICE_TAG_RE = re.compile(r"\s*\{\s*(?:v|voice)\s*:\s*([a-z_]+)\s*\}", re.I)
LAUGH_RE = re.compile(r"(?i)(?<![a-z])(?:a?ha(?:\s?ha)+h?|lo+l+|lmf?ao+|rofl|bwa+h?a+(?:ha)*)(?![a-z])|[\U0001F602\U0001F923\U0001F606\U0001F639]")
CHUCKLE_RE = re.compile(r"(?i)(?<![a-z])(?:he(?:\s?he)+h?|heh)(?![a-z])|[\U0001F605\U0001F60F\U0001F61C\U0001F61D]")
SIGH_RE = re.compile(r"(?i)\*?(?<![a-z])(?:sigh+s?|uff+|ugh+)(?![a-z])\*?|\U0001F62E‍\U0001F4A8|[\U0001F614\U0001F61E\U0001F629\U0001F97A\U0001F613]")
GASP_RE = re.compile(r"(?i)(?<![a-z])(?:omg|oh my god|oh my gosh|no way|wait what|whoa+)(?![a-z])|[\U0001F631\U0001F628\U0001F632\U0001F92F\U0001F633]|\U0001F62E(?!‍)")
CRY_RE = re.compile(r"[\U0001F62D\U0001F622]")
def has_voice_cue(t): return any(r.search(t) for r in (LAUGH_RE, CHUCKLE_RE, SIGH_RE))
SENT_RE = re.compile(r"[^.!?…]+(?:[.!?…]+|$)")
EMO_ALIAS = {"funny": "funny", "laugh": "funny", "haha": "funny", "angry": "angry", "gussa": "angry", "shout": "shout", "chilla": "shout",
             "sad": "sad", "cry": "cry", "rona": "cry", "scary": "scary", "dar": "scary", "horror": "scary", "mystery": "mystery",
             "hype": "excited", "excited": "excited", "khush": "excited", "surprise": "surprise", "shock": "surprise",
             "whisper": "whisper", "nervous": "nervous", "sarcastic": "sarcastic", "calm": "calm", "normal": "none", "none": "none", "off": "none"}
MOOD_EMO = {"funny": "funny", "angry": "angry", "sad": "sad", "scary": "scary", "mystery": "mystery", "hype": "excited", "surprise": "surprise", "calm": "calm"}
#            rate %, pitch (semitone), volume %, awaaz par effect (ffmpeg)
EMO = {
    "none":      (0, 0.0, 0, ""),
    "calm":      (-4, -0.3, -5, ""),
    "funny":     (8, 1.6, 6, "equalizer=f=3200:t=q:w=1.2:g=2"),
    "excited":   (15, 2.4, 18, "equalizer=f=3000:t=q:w=1:g=3,acompressor=threshold=0.15:ratio=3:attack=5:release=100:makeup=2"),
    "surprise":  (6, 3.0, 10, "equalizer=f=3000:t=q:w=1:g=2"),
    "angry":     (10, -0.6, 28, "highpass=f=90,equalizer=f=2800:t=q:w=1.2:g=5,acompressor=threshold=0.12:ratio=5:attack=4:release=80:makeup=2.5,asoftclip=type=tanh"),
    "shout":     (6, 2.2, 45, "highpass=f=110,equalizer=f=2600:t=q:w=1.1:g=7,acompressor=threshold=0.1:ratio=6:attack=3:release=70:makeup=3,asoftclip=type=tanh"),
    "sad":       (-18, -1.5, -12, "lowpass=f=3600,vibrato=f=5.5:d=0.15"),
    "cry":       (-14, 0.8, -10, "lowpass=f=3400,vibrato=f=6.5:d=0.35,tremolo=f=5:d=0.25"),
    "scary":     (-16, -2.0, -8, "lowpass=f=3200,aecho=0.8:0.6:70|160:0.3|0.18"),
    "mystery":   (-10, -1.0, -5, "aecho=0.8:0.55:90:0.22"),
    "whisper":   (-6, -0.5, -30, "WHISPER"),
    "nervous":   (14, 1.2, -5, "vibrato=f=7:d=0.1"),
    "sarcastic": (-12, -0.8, 0, ""),
}
SLOW_EMO, FAST_EMO = ("sad", "cry", "scary", "mystery", "sarcastic"), ("excited", "angry", "shout", "funny")
MALE_VOICES = ("Guy", "Davis", "Jason", "Tony", "Brandon", "Christopher", "Eric", "Roger", "Steffan", "Andrew", "Brian", "Jacob", "Ryan",
               "Thomas", "William", "Liam", "Prabhat", "Connor", "Luke", "Madhur", "Ken", "Mitchell", "Wayne", "Sam", "Elliot", "Duncan")

def pick_emotion(raw, vtag, mood):
    if vtag: return EMO_ALIAS.get(vtag.lower(), "none")
    e = MOOD_EMO.get(mood, "none")
    if CRY_RE.search(raw) and e in ("none", "sad", "calm"): return "cry"
    if e == "none":
        if LAUGH_RE.search(raw) or CHUCKLE_RE.search(raw): return "funny"
        if SIGH_RE.search(raw): return "sad"
        if GASP_RE.search(raw): return "surprise"
    return e

SLANG = {"omg": "oh my god", "omfg": "oh my god", "idk": "I don't know", "tbh": "to be honest", "ngl": "not gonna lie", "btw": "by the way",
         "imo": "in my opinion", "imho": "in my honest opinion", "rn": "right now", "smh": "shaking my head", "brb": "be right back",
         "pls": "please", "plz": "please", "thx": "thanks", "ty": "thank you", "np": "no problem", "fr": "for real", "wtf": "what the heck",
         "wth": "what the heck", "bruh": "bruh", "nvm": "never mind", "ikr": "I know right", "irl": "in real life", "afk": "away from keyboard",
         "gg": "good game", "dm": "D M", "asap": "as soon as possible", "jk": "just kidding", "ofc": "of course", "u": "you", "ur": "your", "r": "are"}
SLANG_RE = re.compile(r"(?i)(?<![\w'])(" + "|".join(sorted(map(re.escape, SLANG), key=len, reverse=True)) + r")(?![\w'])")

def _tweak(t, e):
    """text ki chhoti tricks taaki neural awaaz khud thoda emotion me bole"""
    t = SLANG_RE.sub(lambda m: SLANG[m.group(1).lower()], t)
    t = re.sub(r"\b([A-Z][A-Z']{3,})\b", lambda m: m.group(1).lower(), t)       # CAPS words spell na hon
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
        if caps: t = t.lower()
        if GASP_RE.search(sent): out.append(("gasp", "", e, False))
        out.append(("say", _tweak(t, e), e, loud))
    return out

def voice_plan(raw, emo):
    """message -> [(kind, text, emotion, loud)]  kind: say / laugh / chuckle / sigh / gasp"""
    marks, last = [], -1
    for s, e_, kind in sorted([(m.start(), m.end(), kd) for rx, kd in ((SIGH_RE, "sigh"), (LAUGH_RE, "laugh"), (CHUCKLE_RE, "chuckle"))
                               for m in rx.finditer(raw)]):
        if s >= last: marks.append((s, e_, kind)); last = e_
    out, pos = [], 0
    for s, e_, kind in marks:
        out += say_chunks(raw[pos:s], emo); out.append((kind, "", emo, False)); pos = e_
    out += say_chunks(raw[pos:], emo)
    if emo == "none" and any(x[0] == "say" and x[2] == "shout" for x in out):
        out = [("say", _tweak(x[1], "angry"), "angry", x[3]) if x[0] == "say" and x[2] == "none" else x for x in out]
    merged = []                       # same tarah ke lagaatar sentence ek saath bolo (awaaz natural rehti hai)
    for seg in out:
        if merged and seg[0] in ("laugh", "chuckle", "sigh", "gasp") and merged[-1][0] == seg[0]: continue
        if merged and seg[0] == "say" and merged[-1][0] == "say" and merged[-1][2:] == seg[2:]:
            merged[-1] = ("say", merged[-1][1] + " " + seg[1], seg[2], seg[3]); continue
        merged.append(seg)
    seen = set()
    for i, seg in enumerate(merged):           # har cue (hasi / halki hasi / aah / gasp) ek message me ek hi baar
        if seg[0] != "say":
            if seg[0] in seen or (seg[0] == "chuckle" and "laugh" in seen) or (seg[0] == "laugh" and "chuckle" in seen): merged[i] = None
            seen.add(seg[0])
    merged = [x for x in merged if x]
    if emo == "nervous":              # pehle shabd par hakla: "W-what"
        for i, seg in enumerate(merged):
            if seg[0] == "say":
                merged[i] = ("say", re.sub(r"^([A-Za-z])([a-z]+)", lambda m: f"{m.group(1)}-{m.group(1).lower()}{m.group(2)}", seg[1], 1), *seg[2:]); break
    return merged

def _prosody(sp, e, loud, strength, rng):
    dr, dst, dv, _ = EMO.get(e, EMO["none"])
    if loud: dr, dst, dv = dr + 4, dst + 0.8, dv + 18
    st = dst * strength + rng.uniform(-0.25, 0.25)
    f0 = 120 if any(nm in sp["voice"] for nm in MALE_VOICES) else 210
    rate = int(sp["rate"][:-1]) + round(dr * strength + rng.uniform(-2.5, 2.5))
    hz = int(sp["pitch"][:-2]) + round(f0 * (2 ** (st / 12) - 1))
    vol = round(dv * strength)
    rate, hz, vol = max(-60, min(100, rate)), max(-80, min(80, hz)), max(-80, min(100, vol))
    return f"{rate:+d}%", f"{vol:+d}%", f"{hz:+d}Hz"

def _decode(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype="<f4").astype(float)

def _trim(x, keep=0.02):
    if len(x) == 0: return x
    thr = max(0.012, np.abs(x).max() * 0.04)
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx): return x[:0]
    a, b = max(0, idx[0] - int(keep * SR)), min(len(x), idx[-1] + int(keep * 2 * SR))
    y = x[a:b].copy(); f = min(len(y) // 4, int(0.008 * SR))
    if f > 1: y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y

_fx_warned = set()
def _fx(x, chain):
    if not chain or len(x) < 64: return x
    pad = np.concatenate([x, np.zeros(int(0.35 * SR))]) if "aecho" in chain else x
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", chain,
                        "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"], input=pad.astype("<f4").tobytes(), capture_output=True)
    if p.returncode or len(p.stdout) < 64:
        if chain not in _fx_warned:
            _fx_warned.add(chain); print(f"(voice effect nahi chala, bina effect: {chain[:40]} {p.stderr[-120:]!r})", flush=True)
        return x
    y = np.frombuffer(p.stdout, dtype="<f4").astype(float)
    return _trim(y) if "aecho" in chain else y[:len(x)]

def _bandnoise(n, rng, lo, hi, centre=None, width=None):
    F = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR)
    F *= np.exp(-((f - centre) / width) ** 2) if centre else ((f >= lo) & (f <= hi))
    y = np.fft.irfft(F, n); return y / (np.abs(y).max() + 1e-9)

def _whisper(x, rng):
    n = len(x)
    if n < 256: return x
    w = int(0.012 * SR); env = np.convolve(np.abs(x), np.ones(w) / w, mode="same")
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X[f < 450] = 0; hp = np.fft.irfft(X, n)
    y = 0.3 * hp + 2.4 * _bandnoise(n, rng, 1200, 7000) * env
    return y * (np.sqrt((x ** 2).mean()) * 0.8 / (np.sqrt((y ** 2).mean()) + 1e-9))

def _sigh(rng, ref):
    n = int(rng.uniform(0.62, 0.8) * SR); t = np.arange(n) / SR
    y = (_bandnoise(n, rng, 0, 0, 900, 600) + 0.3 * _bandnoise(n, rng, 0, 0, 2400, 900))
    env = np.minimum(1, t / 0.12) ** 1.5 * np.exp(-2.6 * np.maximum(0, t - 0.12))
    y = y * env; return y * (ref * 0.55 / (np.sqrt((y ** 2).mean()) + 1e-9))

def _gasp(rng, ref):
    n = int(rng.uniform(0.26, 0.34) * SR); t = np.arange(n) / SR
    y = _bandnoise(n, rng, 0, 0, 2200, 1100) * (t / t[-1]) ** 1.4
    f = int(0.008 * SR); y[-f:] *= np.linspace(1, 0, f)
    return y * (ref * 0.6 / (np.sqrt((y ** 2).mean()) + 1e-9))

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

def _laugh(syl, rng, big=True):
    if not syl: return np.zeros(1)
    pat = ([(0, 1.0, 1.0), (1, 0.9, 1.06), (2, 0.8, 1.1), (1, 0.66, 1.12), (2, 0.52, 1.15)] if big else [(0, 0.72, 1.04), (1, 0.56, 1.08)])
    parts = []
    for i, g, k in pat:
        y = _speed(syl[i % len(syl)][: int(0.26 * SR)], k * rng.uniform(0.97, 1.03)) * g
        f = min(len(y) // 3, int(0.03 * SR))
        if f > 1: y[-f:] *= np.linspace(1, 0, f)
        parts += [y, np.zeros(int(rng.uniform(0.03, 0.055) * SR))]
    return np.concatenate(parts)

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
    # ---- har message ka plan (emotion + tukde)
    plans, jobs = {}, {}
    def job(text, sp, rate, vol, pitch):
        key = hashlib.md5(f"{sp['voice']}|{rate}|{vol}|{pitch}|{text}".encode()).hexdigest()[:16]
        jobs[key] = (text, sp["voice"], rate, vol, pitch); return key
    for k, (role, raw) in S["vtexts"].items():
        sp = v.get(role) or v["ai"]
        emo = pick_emotion(raw, S.get("vemo", {}).get(k), S["moods"].get(k)) if strength > 0 else "none"
        segs = voice_plan(raw, emo) if strength > 0 else [("say", tts_clean(raw), "none", False)]
        rng = np.random.default_rng(1000 + k); steps = []
        for kind, text, e, loud in segs:
            if kind == "say":
                rate, vol, pitch = _prosody(sp, e, loud, strength, rng) if strength > 0 else (sp["rate"], "+0%", sp["pitch"])
                steps.append(("say", job(text, sp, rate, vol, pitch), text, e, loud))
            elif kind in ("laugh", "chuckle"):
                rate, vol, pitch = _prosody(sp, "funny", False, max(strength, 0.6), np.random.default_rng(7))
                steps.append((kind, job("Ha ha ha!" if kind == "laugh" else "Heh heh.", sp, rate, vol, pitch), "", e, False))
            else:
                steps.append((kind, None, "", e, False))
        plain = job(tts_clean(raw), sp, sp["rate"], "+0%", sp["pitch"]) if re.search(r"\w", tts_clean(raw)) else None
        plans[k] = (role, emo, steps, plain)
    # ---- saari TTS ek saath (4-4 karke), dobara koshish ke saath
    got = {}
    async def one(sem, key):
        text, voice, rate, vol, pitch = jobs[key]; path = tmp / f"{key}.mp3"
        for attempt in range(4):
            try:
                async with sem:
                    await edge_tts.Communicate(text, voice, rate=rate, volume=vol, pitch=pitch).save(str(path))
                if path.exists() and path.stat().st_size > 300: return key, path
            except Exception as e:
                print(f"(voice '{text[:30]}': koshish {attempt + 1} fail: {str(e)[:90]})", flush=True)
            await asyncio.sleep(1.5 * (attempt + 1))
        return key, None
    async def run(keys):
        sem = asyncio.Semaphore(4)
        return await asyncio.gather(*[one(sem, kk) for kk in keys])
    needed = {s[1] for _, _, st, _ in plans.values() for s in st if s[1]}
    for key, path in asyncio.run(run(sorted(needed))):
        if path: got[key] = _trim(_decode(path))
    # ---- har message jodo
    out = {}
    for k, (role, emo, steps, plain) in plans.items():
        rng = np.random.default_rng(5000 + k)
        if any(s[1] and s[1] not in got and s[0] == "say" for s in steps):      # koi tukda nahi bana -> seedhi awaaz
            if plain and plain not in got:
                r = asyncio.run(run([plain]))[0]
                if r[1]: got[plain] = _trim(_decode(r[1]))
            steps = [("say", plain, "", "none", False)] if plain in got else []
        speech = [got[s[1]] for s in steps if s[0] == "say" and s[1] in got and len(got[s[1]])]
        ref = float(np.mean([np.sqrt((x ** 2).mean()) for x in speech])) if speech else 0.08
        parts, prev, used = [np.zeros(int(0.03 * SR))], None, []
        for kind, key, text, e, loud in steps:
            if kind == "say":
                x = got.get(key)
                if x is None or not len(x): continue
                fx = EMO.get(e, EMO["none"])[3]
                if strength >= 0.5 or fx == "WHISPER":
                    x = _whisper(x, rng) if fx == "WHISPER" else _fx(x, fx)
                    if loud and fx and "acompressor" not in fx: x = _fx(x, "acompressor=threshold=0.15:ratio=3:attack=5:release=90:makeup=2")
                if prev is not None: parts.append(np.zeros(int(_gap(prev, e) * SR)))
                parts.append(x); prev = text or "."; used.append(e + ("!" if loud else ""))
            elif kind in ("laugh", "chuckle") and key in got:
                lg = _laugh(_syllables(got[key]), rng, kind == "laugh")
                parts += [np.zeros(int(0.06 * SR)), lg, np.zeros(int(0.06 * SR))]; prev = None; used.append(kind)
            elif kind == "sigh":
                parts += [_sigh(rng, ref), np.zeros(int(0.12 * SR))]; prev = None; used.append("sigh")
            elif kind == "gasp":
                parts += [np.zeros(int(0.04 * SR)), _gasp(rng, ref), np.zeros(int(0.07 * SR))]; prev = None; used.append("gasp")
        y = np.concatenate(parts) if len(parts) > 1 else np.zeros(0)
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
    print(f"[voice] {len(out)}/{len(S['vtexts'])} message ki awaaz ban gayi (emotion {'off' if strength == 0 else strength})", flush=True)
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
    items, opts, moods, memes, vraw, vemo = parse_script(script)
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
    for e in plan["log"]:
        t_ = (e["t"] - t0) / 1000
        if e["n"] == "cmd":
            c = e.get("c")
            if c == "intro": events += [(sh(t_ + 0.02), "whoosh"), (sh(t_ + 0.4), "hit")]
            elif c in ("caption", "level"): events.append((sh(t_ + 0.02), "pop2"))
            elif c == "end": events += [(sh(t_ + 1.5), "subscribe"), (sh(t_ + 1.85), "bell")]
            continue
        user = e["n"] == "send"; t_ev = sh(t_)
        if user: events.append((t_ev, "send"))
        else:
            rv = f"recv_{e.get('role')}"
            events.append((t_ev, rv if rv in CUSTOM_SFX else "recv"))
        mood = S["moods"].get(e["k"])
        if mood:
            if mood != "calm": events.append((t_ev + 0.04, mood))
            if mood in MUSIC_OF: music_tl.append((t_ev, MUSIC_OF[mood]))
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
               S["use_intro"], S["keys"], S["bgm"], extra, duck, [(sh(a_ / 1000), sh(b_ / 1000)) for a_, b_ in plan.get("typing", [])])
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
