# Live Captions — Windows 0.6.1

Een kleine lokale Python-app voor instelbare ondertiteling over andere vensters.
Geen permanent zwart vlak: standaard witte tekst met zwarte contour, 25% zwarte
achtergrond, twee regels. Zet achtergronddekking op 0% voor uitsluitend tekst.

## Starten

1. Pak de volledige ZIP uit naar een schrijfbare map, bijvoorbeeld Documenten.
2. Installeer **Python 3.12 64-bit** (3.11 en 3.13 worden ook geaccepteerd).
   Gebruik https://www.python.org/downloads/windows/ en installeer de launcher/PATH-optie.
3. Dubbelklik **run.cmd**. De eerste keer installeert het de dependencies in `.venv`.
4. Kies bron en taal en druk op **Start captions**. Standaard: systeemaudio,
   Nederlands, Whisper `base` op CPU. Eerste gebruik downloadt het model.
   Voor **twee VLC-kanalen** tegelijk: zie [docs/SETUP_MULTICHANNEL.md](docs/SETUP_MULTICHANNEL.md)
   (VoiceMeeter Banana) en start `start-vlc1.cmd` + `start-vlc2.cmd`.
5. Speel spraak af. De overlay werkt tussentekst bij (standaard elke 0,5 s) tijdens
   spraak, en rondt af na een korte pauze (standaard 0,25 s). Whisper draait op CPU
   met tot 8 threads.

**demo.cmd** opent dezelfde interface zonder modeldownload of audio-opname.
De Python-pakketten worden bij de eerste start wel geïnstalleerd. Klik Voorbeeld / slepen.
Dit is een broncodepakket, geen zelfstandige EXE; de ZIP zelf is klein, maar de
afhankelijkheden en modellen kunnen honderden MB's tot meer dan een GB gebruiken.

## Bediening

- **Voorbeeld / slepen** toont 15 seconden voorbeeldtekst en schakelt click-through uit.
  Sleep de tekst; positie wordt bewaard. Schakel daarna click-through weer in.
- **Ctrl+Alt+H:** overlay tonen/verbergen. Dit pauzeert audioherkenning niet.
- **Ctrl+Alt+C:** click-through aan/uit. Bij ingeschakelde modus gaan klikken naar de app eronder.
- **Ctrl+Alt+S:** instellingen openen.
- **Stop captions:** stopt opname, wist zichtbare tekst en wacht een lopende
  modelbewerking af. Tijdens een eerste modeldownload kan stoppen langer duren.
- **Afsluiten:** sluit de app en achtergrondwerkers. Het consolevenster sluit ook.
- Het kruisje van Instellingen verbergt het venster naar het systeemvak als dat
  beschikbaar is. Rechtsklik op het CC-icoon voor starten, stoppen en afsluiten.
- **Positie herstellen** zet de overlay terug op het primaire scherm.

Lettertype, grootte, tekstkleur, achtergronddekking, vensterdekking, breedte,
1–12 regels en verdwijnvertraging werken direct. **Tekst blijft zichtbaar**
schakelt auto-verbergen uit. **Monoloog opbouwen** houdt afgeronde zinnen als
één blok in beeld (alleen in RAM; geen transcriptbestand). Vensterdekking
beïnvloedt ook de tekst; gebruik achtergronddekking om alleen het zwarte vlak
transparant te maken. Bron, taal, model en audio-instellingen kunnen worden
aangepast wanneer opname gestopt is.

## Wat dit MVP doet en waar de grens ligt

De werkelijke backend is **faster-whisper**, geen gesimuleerde transcriptie.
RealtimeSTT gebruikt deze engine ook voor zijn algemene standaardpad. Rechtstreekse
integratie houdt dit pakket eenvoudiger; RealtimeSTT is hier geen optionele plug-in.
Je hoeft geen API-key, betaalde dienst, CUDA of los FFmpeg-programma te installeren.

- Systeemaudio wordt via **PyAudioWPatch / WASAPI loopback** opgenomen van het
  standaard Windows-uitvoerapparaat. Je kunt ook een **specifiek apparaat**
  kiezen (bijv. Voicemeeter VAIO/AUX) voor gescheiden kanalen.
- Microfoon is een alternatieve bron. Meerdere Live Captions-instances met
  `--profile vlc1` / `--profile vlc2` gebruiken elk een eigen `settings-*.json`.
  Voor gescheiden VLC-audio + mix terug naar speakers: VoiceMeeter Banana
  ([docs/SETUP_MULTICHANNEL.md](docs/SETUP_MULTICHANNEL.md)).
- Audio wordt naar mono 16 kHz omgezet. Tijdens spraak verschijnt **tussentekst**
  (instelbaar, standaard 0,5 s); bij een pauze of het maximale spraakblok volgt
  een afronding. Eerdere woorden in een zin kunnen nog iets bijgesteld worden.
  Bij een harde split na `max_seconds` kan een woord nog geknipt worden. Zonder
  monoloog-modus tonen de laatste 1–12 visuele regels van het nieuwste resultaat;
  met monoloog-modus groeit de tekst tot die regelruimte (oudere regels scrollen
  uit beeld). Er is geen scrollend transcriptbestand.
- Automatisch verbergen gebeurt na de ingestelde tijd sinds het laatste
  captionresultaat (standaard 2,5 seconden), tenzij **Tekst blijft zichtbaar**
  aan staat. Door herkenningsvertraging is dat niet precies hetzelfde moment als
  de stilte in de originele audio.
- Een energiedrempel plus Whisper's spraakfilter onderdrukken stilte. Muziek,
  ruis en zachte stemmen kunnen nog foutieve of ontbrekende tekst opleveren.
- Een wachtrij van één job houdt de overlay bij de nieuwste audio. Als de CPU
  het niet bijhoudt, wordt ouder werk overgeslagen. Kies `tiny` voor snelheid;
  `small` kost meer tijd en geheugen. CUDA/Intel-GPU wordt in 0.6.1 niet gebruikt.
  Twee instances ≈ 2× CPU; gebruik `tiny` als het achterloopt.
- Globale sneltoetsen zijn gedeeld tussen instances; bij twee vensters kunnen
  ze botsen — gebruik tray/knoppen per profile.
- Always-on-top is bedoeld voor normale/borderless Windows-vensters. Exclusief
  fullscreen games, beveiligde schermen en sommige beschermde audio kunnen dit blokkeren.
- Sneltoetsen zijn globaal, vast ingesteld en hebben geen administratorrechten
  nodig. Bij conflicten meldt de app dit; de systeemvakacties blijven beschikbaar.

## Privacy en bestanden

Audio en herkende tekst blijven alleen tijdelijk in RAM. De app maakt geen
audiofiles, transcriptbestanden of transcriptlogs. Er is geen opslagoptie voor
transcripts. Alleen **settings.json** wordt naast de app opgeslagen; de algemene
modelcache van Hugging Face wordt gebruikt voor modelbestanden. Installatie en
eerste modeldownload vereisen internet. Met geïnstalleerde pakketten en een
gecachet model gebeurt herkenning lokaal. Foutmeldingen tonen technische details,
geen opzettelijk gelogde transcripties. Een lopend, onafgemaakt spraakblok wordt
bij stoppen weggegooid.

## Problemen oplossen

- Geen systeemgeluid: controleer het standaard uitvoerapparaat in Windows.
  Stop/start captions nadat je een headset of andere uitgang hebt gekozen.
- Geen microfoon: controleer Windows > Privacy en beveiliging > Microfoon en
  toegang voor bureaubladapps; controleer de standaardmicrofoon.
- Alleen zachte spraak mist: verlaag de spraakdrempel, bijvoorbeeld van 0.006 naar 0.003.
- DLL-fout tijdens import: installeer de Microsoft Visual C++ Redistributable
  2015–2022 x64 vanaf Microsoft en probeer opnieuw.
- Downloadfout: controleer toegang tot Hugging Face en je internetverbinding.
- Mislukte installatie: gebruik 64-bit Python 3.12. Open een terminal in de map
  en voer `.venv\Scripts\python.exe -m pip install -r requirements.txt` uit.
- Tekst zoek: gebruik Ctrl+Alt+S, Positie herstellen, Voorbeeld / slepen.
- Beschadigde instellingen: hernoem settings.json; de app maakt nieuwe defaults.

## Ontwikkeling en controles

`python -m unittest discover -s tests -v` controleert audioconversie, segmentatie,
configuratieherstel en de levenscyclus met een fake backend. `python app.py --demo
--smoke-test` opent kort de echte interface zonder microfoon of model.
Zie VALIDATION.md voor wat bij oplevering daadwerkelijk gecontroleerd is.

## Gebruikte documentatie

- RealtimeSTT: https://github.com/KoljaB/RealtimeSTT
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- WASAPI loopback: https://github.com/s0d3s/PyAudioWPatch

De Python-pakketten hebben hun eigen licenties. Dit pakket bevat de appbroncode;
dependencies en modellen worden bij gebruik afzonderlijk gedownload.
