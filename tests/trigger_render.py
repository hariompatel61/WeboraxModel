import requests
import json

script = """
## 🎬 Scene 1 — Opening Cinematic Shot

**Visual:**
Drone shot of Indian Parliament in 3D cartoon style. Dramatic music like a reality show intro. Spotlights in sky.

**Narrator (deep sarcastic tone):**
"Swagat hai aapka duniya ke sabse bade reality show mein… jahan script public likhti hai… aur acting neta karte hain…"

---

## 🎬 Scene 2 — Inside Parliament Arena

**Visual:**
Parliament turned into WWE arena. Name plates glowing. Narendra Modi adjusting mic confidently. Rahul Gandhi flipping notes upside down. Arvind Kejriwal coughing wearing muffler. Yogi Adityanath sitting serious. Amit Shah observing like chess master.

**Narrator:**
"Aaj ka mudda: Mehngai… berozgari… aur reels banati hui rajneeti."

---

## 🎬 Scene 3 — Inflation Discussion

**Visual:**
Petrol pump meter spinning like fan. Price board showing absurd numbers.

**Rahul Gandhi (confused):**
"Yeh petrol hai ya crypto? Roz naya high bana raha hai."

**Modi (smiling cinematic close-up):**
"Mitron… petrol mehnga nahi hua… aapki expectations sasti ho gayi hain."

---

## 🎬 Scene 4 — Education and Jobs

**Visual:**
Students holding degrees that turn into paper planes flying away.

**Kejriwal:**
"School bana diye, hospital bana diye… par naukri ka server down kyun hai?"

**Amit Shah (calm):**
"System upgrade chal raha hai… 2047 tak restart ho jayega."

---

## 🎬 Scene 5 — Law and Order

**Visual:**
Yogi walking in slow motion, bulldozer transforming into superhero robot behind him.

**Yogi:**
"Jahan kanoon so raha hai… wahan bulldozer jag raha hai."

---

## 🎬 Scene 6 — Social Media Politics

**Visual:**
All leaders making reels on phones. Modi doing cinematic wave shot. Rahul trying multiple retakes. Kejriwal adding subtitles. Shah checking analytics. Yogi standing still but reel goes viral anyway.

**Narrator:**
"Desh ke issues pending hain… par reels trending hain."

---

## 🎬 Scene 7 — Common Man Cutaway

**Visual:**
A middle-class family watching TV, electricity bill in hand. Common man looking frustrated.

**Common Man:**
"EMI hum bharein… debate yeh karein… aur reel pe caption — Desh badal raha hai."

---

## 🎬 Scene 8 — Parliament Chaos Montage

**Visual:**
Fast cuts of papers flying, desk banging, mic muting, camera zooms, meme reactions popping on screen.

**Narrator:**
"Yahan bill pass ho ya na ho… blame pass zaroor hota hai."

---

## 🎬 Scene 9 — Climax Satire

**Visual:**
All leaders standing for press photo. Camera flash. Background changes to green screen showing Election Coming Soon.

**Rahul Gandhi:**
"Alliance karein?"

**Modi:**
"Challenge accepted."

**Kejriwal:**
"Press conference ready hai."

**Amit Shah:**
"Calculation already ho chuki hai."

**Yogi:**
"Result aane do…"

---

## 🎬 Scene 10 — Punchline Ending

**Visual:**
Public holding remote control labelled Vote. Crowd with voting power. Text on screen: Season khatam nahi hua interval chal raha hai.

**Narrator (serious plus sarcastic mix):**
"Reality show unka hai… par remote aapke haath mein hai."
"""

r = requests.post('http://127.0.0.1:8000/api/render-video', json={'script': script})
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")
