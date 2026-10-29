# Multi-kanaal captions (2× VLC via VoiceMeeter Banana)

Live Captions kan **niet** zelf virtuele kabels aanmaken (dat zijn Windows-drivers).
Gebruik **VoiceMeeter Banana** (gratis, VB-Audio) om elk VLC-venster naar een
aparte virtuele uitgang te sturen, captions per kanaal te maken, en het geluid
weer samen naar je speakers te mixen.

Download: https://vb-audio.com/Voicemeeter/banana.htm

## Signaalpad

```
VLC 1  →  Voicemeeter VAIO  ──┐
                              ├→  Hardware Out A1 (speakers/headset)
VLC 2  →  Voicemeeter AUX   ──┘
              │
              ├→ LiveCaptions --profile vlc1  (luistert VAIO)
              └→ LiveCaptions --profile vlc2  (luistert AUX)
```

## Stappen

1. Installeer **VoiceMeeter Banana** en herstart Windows als de installer dat vraagt.
2. Open VoiceMeeter. Zet **A1** op je echte speakers of headset.
3. Zorg dat de knoppen **A1** aan staan op de strips **VAIO** en **AUX** (anders hoor je ze niet).
4. In **VLC 1**: Audio → Audioapparaat → **Voicemeeter Input** (VAIO).
5. In **VLC 2**: Audio → Audioapparaat → **Voicemeeter Aux Input**.
6. Controleer apparaten:
   ```
   .venv\Scripts\python.exe scripts\check_audio_devices.py
   ```
   Of vanuit de dist-map: start Live Captions en klik **Vernieuwen** bij Audiobron.
7. Start twee Live Captions-instances:
   - `start-vlc1.cmd` → kies het VAIO-loopback/invoer-apparaat
   - `start-vlc2.cmd` → kies het AUX-apparaat
8. Sleep de overlays uit elkaar. Elke instance bewaart eigen positie in
   `settings-vlc1.json` / `settings-vlc2.json`.

## Opmerkingen

- Globale sneltoetsen (Ctrl+Alt+H/C/S) zijn per machine gedeeld; bij twee
  instances kunnen ze botsen. Gebruik tray of knoppen per venster.
- CPU: twee Whisper-instances kosten ongeveer 2× zoveel. Gebruik model **tiny**
  als het achterloopt.
- Zonder VoiceMeeter blijft alleen de standaard WASAPI-systeemmix of microfoon
  beschikbaar (één gemengde bron).
