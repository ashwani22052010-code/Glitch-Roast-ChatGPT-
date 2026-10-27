# ⚔️ 4-AI Cinematic Render

Tumhare **4-AI Cinematic Engine** (ChatGPT / Gemini / Grok / Claude + Battle mode) ki video GitHub Actions par banti hai:
720p se 4K, 30/60 fps, 16:9 ya 9:16, intro, end screen, memes, tumhari apni sounds aur music, aur voice.
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

## Sound effects (beech-beech wale): SIRF TUMHARI

Message ke mood ke hisaab se beech-beech me bajne wale effects ab system ke nahi hain: sirf `sounds/` me tumhari upload ki hui files bajti hain.
Typing / send / reply ki system awaaz rehti hai (apni upload karo to wo). Background music sirf `music/` se (code wala mood music band).
Intro aur end screen: smooth text (glitch nahi), naram bubble awaaz ke saath. `sounds/bubble.mp3` daalo to wahi bajegi.

| Kaise | Kya hota hai |
|---|---|
| `sounds/vine_boom.mp3` upload, message me `{vine_boom}` | us message par wahi sound |
| `sounds/funny_1.mp3`, `funny_2.mp3` ... | `funny` group: tag `{funny}` ya auto (joke / 😂 par) - har baar alag, repeat nahi |
| aur group: `roast` `angry` `sad` `scary` `mystery` `hype` `surprise` `awkward` `fail` `win` `money` `love` `tech` `party` `sarcastic` `dead` `clown` `neutral` `question` ... | naam `group_1`, `group_2` rakho |
| `music/bgm.mp3` + `# bgm = bgm` | background music loop me (`# bgm_vol = 0.14`) |

`{nosfx}` = us message par kuch nahi. `# sfx = 0.6` = effects dheeme (`off` = band), `# sfx_auto = off` = sirf tag wale.
Jis tag ki file upload nahi hui, wo chup rehta hai aur render log me uska naam aa jaata hai.

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
Kuch na likho to: file repo me hai to wahi bajti hai, warna system wali. Tumhari sound ki zor apne aap baaki awaazon jitni kar di jaati hai.

## Human mode (naya, default ON)

`# human = on` (likha na ho to bhi on). User ki typing insaan jaisi: har akshar ki speed alag, kabhi akshar galat (paas wali key)
-> 1-2 akshar aage -> ruk ke mita ke sahi, kabhi poora shabd galat (`teh`, `becuase`, `their`/`there`...) -> laal lehar -> mita ke dobara.
Comma / full stop par saans, beech me kabhi soch ke rukna, aur rukte hi typing ki awaaz bhi ruk jaati hai.
Messages ka time bhi har baar alag: ChatGPT ka lamba reply = user zyada der padhta hai phir likhta hai, lamba reply = ChatGPT zyada sochta hai.
`# human = off` = purana seedha ek jaisa flow. (Purana `laptop` mode hata diya.)

## Intro / end screen ka size

`# intro_text = Glitch Roast`  `# intro_size = 7.8` (screen ki chaudai ka %, 3-16). Bada ho to apne aap fit.
`# end_size = 1.0` (0.5-2.2) = end screen ka text chhota / bada. Dashboard me dono ka 16:9 preview hai.

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
