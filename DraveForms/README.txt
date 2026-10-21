DraveForms v0.8
===============

Een PDF-lezer die invulbare formulieren kan invullen (dropdowns, tekstvakken,
vinkjes) EN tekst aan een bestaande PDF kan toevoegen - ook formulieren die
normaal alleen in Adobe werken. Lokaal, offline, gratis (met donatie).

Starten
-------
- Dubbelklik op run.bat. De eerste keer installeert hij zichzelf (Python-pakketten);
  daarna start de app meteen.
- Werkt de eerste keer niet? Draai start-debug.bat (toont de fout) of herstel.bat
  (installeert opnieuw).

Gebruik
-------
- Openen: kies een PDF. Alle pagina's staan nu ONDER ELKAAR; scroll door het
  hele document. De pijlen en het paginanummer springen naar een pagina.
- Invullen: klik op een dropdown en kies; typ in een tekstvak; zet een vinkje.
- Tekst toevoegen: klik op "Tekst toevoegen", klik op de pagina; er opent een
  tekst-editor met grootte (A-/A+), VET (B), CURSIEF (I) en KLEUR. Plaatsen is
  eenmalig (de knop springt vanzelf uit). Geplaatste tekst SLEPEN = verschuiven;
  DUBBELKLIK = bewerken/verwijderen. Grootte en kleur tonen overal; vet/cursief
  tonen in DraveForms.
- Zoom met + / - of "Passend".
- Opslaan / Opslaan als. Ingevulde waarden en toegevoegde tekst zijn in elke
  PDF-lezer zichtbaar, niet alleen in DraveForms.

Een .exe maken (optioneel)
--------------------------
- Draai eerst run.bat (zodat de .venv bestaat), daarna bouw-exe.bat.
- Resultaat: dist\DraveForms.exe (een enkel bestand).

NIEUW in v0.4
-------------
- Tekst toevoegen aan een bestaande PDF (vrije-tekst-annotaties), met
  bewerken/verwijderen.
- Meerdere pagina's: het hele document wordt nu doorlopend getoond
  (voorheen alleen de eerste pagina).
- Dravenlock-huislogo als pictogram en in de koptekst.

NIEUW in v0.5
-------------
- Tekst invoeren via een echt editor-venster: meerdere regels en keuze van
  lettergrootte (met live voorbeeld).
- Geplaatste tekst kun je met de muis verslepen naar de juiste plek.
- Bewerken/verwijderen via hetzelfde venster (knop 'Verwijderen').

NIEUW in v0.6
-------------
- Bewerken gaat nu met DUBBELKLIK (een enkele klik botste met slepen).
- Lettergrootte met duidelijke A- / A+ knoppen (de oude pijltjes deden
  het niet altijd).
- Het invoervenster lijkt nu op een echte tekst-editor (werkbalk + tekstvlak).

NIEUW in v0.7
-------------
- Vet, cursief en kleur voor toegevoegde tekst (knoppen in de editor).
- Toegevoegde tekst is nu een sleepbare widget: SLEPEN = verschuiven,
  DUBBELKLIK = bewerken. Een gewone klik opent niets meer.
- Tekst plaatsen is eenmalig (de knop springt na plaatsen vanzelf uit).

NIEUW in v0.8
-------------
- Grote/brede tekst valt niet meer over elkaar (ruimere regelhoogte; de
  tekst breekt netjes af).
- De A- / A+ knoppen in de editor werken weer (regressie uit v0.7).
- Na opslaan verschijnt een bevestiging dat het bestand is opgeslagen.

Contact / donatie
-----------------
service@dravenlock.nl - paypal.me/roger076
