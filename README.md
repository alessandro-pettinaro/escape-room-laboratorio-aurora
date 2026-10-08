# Escape room: Laboratorio Aurora

Escape room in Python con interfaccia grafica Tkinter, sviluppata
interamente tramite prompt a ChatGPT (GPT-5.6 Sol) per il corso di
**Intelligenza Artificiale Generativa** (Università Politecnica delle
Marche, A.A. 2025-2026).

Il giocatore esplora una stanza a griglia, raccoglie oggetti e risolve tre
enigmi per ricostruire il codice che apre la porta, entro un tempo limite e
con un numero limitato di vite. Sono previsti tre livelli di difficoltà.

![Schermata iniziale](img/prompt19_1.png)

## Struttura

```
.
├── gen_ai.ipynb          # i 20 prompt, con codice e schermate di ogni versione
├── codice/
│   ├── enigmi.json       # enigmi generati dal modello (Prompt 1–2)
│   ├── prompt03.py       # una versione del gioco per ogni prompt
│   ├── ...
│   └── prompt20.py       # versione finale
└── img/                  # schermate, numerate come i prompt
```

| Prompt | Richiesta | File |
|---|---|---|
| 1–2 | Generazione e correzione degli enigmi | `codice/enigmi.json` |
| 3 | Prima versione del gioco | `codice/prompt03.py` |
| 4 | Ordine delle cifre | `codice/prompt04.py` |
| 5 | Notifiche sulla mappa | `codice/prompt05.py` |
| 6 | Riquadro dell'inventario | `codice/prompt06.py` |
| 7 | Stanza generata casualmente | `codice/prompt07.py` |
| 8 | Tempo limite | `codice/prompt08.py` |
| 9 | Vite | `codice/prompt09.py` |
| 10 | Finestra di fine partita | `codice/prompt10.py` |
| 11 | Attesa dopo un errore | `codice/prompt11.py` |
| 12 | Aggiornamento dei secondi di attesa | `codice/prompt12.py` |
| 13 | Pannello sotto la mappa | `codice/prompt13.py` |
| 14 | Pulsante "Termina partita" | `codice/prompt14.py` |
| 15 | Pulsante "Ricomincia" | `codice/prompt15.py` |
| 16 | Emoji | `codice/prompt16.py` (primo tentativo: `prompt16_prima_versione.py`) |
| 17–18 | Notifiche a fumetto e schermata iniziale con livelli | `codice/prompt17_18.py` |
| 19 | Grafica della schermata iniziale | `codice/prompt19.py` |
| 20 | Ritorno alla schermata iniziale | `codice/prompt20.py` |

Note:

- `prompt08.py` ha il tempo limite a 10 secondi, un valore usato per provare
  la sconfitta allo scadere del tempo.
- `prompt10.py` contiene anche le attese dei Prompt 11 e 12: le versioni sono
  state salvate in un ordine diverso da quello delle richieste.

## Avvio

Serve Python 3 con Tkinter (incluso nell'installazione standard su macOS e
Windows; su Linux `sudo apt install python3-tk`).

```bash
python3 codice/prompt20.py
```

Ogni versione legge `enigmi.json` dalla propria cartella. Dal notebook, ogni
versione si avvia con la funzione `avvia(...)`.

## Autori

Valeria Cannone, Alessandro Pettinaro, Giada Remedia
