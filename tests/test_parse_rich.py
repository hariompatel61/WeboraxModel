import sys
sys.path.append('src')
from app import parse_script

script = """
## 🎬 Scene 1 — Opening Cinematic Shot

**Visual:**
Drone shot of Indian Parliament in 3D cartoon style. Dramatic music like a reality show intro. Spotlights in sky.

**Narrator (deep sarcastic tone):**
"Swagat hai aapka duniya ke sabse bade reality show mein… jahan script public likhti hai… aur acting neta karte hain…"

---

## 🎬 Scene 2 — Inside Parliament Arena

**Visual:**
Parliament turned into WWE arena. Name plates glowing.

* Narendra Modi adjusting mic confidently
* Rahul Gandhi flipping notes upside down
* Arvind Kejriwal coughing, wearing muffler
* Yogi Adityanath sitting serious
* Amit Shah observing like chess master

**Narrator:**
"Aaj ka mudda: Mehngai… berozgari… aur reels banati hui rajneeti."

---

## 🎬 Scene 3 — Inflation Discussion

**Visual:**
Petrol pump meter spinning like fan.

**Rahul Gandhi (confused):**
"Yeh petrol hai ya crypto? Roz naya high bana raha hai."

**Modi (smiling cinematic close-up):**
"Mitron… petrol mehnga nahi hua… aapki expectations sasti ho gayi hain."

Audience laugh track.

---

## 🎬 Scene 4 — Education & Jobs

**Visual:**
Students holding degrees → degrees turning into paper planes.

**Kejriwal:**
"School bana diye, hospital bana diye… par naukri ka server down kyun hai?"

**Amit Shah (calm):**
"System upgrade chal raha hai… 2047 tak restart ho jayega."

---

## 🎬 Scene 5 — Law & Order

**Visual:**
Yogi walking in slow motion, bulldozer transforming into superhero robot.

**Yogi:**
"Jahan kanoon so raha hai… wahan bulldozer jag raha hai."

Background: dramatic anime wind effect.
"""

scenes = parse_script(script)
print(f"Parsed {len(scenes)} scenes")
for s in scenes:
    vis = s['visual'][:70].replace('\n', ' ')
    nar = s['narration'][:90].replace('\n', ' ')
    print(f"  Scene {s['id']}: visual='{vis}...' narration='{nar}...'")
