# Escape room: Laboratorio Aurora

Escape room in Python con interfaccia grafica Tkinter, sviluppata
interamente tramite prompt a ChatGPT (GPT-5.6 Sol) per il corso di
**Intelligenza Artificiale Generativa** (Università Politecnica delle
Marche, A.A. 2025-2026).

Il giocatore esplora una stanza a griglia, raccoglie oggetti e risolve tre
enigmi per ricostruire il codice che apre la porta, entro un tempo limite e
con un numero limitato di vite. Sono previsti tre livelli di difficoltà.

<table>
<tr>
<td width="50%"><img src="img/prompt19_1.png" width="100%"/></td>
<td width="50%"><img src="img/prompt18_2.png" width="100%"/></td>
</tr>
<tr>
<td align="center"><em>Schermata iniziale</em></td>
<td align="center"><em>Partita in corso</em></td>
</tr>
</table>

## Come è nato il progetto

Il gioco non è stato scritto a mano: è il risultato di **20 prompt**
inviati in sequenza al modello, applicando il prompt engineering in modo
iterativo.

1. **Prompt 1–2 – enigmi.** Il modello progetta i tre enigmi, gli oggetti e
   l'indizio sull'ordine delle cifre, in formato JSON (`codice/enigmi.json`).
2. **Prompt 3 – prima versione.** Il modello scrive il gioco di base a
   partire dal file degli enigmi.
3. **Prompt 4–20 – modifiche.** Ogni richiesta parte dalla versione
   precedente, corregge un problema o aggiunge una funzionalità e chiede di
   lasciare invariato il resto.

Dopo ogni prompt la versione ottenuta è stata salvata ed eseguita: in questo
modo il repository mostra come il gioco è cambiato richiesta dopo richiesta.

## Organizzazione del repository

```
escape-room-laboratorio-aurora/
├── README.md
├── requirements.txt          # dipendenze per aprire il notebook
├── gen_ai.ipynb              # i 20 prompt, con file e schermate di ogni versione
├── codice/
│   ├── enigmi.json           # enigmi, oggetti e indizi generati dal modello
│   ├── prompt03.py           # prima versione del gioco
│   ├── prompt04.py … prompt16.py
│   ├── prompt16_prima_versione.py
│   ├── prompt17_18.py
│   ├── prompt19.py
│   └── prompt20.py           # versione finale
└── img/
    ├── prompt01_1.png        # schermate, numerate come i prompt
    └── …
```

**`gen_ai.ipynb`** è il punto di partenza. Per ogni prompt riporta:

- il motivo della richiesta, cioè quale problema della versione precedente
  si voleva risolvere;
- il testo esatto inviato al modello;
- il file con il codice ottenuto;
- due schermate del risultato, affiancate;
- una cella che avvia quella versione del gioco.

**`codice/`** contiene una versione del gioco per ogni prompt. Il numero nel
nome del file è il numero del prompt che l'ha prodotta: `prompt07.py` è il
codice ottenuto con il Prompt 7. Ogni file è un programma completo e
indipendente, che legge `enigmi.json` dalla stessa cartella. Fanno eccezione:

- `prompt16_prima_versione.py`: primo tentativo del Prompt 16 (emoji),
  corretto in `prompt16.py`;
- `prompt17_18.py`: i Prompt 17 (notifiche a fumetto) e 18 (schermata
  iniziale) sono stati salvati in un unico file.

**`img/`** contiene le schermate. `promptNN_1.png` e `promptNN_2.png` sono le
due immagini del Prompt NN.

### Elenco dei prompt

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
| 16 | Emoji | `codice/prompt16.py` |
| 17–18 | Notifiche a fumetto e schermata iniziale con livelli | `codice/prompt17_18.py` |
| 19 | Grafica della schermata iniziale | `codice/prompt19.py` |
| 20 | Ritorno alla schermata iniziale | `codice/prompt20.py` |

Note:

- `prompt08.py` ha il tempo limite a 10 secondi invece di 10 minuti: è un
  valore usato per provare la sconfitta allo scadere del tempo.
- `prompt10.py` contiene già anche le attese dei Prompt 11 e 12: le versioni
  sono state salvate in un ordine diverso da quello delle richieste.

## Requisiti

- **Python 3.10 o successivo.**
- **Tkinter**, la libreria grafica usata dal gioco. Non si installa con
  `pip`:
  - **Windows:** è inclusa nell'installer di python.org;
  - **macOS:** è inclusa nell'installer di python.org; con Homebrew serve
    `brew install python-tk`;
  - **Linux (Debian/Ubuntu):** `sudo apt install python3-tk`.

  Per verificare che sia presente:

  ```bash
  python3 -m tkinter
  ```

  Se si apre una piccola finestra, Tkinter funziona.

Il gioco non usa altre librerie esterne. `requirements.txt` serve solo per
aprire il notebook.

## Avvio

### Solo il gioco

Dalla cartella del repository:

```bash
python3 codice/prompt20.py
```

Per provare una versione precedente basta cambiare il numero del file, ad
esempio `python3 codice/prompt09.py`.

### Notebook

1. Crea e attiva un ambiente virtuale:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   ```

2. Installa le dipendenze:

   ```bash
   pip install -r requirements.txt
   ```

3. Apri il notebook:

   ```bash
   jupyter notebook gen_ai.ipynb
   ```

4. Esegui la prima cella di codice, che definisce la funzione `avvia`. Poi
   esegui la cella sotto il prompt che ti interessa, ad esempio
   `avvia("codice/prompt20.py")`. Il gioco si apre in una finestra
   separata.

## Comandi di gioco

| Tasto | Azione |
|---|---|
| Frecce | Muovono il giocatore |
| E | Interagisce con l'oggetto o la porta adiacente |

## Autori

Valeria Cannone, Alessandro Pettinaro, Giada Remedia
