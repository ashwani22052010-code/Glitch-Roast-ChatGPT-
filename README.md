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

## Haath se render

Actions → **Render videos** → Run workflow (khali = saari scripts, ya ek naam jaise `example`).
Video **Releases** me aati hai aur link `links.txt` me likha jaata hai.
