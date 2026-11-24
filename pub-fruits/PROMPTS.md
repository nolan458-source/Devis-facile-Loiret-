# Pub « Fruits frais » — 60 s, 16:9 — Pack de production IA

Pipeline : 1 image de référence par scène (text-to-image) → image-to-video (8–10 s) → montage + audio.
Outils compatibles : Veo 3, Sora 2, Kling 2.x, Runway Gen-4, Luma Ray. Prompts en anglais (meilleure adhérence des modèles).

## Paramètres communs
- Format 16:9, 1920×1080 min (4K si disponible), 24 fps, durée 10 s par plan (si limite à 8 s : générer 8 s et ralentir à 80 % au montage).
- **Suffixe à ajouter à chaque prompt :**
  `photorealistic commercial food cinematography, shot on ARRI Alexa 65 with 100mm macro lens, shallow depth of field, natural skin and pulp textures, true-to-life colors, crisp 4K detail, smooth slow motion 120fps look, no text, no logo, no people, no hands`
- **Negative prompt :**
  `text, letters, logo, watermark, subtitles, human, hand, fingers, knife held by hand, cartoon, CGI look, plastic texture, oversaturated, morphing, shape change, melting, extra fruit parts, duplicated fruit, warped proportions, flicker, blurry`
- Seed fixe par scène, garder les images de référence pour verrouiller l'apparence des fruits (réutilisées en scènes 5–6).

---

## Scène 1 — 0:00–0:10 — Fraise
**Image de référence :**
`Extreme macro of a single glossy red strawberry with green calyx, tiny water droplets on its surface, one larger droplet near the top, dark blurred background, soft natural window light from the left`
**Vidéo :**
`Extreme macro shot: a single water droplet slowly slides down the glossy surface of a ripe red strawberry, tracing between the seeds. The camera dollies in very slowly toward the fruit. Soft natural side light, deep black softly blurred background, cinematic shallow depth of field, ultra detailed seeds and surface texture.`
**Sortie de plan :** fin en très gros plan sur le rouge → fondu enchaîné couleur vers scène 2.

## Scène 2 — 0:10–0:20 — Orange
**Image :** `A fresh whole orange suspended in mid-air against a dark background, highly detailed dimpled peel with a light film of moisture, warm golden rim light`
**Vidéo :**
`A fresh orange slowly rotates in mid-air against a dark background. Its dimpled peel is highly detailed and slightly wet. Small water droplets spin off its surface in slow motion and catch the light. Warm dramatic golden key light with strong rim light, cinematic contrast, camera slowly orbits slightly.`

## Scène 3 — 0:20–0:30 — Kiwi
**Risque :** une coupe « sans main » est physiquement ambiguë ; les modèles inventent souvent une main ou déforment le fruit. Solution : lame fixe, le kiwi tombe dessus, OU on montre les deux moitiés qui s'écartent.
**Image :** `A whole kiwi fruit on a dark slate surface, studio lighting, premium food advertising`
**Vidéo :**
`Slow motion: a whole kiwi splits cleanly in half and the two halves gently fall apart, revealing bright green juicy flesh, a pale creamy core and a ring of small black seeds, tiny drops of juice glistening. The camera performs a slow circular orbit around the kiwi. Dark slate surface, high-end food commercial lighting, no knife holder, no hands.`
Alternative plus fiable : générer directement les deux moitiés posées + orbite, et faire la « coupe » par raccord de montage.

## Scène 4 — 0:30–0:40 — Pomme
**Image :** `A shiny red apple frozen in mid-air just above perfectly clear water in a glass tank, black studio background, studio strobe lighting`
**Vidéo :**
`Extreme close-up slow motion: a shiny red apple drops into perfectly clear water. A large realistic splash crown forms around the fruit, with air bubbles and droplets suspended in the air, accurate fluid physics. Studio lighting with crisp highlights on the water, black background, ultra precise detail.`

## Scène 5 — 0:40–0:50 — Ballet de fruits
**Image :** `A strawberry, an orange, a kiwi, a red apple, a bunch of green grapes, a mango, a small pineapple and a wedge of watermelon floating in a circle in a dark elegant space, water droplets and tiny glowing particles in the air, soft studio light`
**Vidéo :**
`In a dark elegant space, fresh fruits appear one by one and float: strawberry, orange, kiwi, red apple, bunch of grapes, mango, pineapple and a watermelon wedge. They slowly orbit around the center of the frame. Floating water droplets and tiny glowing particles fill the air. Each fruit keeps its natural size and shape. Cinematic soft light, shallow depth of field.`
**Risque élevé** (8 objets = dérives de forme fréquentes). Si échec : générer 2 plans de 5 s avec 4 fruits chacun, ou composer les fruits en couches (fond noir → détourage → After Effects/DaVinci Fusion).

## Scène 6 — 0:50–1:00 — Composition finale
**Image (= dernière image du plan, à générer en premier) :**
`A beautiful colorful still-life composition of fresh strawberries, orange halves, kiwi halves, a red apple, grapes, mango, pineapple and watermelon, glossy with water droplets, centered on a dark background, soft cinematic light, premium food advertising`
**Vidéo (mode first+last frame si disponible) :**
`The floating fruits quickly converge to the center and settle into a beautiful colorful composition. The camera then slowly pulls back to reveal the whole arrangement. Fruits are perfectly fresh, glossy and appetizing with water droplets. The shot ends on a locked-off static frame with soft cinematic light.`
Plan fixe final : prolonger la dernière image 3 s (freeze + léger zoom 1 %) au montage si le modèle ne tient pas l'immobilité.

---

## Audio
| Temps | Musique | Sound design |
|---|---|---|
| 0–10 | Nappe ambient, piano/pad, 90 → 100 BPM implicite | goutte, micro-ruissellement |
| 10–20 | Entrée kick léger + pluck | whoosh de rotation, gouttes projetées |
| 20–30 | Basse + percussions | « crunch » humide de la coupe |
| 30–40 | Build (riser) | plongeon + splash, bulles |
| 40–50 | Full drop, synthés aériens | scintillements, whooshes doux |
| 50–60 | Climax puis résolution 55 s, queue de reverb | impact feutré à la convergence, silence/ambiance sur le plan fixe |
Sources : Suno/Udio (prompt : `modern uplifting electronic commercial track, clean and fresh, gradual build from ambient pads to a confident climax at 50 seconds, resolves softly at 60 seconds, 60 seconds long`), SFX via ElevenLabs Sound Effects ou banque libre. Veo 3 génère aussi l'audio natif par plan, mais la musique doit être continue : la faire séparément.

## Montage (ffmpeg)
Placer `s1.mp4 … s6.mp4` (10 s chacun) et `audio.wav` (60 s) dans ce dossier, puis :
```bash
./assemble.sh
```
Fondus enchaînés de 0,5 s entre plans (les transitions sont absorbées en compensant : chaque plan doit faire ≥ 10,5 s, sinon la vidéo fera 57,5 s).

## Contrôle qualité (avant export)
1. Lire image par image les 0,5 s autour de chaque transition : aucune forme qui « fond ».
2. Vérifier l'absence de main/texte/watermark sur chaque plan (les versions gratuites des outils ajoutent souvent un watermark → plan payant requis).
3. Durée finale : `ffprobe -v error -show_entries format=duration -of csv=p=0 pub_fruits_60s.mp4` → ≈ 60.0.
