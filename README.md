# ⚔️ 4-AI Cinematic Render

Tumhare **4-AI Cinematic Engine** (ChatGPT / Gemini / Grok / Claude + Battle mode) ki video GitHub Actions par banti hai:
720p se 4K, 30/60 fps, 16:9 ya 9:16, intro, end screen, memes, apni sounds, background music aur voice.
Control Netlify wale **4-AI Cinematic Studio** dashboard se hota hai.

## Repo me kya hai

| File / folder | Kaam |
|---|---|
| `tool.html` | Tumhara tool (bilkul wahi). Render isi ko chala kar video banata hai |
| `render.py` | Render engine |
| `.github/workflows/render.yml`, `video.yml` | GitHub Actions (script aate hi render shuru) |
| `scripts/` | Dashboard yahan script daalta hai (`job_....txt`) |
| `ui/` | Tool se Sync hui settings (`settings.json`) + topbar / footer / suggestion images |
| `images/user/`, `images/ai/` | Message images: `[1]`, `[2]` ... |
| `memes/` | Meme videos: `[m1]`, `[m2]` ... |
| `sounds/` | Apni sounds (`typing`, `send`, `recv_gemini` ... aur `{vine_boom}` jaise tags) |
| `media/`, `music/` | Intro / end video, background music |
| `links.txt` | Bani hui video ke download links (dashboard yahi padhta hai) |

Ye folders dashboard se upload karte hi apne aap ban jaate hain.

## Script format (tool jaisa)

```
# ratio = 16:9            (ya 9:16 / full)
# quality = 1080p          (4k / 2k / 1080p / 720p)
User: Hey ChatGPT! [1]     <- [1] = User image 1
ChatGPT: Hello! {funny}    <- {mood} ya {apni_sound}
Gemini: I'm better. [m2]   <- [m2] = meme video 2
--- battle ---             <- iske baad Phase 2 (AI Battle, full screen)
Grok: ...
Claude: ...
!end: Thanks for watching! | Channel Name
```

Roles: `User:` `ChatGPT:` (ya `GPT:` / `AI:`) `Gemini:` `Grok:` `Claude:`.
Dashboard header ki saari `# ...` lines khud likh deta hai.

## Sound effects (free, apne aap)

~85 awaazein code se hi banti hain (koi download / paisa nahi). Har message ka feel dekh kar (emoji, shabd, mood, voice ka emotion)
usse milti awaaz bajti hai: joke ke baad boing / ba-dum-tss / honk, roast par boom / airhorn, gusse me dhamaka / punch, sad me piano / violin,
darr me horror cheekh / dhak-dhak / darwaza, 💰 par ka-ching, ❌ par wah-wah-waaah, 😬 par jhingur... Har group me kai awaazein hain,
patte ki tarah shuffle: jab tak group ki saari na baj jaayein koi dobara nahi, aur har baar thodi alag (pitch / speed).
Battle shuru hote hi dhamaka + boxing bell, har naye AI par whoosh, aur Gemini / Grok / Claude ke reply ki apni awaaz.
Har message par kuch na kuch bajta hai: normal baat par halka plink / tap / chamak, sawaal par "hm?", aur zor wale message
(CAPS, `!!`, gussa, shock) par aate hi ek jhatka + punchline ke baad wali awaaz.

Khud lagana ho to message me likho (screen par nahi dikhta):

| Group (us group ki koi bhi) | Kab |
|---|---|
| `{funny}` `{angry}` `{sad}` `{scary}` `{mystery}` `{hype}` `{surprise}` | mood (awaaz + music bhi badalta hai) |
| `{roast}` `{awkward}` `{fail}` `{win}` `{money}` `{love}` `{tech}` `{party}` `{sarcastic}` `{dead}` `{clown}` | sirf sound effect |
| `{blast}` `{spooky}` `{time}` `{magic}` `{bells}` `{fight}` `{blade}` `{storm}` `{launch}` `{oof}` `{dun}` `{idea}` `{evil}` | sirf sound effect |

Ek khaas awaaz: `{boom}` `{boom2}` `{airhorn}` `{rimshot}` `{boing}` `{doing}` `{honk}` `{bonk}` `{slide_up}` `{slide_down}` `{squeak}` `{pops}`
`{xylo_up}` `{xylo_down}` `{zip}` `{sad_trombone}` `{deflate}` `{fall}` `{tada}` `{fanfare}` `{explosion}` `{burn}` `{slap}` `{ring}` `{glass}`
`{bass_drop}` `{impact}` `{impact_deep}` `{impact_metal}` `{slam}` `{punch}` `{clang}` `{buzzer}` `{thunder}` `{alarm}` `{braam}` `{sword}`
`{piano_sad}` `{piano_low}` `{violin}` `{musicbox}` `{sting}` `{screech}` `{sting_low}` `{heartbeat}` `{creak}` `{drone}` `{ghost}` `{swell_hit}`
`{toll}` `{wind}` `{dun_dun}` `{tick}` `{tick_fast}` `{sparkle}` `{sneaky}` `{riser}` `{sonar}` `{vibes}` `{applause}` `{levelup}` `{coin}`
`{coins}` `{cash}` `{fireworks}` `{power_up}` `{power_down}` `{laser}` `{drumroll}` `{orch_hit}` `{scratch}` `{zoom_hit}` `{ding}` `{ding2}`
`{glitch}` `{crickets}` `{bloop}` `{beeps}` `{error}` `{harp}` `{chime}` `{heart_soft}` `{whoosh}` `{swoosh}` `{boxing_bell}` `{vs_hit}`
`{plink}` `{tap}` `{shimmer}` `{blip}` `{blip_up}` `{ponder}` (halke) &nbsp;·&nbsp; group: `{neutral}` `{question}` `{accent}`

`{nosfx}` = us message par koi effect nahi. `# sfx = 0.6` = sab effects dheeme (`off` = band), `# sfx_auto = off` = sirf tag wale.
Apni awaaz: `sounds/boom.mp3` daalo to built-in `boom` ki jagah wahi bajegi; `sounds/funny_2.mp3` jaisa naam = `funny` group me ek aur option.

## Meri sounds: typing / send / reply (gallery se)

Dashboard ke **⌨️ Chat Sounds** panel me har ek ke liye **System** ya **Meri** chuno aur 📤 Upload se phone ki file lagao
(GitHub ke `sounds/` folder me save hoti hai). Haath se bhi daal sakte ho:

| File | Kab bajti hai |
|---|---|
| `sounds/typing.mp3` | User ki typing ke dauraan |
| `sounds/send.mp3` | User ka message bhejne par (click) |
| `sounds/recv_chatgpt.mp3` | ChatGPT ka reply aane par |

```
# typing_sound = custom      (ya system -> # keys = iphone / mech / thock / bubble / typewriter / glass)
# typing_mode = loop         (tool jaisa, recording loop me)   ya   keys (recording se kaate click, har akshar par ek)
# send_sound = custom        (ya system)
# recv_sound = custom        (ya system)
# send_vol = 1.2             # recv_vol = 0.8     (100% = 1.0)
```
Kuch na likho to: file repo me hai to wahi bajti hai. Tumhari sound ki zor apne aap baaki awaazon jitni kar di jaati hai.

## Voice + emotion (free)

Script me `# voice = on` ho to har message bola jaata hai (Microsoft ki free edge-tts awaaz). Emotion apne aap aata hai:
mood tag (`{funny}` `{angry}` `{sad}` `{scary}` `{hype}`) aur emoji se. `*sigh*` / `uff` / 😔 = aah, `omg` / 😱 = saans kheenchna,
😭 = rote hue, CAPS ya `!!` = chillana.
Hasi usi awaaz me, asli hasi jaisi (chhote "ha", har ek se pehle saans, pitch upar se girta, aakhir me saans andar):
`haha` / `lol` = normal, `hahaha` / 😂 = badi, `lmao` / 🤣 = zor ki, `heh` / 😏 = chuckle, `hehe` / `xD` / 🤭 = giggle, 😅 = nervous,
`mwahaha` = villain wali (gunj ke saath), 💀 = saans wali hasi, sarcasm me "ha. ha.".
Khud batana ho to message me `{v:angry}` `{v:funny}` `{v:sad}` `{v:cry}` `{v:scary}` `{v:shout}` `{v:whisper}` `{v:excited}`
`{v:surprise}` `{v:nervous}` `{v:sarcastic}` `{v:calm}` `{v:normal}` likho (screen par nahi dikhta).
`# voice_emotion = 1` (normal), `1.4` (zyada), `0.6` (halka), `off`.

## Haath se render

Actions → **Render videos** → Run workflow (khali = saari scripts, ya ek naam jaise `example`).
Video **Releases** me aati hai aur link `links.txt` me likha jaata hai.
