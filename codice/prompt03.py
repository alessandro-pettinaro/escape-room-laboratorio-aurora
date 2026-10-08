"""Escape room Tkinter. Collocare enigmi.json accanto a questo file."""

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


LATO = 16
CELLA = 38
PORTA = (0, 8)
PARTENZA = (13, 2)


def carica_dati():
    percorso = Path(__file__).resolve().with_name("enigmi.json")
    try:
        with percorso.open("r", encoding="utf-8") as file:
            dati = json.load(file)
        enigmi = []
        for grezzo in dati["enigmi"]:
            testo = grezzo["testo_giocatore"]
            indizi = testo["indizi"]
            prima = [i["testo"] for i in indizi if i["quando"].lower().startswith("prima")]
            dopo = [i["testo"] for i in indizi if i["quando"].lower().startswith("dopo")]
            lettura = [i["testo"] for i in indizi
                       if not i["quando"].lower().startswith(("prima", "dopo"))]
            cifra = grezzo["soluzione"]["cifra_ottenuta"]
            if not isinstance(cifra, int) or not 0 <= cifra <= 9:
                raise ValueError(f"Cifra non valida per l'enigma {grezzo['id']}.")
            enigmi.append({
                "id": grezzo["id"],
                "nome": grezzo["nome"],
                "oggetto_principale": testo["oggetto_principale"],
                "secondo_oggetto": testo.get("secondo_oggetto"),
                "oggetto_da_raccogliere": testo.get("oggetto_da_raccogliere"),
                "indizi_prima": prima,
                "indizi_dopo": dopo,
                "indizi_lettura": lettura,
                "cifra_ottenuta": cifra,
                "spiegazione": grezzo["soluzione"]["spiegazione"],
            })
        if not enigmi:
            raise ValueError("La lista degli enigmi è vuota.")
        ordine = dati.get("indizio_ordine", {})
        return {
            "titolo": dati.get("titolo", "Laboratorio Aurora"),
            "ambientazione": "Un laboratorio abbandonato. Osserva gli oggetti, raccogli ciò che serve e trova il codice d'uscita.",
            "indizio_ordine": {
                "oggetto": ordine.get("oggetto", "Poster"),
                "testo_visibile": ordine.get("testo_giocatore", ""),
            },
            "enigmi": enigmi,
            "codice_porta": "".join(str(enigma["cifra_ottenuta"]) for enigma in enigmi),
        }
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError,
            TypeError, ValueError) as errore:
        raise ValueError(f"Impossibile leggere enigmi.json:\n{errore}") from errore


class Gioco:
    def __init__(self, radice, dati):
        self.radice = radice
        self.dati = dati
        self.giocatore = PARTENZA
        self.risolti = set()
        self.inventario = set()
        self.oggetti = {}
        self.posizioni = {}
        self.finestra_attiva = None
        self.vinto = False
        self.muri = self.crea_muri()
        self.crea_oggetti()

        radice.title(dati.get("titolo", "Escape room"))
        radice.resizable(False, False)
        telaio = ttk.Frame(radice, padding=12)
        telaio.grid()
        ttk.Label(telaio, text=dati.get("titolo", "Laboratorio"),
                  font=("Arial", 17, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(telaio, text=dati.get("ambientazione", ""),
                  wraplength=600).grid(row=1, column=0, sticky="w", pady=(3, 9))

        self.canvas = tk.Canvas(telaio, width=LATO * CELLA, height=LATO * CELLA,
                                highlightthickness=0, background="#101820")
        self.canvas.grid(row=2, column=0)
        ttk.Label(telaio, text="Frecce: muovi  •  E: interagisci  •  La porta è blu",
                  anchor="w").grid(row=3, column=0, sticky="ew", pady=(8, 2))
        self.stato = tk.StringVar(value="Esplora il laboratorio. Avvicinati a un oggetto e premi E.")
        ttk.Label(telaio, textvariable=self.stato, wraplength=600,
                  foreground="#173b5e").grid(row=4, column=0, sticky="ew", pady=3)
        self.riepilogo = tk.StringVar()
        ttk.Label(telaio, textvariable=self.riepilogo, wraplength=600).grid(
            row=5, column=0, sticky="ew")
        ttk.Button(telaio, text="Esamina inventario", command=self.mostra_inventario).grid(
            row=6, column=0, sticky="w", pady=(6, 0))

        radice.bind("<Up>", lambda evento: self.muovi(-1, 0))
        radice.bind("<Down>", lambda evento: self.muovi(1, 0))
        radice.bind("<Left>", lambda evento: self.muovi(0, -1))
        radice.bind("<Right>", lambda evento: self.muovi(0, 1))
        radice.bind("<KeyPress-e>", lambda evento: self.interagisci())
        radice.bind("<KeyPress-E>", lambda evento: self.interagisci())
        self.disegna()

    @staticmethod
    def crea_muri():
        muri = {(r, c) for r in range(LATO) for c in range(LATO)
                if r in (0, LATO - 1) or c in (0, LATO - 1)}
        muri.remove(PORTA)
        muri.update((6, c) for c in range(2, 7))
        muri.update((6, c) for c in range(9, 14))
        muri.update((10, c) for c in range(2, 6))
        muri.update((10, c) for c in range(8, 12))
        muri.update((r, 7) for r in range(2, 6))
        muri.update((r, 5) for r in range(7, 10))
        return muri

    def aggiungi(self, chiave, nome, posizione, descrizione, tipo, enigma=None):
        self.oggetti[chiave] = {"nome": nome, "descrizione": descrizione,
                               "tipo": tipo, "enigma": enigma}
        self.posizioni[chiave] = posizione

    def crea_oggetti(self):
        postazioni = [(3, 3), (5, 12), (11, 12)]
        complementi = [(3, 11), (12, 10), (8, 12)]
        raccolte = [(11, 3), (12, 4), (12, 11)]
        enigmi = self.dati["enigmi"]
        if len(enigmi) > len(postazioni):
            raise ValueError("La mappa supporta al massimo tre enigmi.")
        for i, enigma in enumerate(enigmi):
            principale = f"principale_{i}"
            self.aggiungi(principale, enigma["oggetto_principale"], postazioni[i],
                          "\n\n".join(enigma["indizi_prima"]) or enigma["nome"],
                          "enigma", enigma)
            if enigma.get("secondo_oggetto"):
                descrizione = "\n\n".join(enigma["indizi_lettura"])
                self.aggiungi(f"secondario_{i}", enigma["secondo_oggetto"],
                              complementi[i], descrizione, "indizio", enigma)
            raccoglibile = enigma.get("oggetto_da_raccogliere")
            if raccoglibile:
                descrizione = raccoglibile.get("uso_per_sbloccare", "")
                self.aggiungi(f"raccoglibile_{i}", raccoglibile["nome"],
                              raccolte[i], descrizione, "raccoglibile", enigma)

        ordine = self.dati.get("indizio_ordine")
        if ordine:
            self.aggiungi("poster", ordine["oggetto"], (1, 9),
                          ordine["testo_visibile"], "indizio")

    def disegna(self):
        self.canvas.delete("all")
        colori = {"enigma": "#62c4aa", "indizio": "#e3c36e",
                  "raccoglibile": "#d98bda"}
        for r in range(LATO):
            for c in range(LATO):
                x, y = c * CELLA, r * CELLA
                colore = "#344654" if (r, c) in self.muri else "#e7edf0"
                if (r, c) == PORTA:
                    colore = "#2d71be"
                self.canvas.create_rectangle(x, y, x + CELLA, y + CELLA,
                                              fill=colore, outline="#aab8bf")
        self.canvas.create_text((PORTA[1] + .5) * CELLA,
                                (PORTA[0] + .5) * CELLA,
                                text="USC", fill="white", font=("Arial", 10, "bold"))
        for chiave, posizione in self.posizioni.items():
            oggetto = self.oggetti[chiave]
            if oggetto["tipo"] == "raccoglibile" and chiave in self.inventario:
                continue
            r, c = posizione
            x, y = c * CELLA + CELLA / 2, r * CELLA + CELLA / 2
            self.canvas.create_oval(x - 13, y - 13, x + 13, y + 13,
                                    fill=colori[oggetto["tipo"]], outline="#26333c")
            iniziali = "".join(parola[0] for parola in oggetto["nome"].split()[:2]).upper()
            self.canvas.create_text(x, y, text=iniziali, font=("Arial", 9, "bold"))
        r, c = self.giocatore
        x, y = c * CELLA + CELLA / 2, r * CELLA + CELLA / 2
        self.canvas.create_oval(x - 14, y - 14, x + 14, y + 14,
                                fill="#f47650", outline="#622a1d", width=2)
        self.canvas.create_text(x, y, text="TU", fill="white",
                                font=("Arial", 9, "bold"))
        trovate = [str(e["cifra_ottenuta"]) if e["id"] in self.risolti else "?"
                   for e in self.dati["enigmi"]]
        nomi = [self.oggetti[chiave]["nome"] for chiave in self.inventario]
        self.riepilogo.set("Cifre trovate: " + " · ".join(trovate) +
                           "     Inventario: " + (", ".join(nomi) if nomi else "vuoto"))

    def muovi(self, dr, dc):
        if self.finestra_attiva or self.vinto:
            return
        r, c = self.giocatore
        destinazione = (r + dr, c + dc)
        occupate = {posizione for chiave, posizione in self.posizioni.items()
                    if chiave not in self.inventario}
        if destinazione == PORTA:
            self.stato.set("La porta è bloccata. Premi E dalla casella adiacente.")
        elif destinazione in self.muri or destinazione in occupate:
            self.stato.set("Passaggio occupato. Premi E accanto a un oggetto.")
        elif 0 <= destinazione[0] < LATO and 0 <= destinazione[1] < LATO:
            self.giocatore = destinazione
            self.disegna()

    def nuova_finestra(self, titolo):
        finestra = tk.Toplevel(self.radice)
        finestra.title(titolo)
        finestra.resizable(False, False)
        finestra.transient(self.radice)
        finestra.grab_set()
        self.finestra_attiva = finestra

        def chiudi():
            self.finestra_attiva = None
            finestra.destroy()
            self.radice.focus_set()

        finestra.protocol("WM_DELETE_WINDOW", chiudi)
        finestra.chiudi = chiudi
        return finestra

    @staticmethod
    def vicino(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def interagisci(self):
        if self.finestra_attiva or self.vinto:
            return
        vicini = []
        if self.vicino(self.giocatore, PORTA):
            vicini.append(("porta", None))
        for chiave, posizione in self.posizioni.items():
            if chiave not in self.inventario and self.vicino(self.giocatore, posizione):
                vicini.append(("oggetto", chiave))
        if not vicini:
            self.stato.set("Non c'è nulla con cui interagire nelle caselle adiacenti.")
        elif len(vicini) == 1:
            self.apri_interazione(*vicini[0])
        else:
            finestra = self.nuova_finestra("Scegli con cosa interagire")
            corpo = ttk.Frame(finestra, padding=15)
            corpo.grid()
            ttk.Label(corpo, text="Oggetti adiacenti:").grid(sticky="w")
            for i, (tipo, chiave) in enumerate(vicini, 1):
                nome = "Porta d'uscita" if tipo == "porta" else self.oggetti[chiave]["nome"]
                def scegli(t=tipo, k=chiave):
                    finestra.chiudi()
                    self.apri_interazione(t, k)
                ttk.Button(corpo, text=nome, command=scegli).grid(row=i, column=0,
                                                                    sticky="ew", pady=2)

    def apri_interazione(self, tipo, chiave):
        if tipo == "porta":
            self.apri_porta()
            return
        oggetto = self.oggetti[chiave]
        finestra = self.nuova_finestra(oggetto["nome"])
        corpo = ttk.Frame(finestra, padding=16)
        corpo.grid()
        ttk.Label(corpo, text=oggetto["nome"], font=("Arial", 14, "bold")).grid(sticky="w")
        ttk.Label(corpo, text=oggetto["descrizione"], wraplength=430,
                  justify="left").grid(sticky="w", pady=(8, 12))
        self.stato.set("Esamini: " + oggetto["nome"] + ". " + oggetto["descrizione"])
        if oggetto["tipo"] == "raccoglibile":
            def raccogli():
                self.inventario.add(chiave)
                self.stato.set("Hai raccolto: " + oggetto["nome"] + ".")
                finestra.chiudi()
                self.disegna()
            ttk.Button(corpo, text="Raccogli", command=raccogli).grid(sticky="w")
        elif oggetto["tipo"] == "enigma":
            def apri_enigma():
                enigma = oggetto["enigma"]
                necessario = enigma.get("oggetto_da_raccogliere")
                if necessario:
                    chiave_necessaria = next((k for k, o in self.oggetti.items()
                                             if o["tipo"] == "raccoglibile" and
                                             o["enigma"] is enigma), None)
                    if chiave_necessaria not in self.inventario:
                        self.stato.set("Ti serve: " + necessario["nome"] + ".")
                        messagebox.showinfo("Oggetto necessario",
                                            "Ti serve: " + necessario["nome"], parent=finestra)
                        return
                finestra.chiudi()
                self.apri_enigma(enigma)
            ttk.Button(corpo, text="Risolvi enigma", command=apri_enigma).grid(sticky="w")
        ttk.Button(corpo, text="Chiudi", command=finestra.chiudi).grid(sticky="e", pady=(8, 0))

    def apri_enigma(self, enigma):
        finestra = self.nuova_finestra(enigma["nome"])
        corpo = ttk.Frame(finestra, padding=18)
        corpo.grid()
        ttk.Label(corpo, text=enigma["nome"], font=("Arial", 14, "bold")).grid(sticky="w")
        indizi = list(enigma["indizi_dopo"])
        if not enigma.get("secondo_oggetto"):
            indizi += enigma["indizi_lettura"]
        for i, indizio in enumerate(indizi, 1):
            ttk.Label(corpo, text=f"{i}. {indizio}", wraplength=460,
                      justify="left").grid(sticky="w", pady=(8, 0))
        ttk.Label(corpo, text="Quale cifra ottieni?").grid(sticky="w", pady=(14, 3))
        risposta = ttk.Entry(corpo, width=12)
        risposta.grid(sticky="w")

        def verifica(evento=None):
            if risposta.get().strip() == str(enigma["cifra_ottenuta"]):
                self.risolti.add(enigma["id"])
                messaggio = (f"Enigma risolto! Cifra: {enigma['cifra_ottenuta']}.\n\n" +
                             enigma.get("spiegazione", ""))
                self.stato.set(messaggio.replace("\n", " "))
                finestra.chiudi()
                self.disegna()
                messagebox.showinfo("Cifra ottenuta", messaggio, parent=self.radice)
            else:
                self.stato.set("Risposta non corretta. Rileggi gli indizi.")
                messagebox.showinfo("Riprova", "Risposta non corretta.", parent=finestra)

        risposta.bind("<Return>", verifica)
        ttk.Button(corpo, text="Verifica", command=verifica).grid(sticky="w", pady=(10, 0))
        risposta.focus_set()

    def apri_porta(self):
        finestra = self.nuova_finestra("Porta d'uscita")
        corpo = ttk.Frame(finestra, padding=18)
        corpo.grid()
        ttk.Label(corpo, text="La porta richiede un codice.",
                  font=("Arial", 12, "bold")).grid(sticky="w")
        ttk.Label(corpo, text="Inserisci le cifre nell'ordine indicato dagli indizi.",
                  wraplength=360).grid(sticky="w", pady=(6, 10))
        codice = ttk.Entry(corpo, width=15)
        codice.grid(sticky="w")

        def verifica(evento=None):
            if codice.get().strip() == str(self.dati["codice_porta"]):
                self.vinto = True
                self.stato.set("La porta si apre. Hai vinto!")
                finestra.chiudi()
                messagebox.showinfo("Vittoria", "La porta si apre. Sei uscito dal laboratorio!",
                                    parent=self.radice)
            else:
                self.stato.set("Codice errato. La porta resta chiusa.")
                messagebox.showinfo("Codice errato", "La porta resta chiusa.", parent=finestra)

        codice.bind("<Return>", verifica)
        ttk.Button(corpo, text="Apri porta", command=verifica).grid(sticky="w", pady=(10, 0))
        codice.focus_set()

    def mostra_inventario(self):
        if self.finestra_attiva:
            return
        if not self.inventario:
            self.stato.set("L'inventario è vuoto.")
            return
        finestra = self.nuova_finestra("Inventario")
        corpo = ttk.Frame(finestra, padding=16)
        corpo.grid()
        for i, chiave in enumerate(sorted(self.inventario)):
            oggetto = self.oggetti[chiave]
            ttk.Label(corpo, text=oggetto["nome"],
                      font=("Arial", 11, "bold")).grid(row=2 * i, sticky="w", pady=(6, 0))
            ttk.Label(corpo, text=oggetto["descrizione"], wraplength=430,
                      justify="left").grid(row=2 * i + 1, sticky="w")
        ttk.Button(corpo, text="Chiudi", command=finestra.chiudi).grid(sticky="e", pady=(10, 0))


def main():
    radice = tk.Tk()
    radice.withdraw()
    try:
        dati = carica_dati()
        Gioco(radice, dati)
    except (ValueError, KeyError, TypeError, IndexError) as errore:
        messagebox.showerror("Errore", str(errore), parent=radice)
        radice.destroy()
        return
    radice.deiconify()
    radice.mainloop()


if __name__ == "__main__":
    main()
