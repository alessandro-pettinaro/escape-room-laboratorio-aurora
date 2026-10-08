"""Escape room Tkinter. Collocare enigmi.json accanto a questo file."""

import json
import re
import math
import random
import time
import tkinter as tk
import tkinter.font as tkfont
from collections import deque
from pathlib import Path
from tkinter import messagebox, ttk


LATO = 16
CELLA = 38
LARGHEZZA_FINESTRA = 820
ALTEZZA_PANNELLO = 126
ALTEZZA_CIFRE = 72
TEMPO_LIMITE = 10 * 60
ATTESA_ENIGMA = 30
COLORE_VITA = "#E5383B"
COLORE_VITA_PERSA = "#5A6A70"


def carica_dati():
    percorso = Path(__file__).resolve().with_name("enigmi.json")
    try:
        with percorso.open("r", encoding="utf-8") as file:
            dati = json.load(file)
        if not isinstance(dati["enigmi"], list) or not dati["enigmi"]:
            raise ValueError("La lista degli enigmi è vuota o non valida.")
        if len(dati["enigmi"]) > 3:
            raise ValueError("La mappa supporta al massimo tre enigmi.")
        ordine = dati["indizio_ordine"]
        ordine["oggetto"]
        ordine["testo_giocatore"]
        identificativi = set()
        for enigma in dati["enigmi"]:
            for campo in ("id", "nome", "testo_giocatore", "soluzione"):
                enigma[campo]
            if enigma["id"] in identificativi:
                raise ValueError(f"ID duplicato: {enigma['id']}")
            identificativi.add(enigma["id"])
            testo = enigma["testo_giocatore"]
            testo["oggetto_principale"]
            if not isinstance(testo["indizi"], list) or not testo["indizi"]:
                raise ValueError(f"Indizi mancanti per {enigma['id']}.")
            for indizio in testo["indizi"]:
                indizio["quando"]
                indizio["testo"]
            raccoglibile = testo.get("oggetto_da_raccogliere")
            if raccoglibile:
                raccoglibile["nome"]
                raccoglibile["uso_per_sbloccare"]
            cifra = enigma["soluzione"]["cifra_ottenuta"]
            if not isinstance(cifra, int) or isinstance(cifra, bool) or not 0 <= cifra <= 9:
                raise ValueError(f"Cifra non valida per {enigma['id']}.")
        enigmi = []
        posizioni_ordine = {}
        for grezzo in dati["enigmi"]:
            testo = grezzo["testo_giocatore"]
            prima = [i["testo"] for i in testo["indizi"]
                     if i["quando"].lower().startswith("prima")]
            dopo = [i["testo"] for i in testo["indizi"]
                    if i["quando"].lower().startswith("dopo")]
            lettura = [i["testo"] for i in testo["indizi"]
                       if not i["quando"].lower().startswith(("prima", "dopo"))]
            riferimento = re.search(rf"\b{re.escape(grezzo['id'])}\b",
                                    ordine["testo_giocatore"], flags=re.IGNORECASE)
            if riferimento is None:
                raise ValueError(f"Il poster non indica l'ordine dell'enigma {grezzo['id']}.")
            posizioni_ordine[grezzo["id"]] = riferimento.start()
            enigmi.append({
                "id": grezzo["id"],
                "nome": grezzo["nome"],
                "oggetto_principale": testo["oggetto_principale"],
                "secondo_oggetto": testo.get("secondo_oggetto"),
                "oggetto_da_raccogliere": testo.get("oggetto_da_raccogliere"),
                "indizi_prima": prima,
                "indizi_dopo": dopo,
                "indizi_lettura": lettura,
                "cifra_ottenuta": grezzo["soluzione"]["cifra_ottenuta"],
                "spiegazione": grezzo["soluzione"]["spiegazione"],
            })
        enigmi_in_ordine = sorted(enigmi, key=lambda enigma: posizioni_ordine[enigma["id"]])
        return {
            "titolo": dati.get("titolo", "Laboratorio Aurora"),
            "ambientazione": "Un laboratorio abbandonato. Osserva gli oggetti, raccogli ciò che serve e trova il codice d'uscita.",
            "indizio_ordine": {
                "oggetto": ordine["oggetto"],
                "testo_visibile": ordine["testo_giocatore"],
            },
            "enigmi": enigmi,
            "codice_porta": "".join(str(enigma["cifra_ottenuta"])
                                    for enigma in enigmi_in_ordine),
        }
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError,
            TypeError, ValueError) as errore:
        raise ValueError(f"Impossibile leggere enigmi.json:\n{errore}") from errore


class Gioco:
    def __init__(self, radice, dati):
        self.radice = radice
        self.dati = dati
        famiglie = set(tkfont.families(radice))
        self.famiglia_emoji = next(
            (nome for nome in ("Apple Color Emoji", "Segoe UI Emoji",
                               "Noto Color Emoji", "EmojiOne Color")
             if nome in famiglie), "TkDefaultFont"
        )
        self.giocatore = None
        self.porta = None
        self.risolti = set()
        self.ordine_cifre = []
        self.inventario = set()
        self.oggetti = {}
        self.posizioni = {}
        self.finestra_attiva = None
        self.vinto = False
        self.sconfitto = False
        self.vite = 3
        self.errori = 0
        self.notifica_corrente = None
        self.timer_notifica = None
        self.notifica_attesa_chiave = None
        self.timer_aggiorna_attesa = None
        self.timer_callback = None
        self.attese_enigmi = {}
        self.timer_attese = {}
        self.crea_oggetti()
        self.genera_stanza()

        radice.title(dati.get("titolo", "Escape room"))
        radice.configure(bg="#101820")
        radice.resizable(False, False)
        telaio = tk.Frame(radice, bg="#101820", padx=12, pady=12)
        telaio.grid()
        telaio.columnconfigure(
            0, minsize=min(LARGHEZZA_FINESTRA, radice.winfo_screenwidth() - 48)
        )
        tk.Label(telaio, text=dati.get("titolo", "Laboratorio"),
                 font=("Arial", 17, "bold"), fg="white", bg="#101820").grid(
                     row=0, column=0, sticky="w"
                 )
        riga_descrizione = tk.Frame(telaio, bg="#101820", bd=0, highlightthickness=0)
        riga_descrizione.grid(row=1, column=0, sticky="ew", pady=(3, 9))
        riga_descrizione.columnconfigure(0, weight=1)
        tk.Label(
            riga_descrizione, text=dati.get("ambientazione", ""),
            wraplength=550, justify="left", fg="white", bg="#101820",
            padx=0, pady=0, bd=0, highlightthickness=0
        ).grid(row=0, column=0, sticky="w")
        area_timer = tk.Frame(riga_descrizione, bg="#101820", bd=0)
        area_timer.grid(row=0, column=1, sticky="e")
        self.etichetta_timer = tk.Label(
            area_timer, text="Tempo rimanente: 10:00",
            font=("Arial", 12, "bold"), fg="white", bg="#101820",
            padx=0, pady=0, anchor="e", bd=0, highlightthickness=0
        )
        self.etichetta_timer.pack(side="top")
        riga_vite = tk.Frame(area_timer, bg="#101820", bd=0)
        riga_vite.pack(side="top", anchor="center")
        self.cuori = []
        for _ in range(3):
            cuore = tk.Label(riga_vite, text="❤️", font=("Arial", 17),
                             fg=COLORE_VITA, bg="#101820", bd=0)
            cuore.pack(side="left")
            self.cuori.append(cuore)

        self.canvas = tk.Canvas(telaio, width=LATO * CELLA, height=LATO * CELLA,
                                highlightthickness=0, background="#101820")
        self.canvas.grid(row=2, column=0)
        larghezza_mappa = LATO * CELLA
        larghezza_riquadro = (larghezza_mappa - 8) // 2
        pannello = tk.Frame(telaio, bg="#101820")
        pannello.grid(row=3, column=0, pady=(8, 0))
        self.riquadro_inventario = ttk.LabelFrame(
            pannello, text="INVENTARIO", width=larghezza_riquadro,
            height=ALTEZZA_PANNELLO
        )
        self.riquadro_inventario.grid(row=0, column=0, padx=(0, 8))
        self.riquadro_inventario.grid_propagate(False)
        self.riquadro_inventario.columnconfigure(0, weight=1)
        self.contenuto_inventario = ttk.Frame(self.riquadro_inventario)
        self.contenuto_inventario.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        self.contenuto_inventario.columnconfigure(0, weight=1)
        colonna_destra = tk.Frame(pannello, bg="#101820")
        colonna_destra.grid(row=0, column=1, sticky="n")
        self.riquadro_cifre = ttk.LabelFrame(
            colonna_destra, text="CIFRE TROVATE", width=larghezza_riquadro,
            height=ALTEZZA_CIFRE
        )
        self.riquadro_cifre.pack(side="top")
        self.riquadro_cifre.grid_propagate(False)
        self.cifre_trovate = tk.StringVar()
        ttk.Label(self.riquadro_cifre, textvariable=self.cifre_trovate,
                  font=("Arial", 22, "bold")).grid(row=0, column=0,
                                                     padx=18, pady=4)
        riga_pulsanti = tk.Frame(colonna_destra, bg="#101820")
        riga_pulsanti.pack(side="top", pady=(8, 0))
        larghezza_pulsante = (larghezza_riquadro - 8) // 2

        def crea_pulsante(testo, colore, colore_hover, comando):
            pulsante = tk.Canvas(
                riga_pulsanti, width=larghezza_pulsante, height=38, bg=colore,
                highlightthickness=0, bd=0, cursor="hand2", takefocus=1
            )
            pulsante.pack(side="left", padx=(0, 8) if testo == "Ricomincia" else 0)
            fondo = pulsante.create_rectangle(
                0, 0, larghezza_pulsante, 38, fill=colore, outline=colore
            )
            pulsante.create_text(
                larghezza_pulsante / 2, 19, text=testo,
                fill="white", font=("Arial", 10, "bold")
            )
            for sequenza in ("<Button-1>", "<Return>", "<space>"):
                pulsante.bind(sequenza, comando)
            pulsante.bind(
                "<Enter>", lambda evento: pulsante.itemconfigure(
                    fondo, fill=colore_hover, outline=colore_hover
                )
            )
            pulsante.bind(
                "<Leave>", lambda evento: pulsante.itemconfigure(
                    fondo, fill=colore, outline=colore
                )
            )

        crea_pulsante("Ricomincia", "#2F6FD0", "#245AAF", self.conferma_ricomincia)
        crea_pulsante("Termina partita", "#E5383B", "#C42F33", self.conferma_termina)
        radice.bind("<Up>", lambda evento: self.muovi(-1, 0))
        radice.bind("<Down>", lambda evento: self.muovi(1, 0))
        radice.bind("<Left>", lambda evento: self.muovi(0, -1))
        radice.bind("<Right>", lambda evento: self.muovi(0, 1))
        radice.bind("<KeyPress-e>", lambda evento: self.interagisci())
        radice.bind("<KeyPress-E>", lambda evento: self.interagisci())
        self.disegna()
        self.mostra_notifica("Esplora il laboratorio. Avvicinati a un oggetto e premi E.")
        self.inizio_timer = time.monotonic()
        self.scadenza_timer = self.inizio_timer + TEMPO_LIMITE
        self.aggiorna_timer()

    def aggiorna_timer(self):
        self.timer_callback = None
        if self.vinto or self.sconfitto:
            return
        adesso = time.monotonic()
        residuo = max(0, math.ceil(self.scadenza_timer - adesso))
        minuti, secondi = divmod(residuo, 60)
        self.etichetta_timer.config(text=f"Tempo rimanente: {minuti:02d}:{secondi:02d}")
        if residuo == 0:
            self.sconfiggi("tempo")
            return
        if residuo < 60:
            colore = "red" if int(adesso * 2) % 2 == 0 else "white"
        else:
            colore = "white"
        self.etichetta_timer.config(fg=colore)
        self.timer_callback = self.radice.after(250, self.aggiorna_timer)

    def tempo_esaurito(self):
        if not self.vinto and not self.sconfitto and time.monotonic() >= self.scadenza_timer:
            self.sconfiggi("tempo")
        return self.sconfitto

    def perdi_vita(self):
        if self.sconfitto or self.vinto:
            return
        self.errori += 1
        self.vite -= 1
        for indice, cuore in enumerate(self.cuori):
            cuore.config(
                text="❤️" if indice < self.vite else "🩶",
                fg=COLORE_VITA if indice < self.vite else COLORE_VITA_PERSA
            )
        if self.vite == 0:
            self.sconfiggi("vite")

    def sconfiggi(self, motivo):
        if self.sconfitto:
            return
        self.sconfitto = True
        if self.timer_callback is not None:
            self.radice.after_cancel(self.timer_callback)
            self.timer_callback = None
        if motivo == "tempo":
            self.etichetta_timer.config(text="Tempo rimanente: 00:00", fg="red")
        if self.finestra_attiva:
            self.finestra_attiva.chiudi()
        for elemento in self.contenuto_inventario.winfo_children():
            for controllo in elemento.winfo_children():
                if isinstance(controllo, ttk.Button):
                    controllo.state(["disabled"])
        self.mostra_fine(motivo)

    def mostra_fine(self, esito):
        messaggi = {
            "vittoria": "Ce l'hai fatta! Hai aperto la porta e sei fuggito dal laboratorio.",
            "tempo": "Il tempo è scaduto. La porta resterà sigillata per sempre.",
            "vite": "Hai esaurito le vite. Il sistema di sicurezza ha bloccato definitivamente la porta."
        }
        if self.timer_notifica is not None:
            self.radice.after_cancel(self.timer_notifica)
            self.timer_notifica = None
        if self.timer_aggiorna_attesa is not None:
            self.radice.after_cancel(self.timer_aggiorna_attesa)
            self.timer_aggiorna_attesa = None
        self.notifica_attesa_chiave = None
        self.notifica_corrente = None
        self.canvas.delete("notifica")

        finestra = tk.Toplevel(self.radice)
        finestra.title("Partita terminata")
        finestra.resizable(False, False)
        finestra.transient(self.radice)
        finestra.grab_set()
        finestra.protocol("WM_DELETE_WINDOW", self.radice.destroy)
        self.finestra_attiva = finestra
        corpo = ttk.Frame(finestra, padding=20)
        corpo.grid()
        ttk.Label(corpo, text=messaggi[esito], wraplength=430,
                  justify="center", font=("Arial", 13, "bold")).grid(
                      row=0, column=0, columnspan=2, pady=(0, 14)
                  )
        durata = min(TEMPO_LIMITE, int(time.monotonic() - self.inizio_timer))
        minuti, secondi = divmod(durata, 60)
        ttk.Label(corpo, text=f"Tempo impiegato: {minuti:02d}:{secondi:02d}").grid(
            row=1, column=0, columnspan=2, pady=2
        )
        ttk.Label(corpo, text=f"Errori commessi: {self.errori}").grid(
            row=2, column=0, columnspan=2, pady=(2, 14)
        )
        ttk.Button(corpo, text="Gioca ancora", command=self.nuova_partita).grid(
            row=3, column=0, padx=5
        )
        ttk.Button(corpo, text="Esci", command=self.radice.destroy).grid(
            row=3, column=1, padx=5
        )

        def centra():
            x = self.radice.winfo_rootx() + (self.radice.winfo_width() -
                                            finestra.winfo_width()) // 2
            y = self.radice.winfo_rooty() + (self.radice.winfo_height() -
                                            finestra.winfo_height()) // 2
            finestra.geometry(f"+{x}+{y}")

        finestra.after_idle(centra)

    def nuova_partita(self):
        if self.timer_callback is not None:
            self.radice.after_cancel(self.timer_callback)
        if self.timer_notifica is not None:
            self.radice.after_cancel(self.timer_notifica)
        if self.timer_aggiorna_attesa is not None:
            self.radice.after_cancel(self.timer_aggiorna_attesa)
        for callback in self.timer_attese.values():
            self.radice.after_cancel(callback)
        for elemento in self.radice.winfo_children():
            elemento.destroy()
        Gioco(self.radice, self.dati)

    def secondi_attesa(self, chiave):
        scadenza = self.attese_enigmi.get(chiave, 0)
        return max(0, math.ceil(scadenza - time.monotonic()))

    def inizia_attesa(self, chiave):
        self.attese_enigmi[chiave] = time.monotonic() + ATTESA_ENIGMA
        if chiave in self.timer_attese:
            self.radice.after_cancel(self.timer_attese[chiave])
        self.timer_attese[chiave] = self.radice.after(
            ATTESA_ENIGMA * 1000, lambda: self.fine_attesa(chiave)
        )

    def fine_attesa(self, chiave):
        residuo = self.attese_enigmi.get(chiave, 0) - time.monotonic()
        if residuo > 0:
            self.timer_attese[chiave] = self.radice.after(
                math.ceil(residuo * 1000), lambda: self.fine_attesa(chiave)
            )
            return
        self.attese_enigmi.pop(chiave, None)
        self.timer_attese.pop(chiave, None)
        self.disegna()

    @staticmethod
    def adiacenti(posizione):
        r, c = posizione
        return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))

    def genera_stanza(self):
        interne = [(r, c) for r in range(1, LATO - 1)
                   for c in range(1, LATO - 1)]
        perimetro = {(r, c) for r in range(LATO) for c in range(LATO)
                     if r in (0, LATO - 1) or c in (0, LATO - 1)}
        porte = ([(0, c) for c in range(1, LATO - 1)] +
                 [(LATO - 1, c) for c in range(1, LATO - 1)] +
                 [(r, 0) for r in range(1, LATO - 1)] +
                 [(r, LATO - 1) for r in range(1, LATO - 1)])

        for _ in range(1000):
            porta = random.choice(porte)
            muri = (perimetro - {porta}) | set(
                random.sample(interne, random.randint(18, 34))
            )
            libere = [posizione for posizione in interne if posizione not in muri]
            caselle = random.sample(libere, len(self.oggetti) + 1)
            posizioni = dict(zip(self.oggetti, caselle))
            giocatore = caselle[-1]
            percorribili = set(libere) - set(posizioni.values())
            raggiunte = {giocatore}
            coda = deque([giocatore])
            while coda:
                for vicina in self.adiacenti(coda.popleft()):
                    if vicina in percorribili and vicina not in raggiunte:
                        raggiunte.add(vicina)
                        coda.append(vicina)
            if all(any(vicina in raggiunte for vicina in self.adiacenti(posizione))
                   for posizione in (*posizioni.values(), porta)):
                self.porta = porta
                self.muri = muri
                self.posizioni = posizioni
                self.giocatore = giocatore
                return
        raise ValueError("Impossibile generare una stanza percorribile.")

    def aggiungi(self, chiave, nome, descrizione, tipo, enigma=None):
        self.oggetti[chiave] = {"nome": nome, "descrizione": descrizione,
                               "tipo": tipo, "enigma": enigma}

    def crea_oggetti(self):
        enigmi = self.dati["enigmi"]
        if len(enigmi) > 3:
            raise ValueError("La mappa supporta al massimo tre enigmi.")
        for i, enigma in enumerate(enigmi):
            principale = f"principale_{i}"
            self.aggiungi(principale, enigma["oggetto_principale"],
                          "\n\n".join(enigma["indizi_prima"]) or enigma["nome"],
                          "enigma", enigma)
            if enigma.get("secondo_oggetto"):
                descrizione = "\n\n".join(enigma["indizi_lettura"])
                self.aggiungi(f"secondario_{i}", enigma["secondo_oggetto"],
                              descrizione, "indizio", enigma)
            raccoglibile = enigma.get("oggetto_da_raccogliere")
            if raccoglibile:
                descrizione = raccoglibile.get("uso_per_sbloccare", "")
                self.aggiungi(f"raccoglibile_{i}", raccoglibile["nome"],
                              descrizione, "raccoglibile", enigma)

        ordine = self.dati.get("indizio_ordine")
        if ordine:
            self.aggiungi("poster", ordine["oggetto"],
                          ordine["testo_visibile"], "indizio")

    @staticmethod
    def tipo_icona(nome):
        nome = nome.casefold()
        for parola, tipo in (
            ("taccuino", "taccuino"), ("quaderno", "taccuino"),
            ("batteria", "batteria"), ("fusibile", "fusibile"),
            ("reagente", "reagente"), ("provetta", "reagente"),
            ("terminale", "terminale"), ("monitor", "terminale"),
            ("microscopio", "microscopio"), ("generatore", "generatore"),
            ("bilancia", "bilancia"), ("congelatore", "congelatore"),
            ("vetrino", "vetrino"), ("poster", "poster"),
        ):
            if parola in nome:
                return tipo
        return "oggetto"

    @staticmethod
    def disegna_porta_aperta(canvas, cx, cy, dimensione):
        """Porta marrone socchiusa, con luce verde visibile nello spiraglio."""
        scala = dimensione / 32
        def punto(x, y):
            return cx + (x - 16) * scala, cy + (y - 16) * scala
        def poligono(coordinate, **opzioni):
            punti = []
            for x, y in coordinate:
                punti.extend(punto(x, y))
            canvas.create_polygon(*punti, **opzioni)

        canvas.create_rectangle(*punto(4, 2), *punto(28, 30),
                                fill="#754A30", outline="#49301F",
                                width=max(1, scala * 2))
        canvas.create_rectangle(*punto(8, 5), *punto(25, 27),
                                fill="#80E698", outline="#4A985B")
        poligono([(8, 5), (20, 8), (20, 25), (8, 28)],
                 fill="#B87548", outline="#603B27", width=max(1, scala * 1.5))
        canvas.create_line(*punto(11, 8), *punto(11, 25),
                           fill="#D69B6B", width=max(1, scala))
        canvas.create_oval(*punto(16, 17), *punto(18, 19),
                           fill="#E5C26C", outline="#76532B")

    @staticmethod
    def emoji_icona(tipo):
        return {
            "taccuino": "📓", "batteria": "🔋", "fusibile": "🔌",
            "reagente": "🧪", "terminale": "🖥️", "microscopio": "🔬",
            "generatore": "⚡", "porta": "🚪", "giocatore": "🧑‍🔬",
            "bilancia": "⚖️", "congelatore": "🧊", "vetrino": "🔎",
            "poster": "📜", "oggetto": "📦",
        }.get(tipo, "📦")

    def disegna_emoji(self, canvas, tipo, cx, cy, dimensione):
        dimensione_font = max(16, int(dimensione * .80))
        icona = canvas.create_text(
            cx, cy, text=self.emoji_icona(tipo), anchor="center",
            font=(self.famiglia_emoji, -dimensione_font)
        )
        # Alcune piattaforme mostrano le emoji composte come più glifi.
        # Riduci il carattere finché resta all'interno della casella.
        while dimensione_font > 10:
            bordi = canvas.bbox(icona)
            if bordi is None or (bordi[2] - bordi[0] <= dimensione and
                                bordi[3] - bordi[1] <= dimensione):
                break
            dimensione_font -= 1
            canvas.itemconfigure(icona, font=(self.famiglia_emoji, -dimensione_font))

    def disegna(self):
        self.canvas.delete("all")
        for r in range(LATO):
            for c in range(LATO):
                x, y = c * CELLA, r * CELLA
                colore = "#344654" if (r, c) in self.muri else "#e7edf0"
                if (r, c) == self.porta:
                    colore = "#2d71be"
                self.canvas.create_rectangle(x, y, x + CELLA, y + CELLA,
                                              fill=colore, outline="#aab8bf")
        porta_x = (self.porta[1] + .5) * CELLA
        porta_y = (self.porta[0] + .5) * CELLA
        if len(self.risolti) == len(self.dati["enigmi"]):
            self.disegna_porta_aperta(self.canvas, porta_x, porta_y,
                                      min(CELLA - 4, 30))
        else:
            self.disegna_emoji(self.canvas, "porta", porta_x, porta_y,
                               min(CELLA - 4, 30))
        for chiave, posizione in self.posizioni.items():
            oggetto = self.oggetti[chiave]
            if oggetto["tipo"] == "raccoglibile" and chiave in self.inventario:
                continue
            r, c = posizione
            x, y = c * CELLA + CELLA / 2, r * CELLA + CELLA / 2
            if oggetto["tipo"] == "enigma" and self.secondi_attesa(chiave):
                self.canvas.create_oval(x - 17, y - 17, x + 17, y + 17,
                                        outline="#9e171b", width=5)
                self.canvas.create_oval(x - 15, y - 15, x + 15, y + 15,
                                        outline="#ff454a", width=3)
            self.disegna_emoji(
                self.canvas, self.tipo_icona(oggetto["nome"]),
                x, y, min(CELLA - 4, 30)
            )
            if oggetto["tipo"] == "enigma" and oggetto["enigma"]["id"] in self.risolti:
                self.canvas.create_text(
                    x + CELLA * .29, y - CELLA * .29, text="✅", anchor="center",
                    font=(self.famiglia_emoji, -max(11, int(CELLA * .34)))
                )
        r, c = self.giocatore
        x, y = c * CELLA + CELLA / 2, r * CELLA + CELLA / 2
        self.disegna_emoji(self.canvas, "giocatore", x, y, min(CELLA - 4, 30))
        trovate = ([str(cifra) for cifra in self.ordine_cifre] +
                  ["?"] * (len(self.dati["enigmi"]) - len(self.ordine_cifre)))
        self.cifre_trovate.set("   ".join(trovate))
        self.aggiorna_inventario()
        if self.notifica_corrente:
            self.disegna_notifica()

    def aggiorna_inventario(self):
        for elemento in self.contenuto_inventario.winfo_children():
            elemento.destroy()
        if not self.inventario:
            ttk.Label(self.contenuto_inventario,
                      text="Nessun oggetto raccolto").grid(
                          row=0, column=0, sticky="w"
                      )
            return
        for riga, chiave in enumerate(sorted(self.inventario)):
            oggetto = self.oggetti[chiave]
            gruppo = ttk.Frame(self.contenuto_inventario)
            gruppo.grid(row=riga, column=0, sticky="ew", pady=2)
            gruppo.columnconfigure(1, weight=1)
            ttk.Label(
                gruppo, text=self.emoji_icona(self.tipo_icona(oggetto["nome"])),
                font=(self.famiglia_emoji, -18)
            ).grid(row=0, column=0, padx=(0, 4))
            ttk.Label(gruppo, text=oggetto["nome"]).grid(
                row=0, column=1, sticky="w"
            )
            pulsante = ttk.Button(
                gruppo, text="i", width=2,
                command=lambda k=chiave: self.mostra_notifica(
                    self.oggetti[k]["nome"] + ". " + self.oggetti[k]["descrizione"])
            )
            pulsante.grid(row=0, column=2, sticky="e", padx=(4, 0))
            if self.sconfitto:
                pulsante.state(["disabled"])

    def disegna_notifica(self):
        self.canvas.delete("notifica")
        testo, oggetto = self.notifica_corrente
        if oggetto == "porta":
            r, c = self.porta
        elif oggetto in self.posizioni and oggetto not in self.inventario:
            r, c = self.posizioni[oggetto]
        else:
            r, c = self.giocatore

        limite = LATO * CELLA
        centro_x = (c + .5) * CELLA
        testo_id = self.canvas.create_text(
            0, 0, text=testo, anchor="nw", width=limite - 24,
            fill="#ffffff", font=("Arial", 11), tags="notifica"
        )
        x0, y0, x1, y1 = self.canvas.bbox(testo_id)
        larghezza, altezza = x1 - x0, y1 - y0
        sinistra = max(12, min(centro_x - larghezza / 2, limite - larghezza - 12))
        sopra = r * CELLA - altezza - 18
        if r == 0 or sopra < 8:
            sopra = (r + 1) * CELLA + 8
        sopra = max(12, min(sopra, limite - altezza - 12))
        self.canvas.move(testo_id, sinistra - x0, sopra - y0)
        rettangolo = self.canvas.create_rectangle(
            sinistra - 7, sopra - 5, sinistra + larghezza + 7, sopra + altezza + 5,
            fill="#243746", outline="#f5d57a", width=2, tags="notifica"
        )
        self.canvas.tag_lower(rettangolo, testo_id)

    def mostra_notifica(self, testo, oggetto=None):
        if self.timer_notifica is not None:
            self.radice.after_cancel(self.timer_notifica)
        if self.timer_aggiorna_attesa is not None:
            self.radice.after_cancel(self.timer_aggiorna_attesa)
            self.timer_aggiorna_attesa = None
        self.notifica_attesa_chiave = None
        self.notifica_corrente = (testo, oggetto)
        self.disegna_notifica()
        durata = max(3000, min(15000, 1800 + len(testo) * 45))

        def nascondi():
            if self.timer_aggiorna_attesa is not None:
                self.radice.after_cancel(self.timer_aggiorna_attesa)
                self.timer_aggiorna_attesa = None
            self.notifica_attesa_chiave = None
            self.canvas.delete("notifica")
            self.notifica_corrente = None
            self.timer_notifica = None

        self.timer_notifica = self.radice.after(durata, nascondi)

    def mostra_notifica_attesa(self, chiave):
        self.mostra_notifica(
            f"Attendi ancora {self.secondi_attesa(chiave)} secondi prima di riprovare.",
            chiave
        )
        self.notifica_attesa_chiave = chiave
        self.aggiorna_notifica_attesa()

    def aggiorna_notifica_attesa(self):
        self.timer_aggiorna_attesa = None
        chiave = self.notifica_attesa_chiave
        if chiave is None or self.notifica_corrente is None:
            return
        residuo = max(0, self.attese_enigmi.get(chiave, 0) - time.monotonic())
        secondi = math.ceil(residuo)
        if secondi:
            testo = f"Attendi ancora {secondi} secondi prima di riprovare."
        else:
            testo = "Ora puoi riprovare l'enigma."
        if self.notifica_corrente != (testo, chiave):
            self.notifica_corrente = (testo, chiave)
            self.disegna_notifica()
        if secondi:
            fino_al_prossimo_secondo = residuo - (secondi - 1)
            ritardo = max(1, math.ceil(fino_al_prossimo_secondo * 1000))
            self.timer_aggiorna_attesa = self.radice.after(
                ritardo, self.aggiorna_notifica_attesa
            )
        else:
            self.notifica_attesa_chiave = None

    def muovi(self, dr, dc):
        if self.tempo_esaurito() or self.finestra_attiva or self.vinto:
            return
        r, c = self.giocatore
        destinazione = (r + dr, c + dc)
        occupate = {posizione for chiave, posizione in self.posizioni.items()
                    if chiave not in self.inventario}
        if destinazione == self.porta:
            self.mostra_notifica("La porta è bloccata. Premi E dalla casella adiacente.",
                                "porta")
        elif destinazione in self.muri or destinazione in occupate:
            self.mostra_notifica("Passaggio occupato. Premi E accanto a un oggetto.")
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

        def posiziona():
            destra = self.radice.winfo_rootx() + self.radice.winfo_width() + 12
            if destra + finestra.winfo_width() <= finestra.winfo_screenwidth():
                finestra.geometry(f"+{destra}+{self.radice.winfo_rooty()}")

        finestra.after_idle(posiziona)

        def chiudi():
            self.finestra_attiva = None
            finestra.destroy()
            self.radice.focus_set()

        finestra.protocol("WM_DELETE_WINDOW", chiudi)
        finestra.chiudi = chiudi
        return finestra

    def conferma_ricomincia(self, evento=None):
        if self.tempo_esaurito() or self.finestra_attiva or self.vinto:
            return
        finestra = self.nuova_finestra("Ricomincia")
        corpo = ttk.Frame(finestra, padding=18)
        corpo.grid()
        ttk.Label(
            corpo,
            text="Se ricominci perderai i progressi della partita in corso. Vuoi continuare?",
            wraplength=400, justify="center"
        ).grid(row=0, column=0, columnspan=2, pady=(0, 14))
        ttk.Button(corpo, text="Annulla", command=finestra.chiudi).grid(
            row=1, column=0, padx=5
        )
        ttk.Button(corpo, text="Ricomincia", command=self.nuova_partita).grid(
            row=1, column=1, padx=5
        )

    def conferma_termina(self, evento=None):
        if self.tempo_esaurito() or self.finestra_attiva or self.vinto:
            return
        finestra = self.nuova_finestra("Termina partita")
        corpo = ttk.Frame(finestra, padding=18)
        corpo.grid()
        ttk.Label(
            corpo,
            text="Se termini la partita perderai tutti i progressi. Vuoi continuare?",
            wraplength=400, justify="center"
        ).grid(row=0, column=0, columnspan=2, pady=(0, 14))
        ttk.Button(corpo, text="Annulla", command=finestra.chiudi).grid(
            row=1, column=0, padx=5
        )
        ttk.Button(corpo, text="Termina", command=self.radice.destroy).grid(
            row=1, column=1, padx=5
        )

    @staticmethod
    def vicino(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def interagisci(self):
        if self.tempo_esaurito() or self.finestra_attiva or self.vinto:
            return
        vicini = []
        if self.vicino(self.giocatore, self.porta):
            vicini.append(("porta", None))
        for chiave, posizione in self.posizioni.items():
            if chiave not in self.inventario and self.vicino(self.giocatore, posizione):
                vicini.append(("oggetto", chiave))
        if not vicini:
            self.mostra_notifica("Non c'è nulla con cui interagire nelle caselle adiacenti.")
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
        if self.tempo_esaurito():
            return
        if tipo == "porta":
            self.apri_porta()
            return
        oggetto = self.oggetti[chiave]
        if oggetto["tipo"] == "raccoglibile":
            self.inventario.add(chiave)
            self.disegna()
            self.mostra_notifica("Esamini: " + oggetto["nome"] + ". " +
                                oggetto["descrizione"])
        elif oggetto["tipo"] == "enigma":
            attesa = self.secondi_attesa(chiave)
            if attesa:
                self.mostra_notifica_attesa(chiave)
                return
            enigma = oggetto["enigma"]
            necessario = enigma.get("oggetto_da_raccogliere")
            if necessario:
                chiave_necessaria = next((k for k, o in self.oggetti.items()
                                         if o["tipo"] == "raccoglibile" and
                                         o["enigma"] is enigma), None)
                if chiave_necessaria not in self.inventario:
                    self.mostra_notifica("Ti serve: " + necessario["nome"] + ".",
                                        chiave)
                    return
            self.apri_enigma(enigma, chiave)
        else:
            self.mostra_notifica("Esamini: " + oggetto["nome"] + ". " +
                                oggetto["descrizione"], chiave)

    def apri_enigma(self, enigma, chiave):
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
            if self.tempo_esaurito():
                return
            if risposta.get().strip() == str(enigma["cifra_ottenuta"]):
                if enigma["id"] not in self.risolti:
                    self.risolti.add(enigma["id"])
                    self.ordine_cifre.append(enigma["cifra_ottenuta"])
                messaggio = (f"Enigma risolto! Cifra: {enigma['cifra_ottenuta']}.\n\n" +
                             enigma.get("spiegazione", ""))
                finestra.chiudi()
                self.disegna()
                self.mostra_notifica(messaggio, chiave)
            else:
                self.perdi_vita()
                if not self.sconfitto:
                    finestra.chiudi()
                    self.inizia_attesa(chiave)
                    self.disegna()
                    self.mostra_notifica(
                        "Risposta non corretta. Rileggi gli indizi. "
                        f"Potrai riprovare tra {ATTESA_ENIGMA} secondi.", chiave
                    )

        risposta.bind("<Return>", verifica)
        ttk.Button(corpo, text="Verifica", command=verifica).grid(sticky="w", pady=(10, 0))
        ttk.Button(corpo, text="Chiudi", command=finestra.chiudi).grid(
            sticky="e", pady=(8, 0))
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
            if self.tempo_esaurito():
                return
            if codice.get().strip() == str(self.dati["codice_porta"]):
                self.vinto = True
                if self.timer_callback is not None:
                    self.radice.after_cancel(self.timer_callback)
                    self.timer_callback = None
                finestra.chiudi()
                self.mostra_fine("vittoria")
            else:
                self.errori += 1
                self.mostra_notifica("Codice errato. La porta resta chiusa.", "porta")

        codice.bind("<Return>", verifica)
        ttk.Button(corpo, text="Apri porta", command=verifica).grid(sticky="w", pady=(10, 0))
        codice.focus_set()


def main():
    global CELLA
    radice = tk.Tk()
    radice.withdraw()
    CELLA = min(CELLA, max(28, (radice.winfo_screenheight() - 290) // LATO))
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
