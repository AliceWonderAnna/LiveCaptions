# Oplevercontrole — 13 september 2026

Uitgevoerd op Windows met Python 3.13.9 (64-bit).

Geslaagd:

- Vijf geautomatiseerde tests: stereo/48 kHz naar mono/16 kHz met behoud van
  signaalniveau; langdurige stilte zonder resultaten of bufferopbouw; afronden
  bij pauzes en splitsen bij maximale bloklengte; JSON-herstel en opslaan;
  doorgeven van captions en stoppen van de worker met een testbackend.
- Echte Qt-interface gestart en gerenderd in offscreen-modus. Instellingen en
  overlayafbeeldingen visueel bekeken; show/hide, click-through-vlag en wissen
  van de overlay gecontroleerd. Windows-fonts expliciet geladen in de test,
  omdat de offscreen-driver deze niet automatisch beschikbaar maakte.
- Echte PyAudioWPatch-import en detectie van de standaard WASAPI-loopbackuitgang.
  De echte stream geopend, 100 milliseconden gelezen uitsluitend in RAM en gesloten.
- Echte faster-whisper-import; het standaardmodel `base` gedownload en op CPU
  met int8 geladen. Een door Windows gegenereerde Engelse testzin is met
  ingeschakelde VAD herkend; de verwachte woorden test/caption waren aanwezig.

Testomgeving: PySide6 6.10.2, numpy 2.5.1, scipy 1.17.1,
faster-whisper 1.2.1, PyAudioWPatch 0.2.12.8, CTranslate2 4.8.2.
De installatie gebruikte een tijdelijke omgeving met reeds aanwezige Qt/numpy/scipy.
Een volledig schone installatie via dubbelklik op run.cmd is niet uitgevoerd.

Niet interactief gecontroleerd: muisklikken door de overlay naar een ander
Windows-programma, hotkey-aflevering vanuit een andere app, systeemvakinteractie,
microfoonhardware, Nederlandse herkenningskwaliteit, meerdere monitoren, langdurig
doorlopende media en exclusieve fullscreen-apps. Er is geen gemeten latencygarantie.
De controles testen de echte capture en inferentie afzonderlijk; een volledige
lange playback-naar-overlay sessie is niet uitgevoerd.

De synthetische testaudio, testmodellen, tijdelijke instellingen en testomgeving
zijn niet opgenomen in de distributie. Er is geen gebruikersaudio opgeslagen.
