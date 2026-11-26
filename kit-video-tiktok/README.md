# Kit vidéo TikTok : 3D en blocs, voix off française, rafales « HUSS »

Ce kit fabrique une vidéo verticale 1080×1920 d'environ 60 s, entièrement par code et sans service payant :

1. Il génère les voix off françaises avec Kokoro, en local, puis applique l'intonation réglée dans `voice_profile.json`.
2. Il vérifie la prononciation avec Whisper.
3. Il fait le rendu 3D (three.js, personnages en blocs) image par image, à 25 images/s.
4. Il génère la musique et les bruitages, puis mixe le tout.
5. Il produit le fichier final `video_finale.mp4`.

L'histoire fournie en exemple, « Le gardien de Boulanville », est originale. Remplacez-la par la vôtre.

---

## 1. Installation (une seule fois)

Il faut au préalable :

- Python 3.10 ou plus récent ;
- Node 18 ou plus récent ;
- `ffmpeg`, compilé avec `rubberband`. Sous Ubuntu : `sudo apt install ffmpeg`. Sous macOS : `brew install ffmpeg`.

Ensuite :

```bash
bash setup.sh
```

Le script installe les paquets Python et Node, ainsi que Chromium pour le rendu. Il télécharge aussi le modèle de voix Kokoro, environ 340 Mo, dans `models/kokoro/`.

## 2. Fabriquer la vidéo

```bash
bash build.sh
```

| Étape | Fichier | Durée indicative (CPU) |
|---|---|---|
| Voix et timeline | `tts.py` → `build/audio/*.wav`, `build/timeline.json` | 1 à 2 min |
| Contrôle de prononciation | `check_pronunciation.py` | 1 min (le modèle Whisper, 480 Mo, est téléchargé au 1er lancement) |
| Rendu 3D | `render.js` → `build/video.mp4` | 5 à 10 min |
| Mixage audio | `mix.py` → `build/mix.wav` | 10 s |
| Montage final | `ffmpeg` → **`video_finale.mp4`** | 5 s |

Pour voir quelques images fixes sans lancer tout le rendu, par exemple aux secondes 3,2 et 10,5 :

```bash
python3 tts.py && cat parts/*.html > index.html && node render.js stills 3.2 10.5   # → build/still_3.2.jpg …
```

---

## 3. Écrire votre histoire : `script.json`

Le fichier contient une ligne par réplique, lues dans l'ordre :

```json
{"id": "intro", "who": "N", "mood": "excited", "text": "À Boulanville, tout le monde adore le foot. Tout le monde... sauf *Timéo*.", "pad": 0.1},
{"id": "b1", "who": "N", "huss": true, "text": "*Huss ! Huss !*", "pad": 0.3},
{"id": "v1", "who": "V", "mood": "excited", "text": "Timéo ! Arrête de sauter sur ma voiture !", "pad": 0.2}
```

| Champ | Rôle |
|---|---|
| `id` | Nom unique de la réplique. La mise en scène s'y réfère, voir §4. |
| `who` | Voix à utiliser : `N` narrateur, `C` coach, `V` voisin, ou une voix que vous ajoutez dans `voice_profile.json`. |
| `mood` | Change le débit : `normal`, `excited`, `hype`, `sad`, `deadpan`, `suspense`. |
| `text` | Texte du sous-titre. Les mots entre `*étoiles*` s'affichent en jaune et en gros. |
| `say` | Facultatif. Texte réellement prononcé, quand il doit différer du sous-titre. Exemple : `"say": "bé-ère"` pour un sigle. |
| `pad` | Silence ajouté après la réplique, en secondes, avant application de `pad_scale`. |
| `at` | Facultatif. Heure minimale de départ de la réplique, en secondes. |
| `huss` | `true` produit des rafales « HUSS », une par mot « Huss » du texte, au rythme réglé dans `voice_profile.json`. |

**Règles pour une prononciation sans faute :**

- Écrivez les nombres en lettres : « un mètre vingt » et non « 1 m 20 ».
- Lancez `python3 check_pronunciation.py` après `tts.py`. Une ligne marquée `<-- to check` doit être écoutée.
  - Un écart sur un prénom inventé (« Timéo » entendu « Timur ») ou sur des chiffres n'est pas une faute.
  - Un mot courant mal entendu est une faute. Changez le mot ou utilisez `say`. Exemple : « rigole » était lu « rigore » à chaque essai, il a été remplacé par « se moque ».
- Si un mot anglais est mal lu (foot, coach…), ajoutez une correction dans `ipa_fixes` de `voice_profile.json`, au format `[phonèmes produits, phonèmes voulus]`.
  - Pour voir les phonèmes produits : `python3 -c "from kokoro_onnx import Kokoro; K=Kokoro('models/kokoro/kokoro-v1.0.onnx','models/kokoro/voices-v1.0.bin'); print(K.tokenizer.phonemize('le coach', 'fr-fr'))"`

## 4. Mise en scène : `parts/*.html`

`build.sh` assemble les fichiers dans cet ordre pour former `index.html` :

| Fichier | Contenu |
|---|---|
| `a_head.html` | Scène three.js, lumières, helpers (`box`, `panel`, `textTex`, `lerp`, `ease`, `clamp`, `prog`). |
| `b_world.html` | Décors : maisons, arbres, panneaux, stade, buts, foule. |
| `c_chars.html` | Fabrique des personnages en blocs, visages dessinés et fonction `pose()`. |
| `d_cast.html` | La distribution : chaque personnage, avec ses couleurs, sa coiffure et son visage. |
| `e_overlay.html` | Calque 2D : bulles, étiquettes, textes qui « pop ». |
| `f_direction.html` | Sous-titres, plans caméra (`shots()`), animation (`update(t)`), rendu. |

**Plans caméra** (`shots()` dans `f_direction.html`). Chaque plan s'écrit :

```js
[heure_de_début, [caméra départ x,y,z], [caméra fin x,y,z], [regard départ x,y,z], [regard fin x,y,z], champ_de_vision]
```

L'heure se cale sur la voix avec `S('id')`, le début d'une réplique, ou `WT('id', /^mot/)`, l'instant où un mot est prononcé. Le décor suit donc automatiquement si vous changez le texte.

**Personnages** (`d_cast.html`) :

```js
const hero = character('hero', { skin: '#f1c9a5', shirt: '#ff8a3d', pants: '#2a3a6b', hair: 'spiky', hairCol: '#e8b23a',
                                 face: { eyes: 'n', mouth: 'grin', freckles: true, blush: true } });
```

- Coiffures (`hair`) : `short`, `spiky`, `pony`, `bun`, `cap`, `bald`, `pigtails`, `chef`, `hood`.
- Yeux (`eyes`) : `n`, `happy`, `wide`, `closed`.
- Bouche (`mouth`) : `smile`, `grin`, `flat`, `open`.

**Animation** (`update(t)` dans `f_direction.html`) : à chaque image, placez les personnages avec `P(perso, {...})`.

```js
P(hero, { x: 0, z: 0, ry: .3, walk: t * 9, hop: jumpY(t, S('saute'), .6, 1.2), arms: CHEER(t), talk: talk('V', t), face: { mouth: 'open' } });
```

| Paramètre | Effet |
|---|---|
| `x`, `y`, `z` | Position. |
| `ry` | Rotation (orientation du personnage). |
| `s` | Taille. |
| `walk` | Phase de marche. |
| `hop` | Saut. |
| `arms` | Bras. |
| `bend` | Penché. |
| `headX`, `headY`, `headZ` | Tête. |
| `talk` | Ouverture de la bouche. `talk('V', t)` la synchronise sur les répliques de la voix `V`. |
| `face` | Expression du moment. |

## 5. Régler la voix et l'intonation : `voice_profile.json`

| Clé | Effet |
|---|---|
| `mix` | Mélange de voix Kokoro, avec un poids pour chacune. Exemples : `ff_siwis` (française), `am_puck` (énergique), `am_onyx` (grave), `bm_george` (posée). |
| `speed` | Débit de base. 1,12 correspond à un débit TikTok rapide. |
| `intonation.target_median` | Hauteur moyenne de la voix, en Hz. |
| `intonation.down` / `intonation.up` | Amplifie les descentes et les montées de la mélodie. 1 = naturel, 1,5 = très expressif. Au-delà de 1,7, la voix sonne « robot » et Whisper comprend moins bien. |
| `intonation.formant` | Timbre. En dessous de 1, voix plus grosse. Au-dessus de 1, voix plus fine. |
| `huss.offsets` | Instants des 3 « HUSS » d'une rafale, en secondes. |
| `huss.every` | Intervalle entre deux rafales, en secondes. |
| `huss.first_dur` / `huss.other_dur` | Durée de chaque cri. |
| `huss.pitch_hz` | Hauteur des cris. |
| `huss.hiss` | Intensité du « s » final. |
| `gap_s` / `pad_scale` | Rythme général : silences entre les répliques. |

**Calage actuel du narrateur, mesuré sur la vidéo de référence et sur ce que le kit produit :**

| Mesure | Référence | Kit |
|---|---|---|
| Hauteur médiane | 164 Hz | 166 Hz |
| Bas de la voix (10 %) | 104 Hz | 111 Hz |
| Haut de la voix (90 %) | 247 Hz | 246 Hz |
| Amplitude d'intonation | 5,8 demi-tons | 5,4 demi-tons |

Pour mesurer votre propre réglage :

```bash
python3 - <<'EOF'
import json,wave,numpy as np,pyworld as pw
tl=json.load(open('build/timeline.json'))
def f0(p):
    w=wave.open(p);a=np.frombuffer(w.readframes(w.getnframes()),np.int16)/32768.
    f,_=pw.harvest(a,w.getframerate(),f0_floor=60,f0_ceil=500,frame_period=10);return f[f>0]
o=np.concatenate([f0(f"build/audio/{l['id']}.wav") for l in tl['lines'] if l['who']=='N' and not l.get('huss')])
print('médiane',round(np.median(o)),'Hz | p10',round(np.percentile(o,10)),'| p90',round(np.percentile(o,90)),'| demi-tons',round((12*np.log2(o/np.median(o))).std(),2))
EOF
```

---

## 6. Avant de publier

- Sur TikTok, cochez « contenu généré par IA » : la voix est synthétique.
- La musique et les bruitages sont générés par `mix.py`, il n'y a donc aucun droit musical à gérer. Si vous ajoutez une musique du catalogue TikTok, faites-le dans l'application.
- N'utilisez pas la voix d'une personne réelle sans son accord.
