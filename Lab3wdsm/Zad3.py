import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time


class BaseStationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikacja Mateusz Harasim")
        self.root.geometry("1100x800")

        # --- Dane symulacji ---
        self.is_running = False
        self.history = {'Q': [], 'W': [], 'Ro': [], 'time': []}

        self.setup_ui()

    def setup_ui(self):
        # --- Lewy Panel: Parametry ---
        p_frame = tk.LabelFrame(self.root, text="Parametry")
        p_frame.place(x=10, y=10, width=250, height=250)

        labels = ["Liczba kanałów", "Długość kolejki", "Natężenie ruchu [lambda]",
                  "Średnia długość rozmowy", "Odchylenie standardowe",
                  "Minimalny czas połączenia", "Maksymalny czas połączenia", "Czas symulacji"]
        self.inputs = {}
        defaults = [10, 10, 1.0, 20, 5, 10, 30, 30]

        for i, (label, default) in enumerate(zip(labels, defaults)):
            tk.Label(p_frame, text=label).grid(row=i, column=0, sticky="w")
            ent = tk.Entry(p_frame, width=8)
            ent.insert(0, str(default))
            ent.grid(row=i, column=1)
            self.inputs[label] = ent

        # --- Środek: Wyniki Poisson/Gauss ---
        res_frame = tk.LabelFrame(self.root, text="Wyniki")
        res_frame.place(x=270, y=10, width=150, height=250)

        tk.Label(res_frame, text="Poisson X:").pack()
        self.lbl_poisson_x = tk.Label(res_frame, text="0", bg="white", width=10, relief="sunken")
        self.lbl_poisson_x.pack()

        tk.Label(res_frame, text="Gauss X:").pack()
        self.lbl_gauss_x = tk.Label(res_frame, text="0", bg="white", width=10, relief="sunken")
        self.lbl_gauss_x.pack()

        # --- Kanały (Wizualizacja) ---
        tk.Label(self.root, text="Kanały", font=("Arial", 12, "bold")).place(x=480, y=10)
        self.chan_canvas = tk.Canvas(self.root, width=200, height=280)
        self.chan_canvas.place(x=450, y=40)
        self.rects = []
        self.texts = []
        for i in range(10):
            row, col = divmod(i, 2)
            x0, y0 = col * 80, row * 50
            r = self.chan_canvas.create_rectangle(x0, y0, x0 + 70, y0 + 40, fill="green")
            t = self.chan_canvas.create_text(x0 + 35, y0 + 20, text="", fill="white")
            self.rects.append(r)
            self.texts.append(t)

        # --- Tabele (Wyniki na dole) ---
        self.tree = ttk.Treeview(self.root, columns=("P", "G", "K", "T_P", "T_O", "L", "M", "R"), show='headings')
        cols = [("P", "liczba Poiss"), ("G", "liczba Gaus"), ("K", "L. klienta"),
                ("T_P", "Czas przyj."), ("T_O", "Czas obsł."), ("L", "lambda_i"), ("M", "mu_i"), ("R", "Rho_i")]
        for id, name in cols:
            self.tree.heading(id, text=name)
            self.tree.column(id, width=60)
        self.tree.place(x=10, y=380, width=550, height=350)

        # --- Wykresy (Prawy panel) ---
        self.fig, (self.ax_q, self.ax_w, self.ax_ro) = plt.subplots(3, 1, figsize=(4, 8))
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas_plot.get_tk_widget().place(x=680, y=10, width=400, height=750)
        self.fig.tight_layout()

        # --- Przyciski i Statystyki ---
        self.btn_start = tk.Button(self.root, text="START", command=self.start_sim, font=("Arial", 14, "bold"))
        self.btn_start.place(x=50, y=740, width=100)

        self.lbl_sim_time = tk.Label(self.root, text="Czas symulacji: 0 / 30", font=("Arial", 12))
        self.lbl_sim_time.place(x=400, y=745)

        # --- Nowy Panel Statystyk (zdefiniowany raz na starcie) ---
        stats_frame = tk.LabelFrame(self.root, text="Statystyki bieżące")
        stats_frame.place(x=270, y=270, width=170, height=100)

        self.lbl_served = tk.Label(stats_frame, text="Obsłużone: 0", anchor="w")
        self.lbl_served.pack(fill="x", padx=5)

        self.lbl_rejected = tk.Label(stats_frame, text="Odrzucone: 0", anchor="w")
        self.lbl_rejected.pack(fill="x", padx=5)

        self.lbl_queue_status = tk.Label(stats_frame, text="Kolejka: 0 / 10", anchor="w")
        self.lbl_queue_status.pack(fill="x", padx=5)

    def generate_all_traffic(self, p):
        traffic = []
        curr_time = 0
        while curr_time < p['sim_time']:
            gap = np.random.exponential(1 / p['lambda'])
            curr_time += gap
            dur = np.clip(np.random.normal(p['mean'], p['sigma']), p['min'], p['max'])
            traffic.append({'arrival': curr_time, 'duration': int(dur), 'gap': gap})
        return traffic

    def start_sim(self):
        if self.is_running: return

        # Pobieramy aktualną liczbę kanałów z pola tekstowego
        try:
            num_ch = int(self.inputs["Liczba kanałów"].get())
        except:
            num_ch = 10  # Wartość awaryjna

        # Czyścimy Canvas przed nowym rysowaniem
        self.chan_canvas.delete("all")
        self.rects = []
        self.texts = []

        # Rysujemy tyle kanałów, ile podał użytkownik
        for i in range(num_ch):
            row, col = divmod(i, 2)  # Układamy w dwóch kolumnach
            x0, y0 = col * 85, row * 45
            r = self.chan_canvas.create_rectangle(x0, y0, x0 + 75, y0 + 35, fill="green")
            t = self.chan_canvas.create_text(x0 + 37, y0 + 17, text="", fill="white")
            self.rects.append(r)
            self.texts.append(t)

        self.is_running = True
        self.history = {'Q': [], 'W': [], 'Ro': [], 'time': []}
        for item in self.tree.get_children():
            self.tree.delete(item)

        threading.Thread(target=self.sim_loop, daemon=True).start()
    def sim_loop(self):
        p = {
            'chan': int(self.inputs["Liczba kanałów"].get()),
            'q_max': int(self.inputs["Długość kolejki"].get()),
            'lambda': float(self.inputs["Natężenie ruchu [lambda]"].get()),
            'mean': float(self.inputs["Średnia długość rozmowy"].get()),
            'sigma': float(self.inputs["Odchylenie standardowe"].get()),
            'min': float(self.inputs["Minimalny czas połączenia"].get()),
            'max': float(self.inputs["Maksymalny czas połączenia"].get()),
            'sim_time': int(self.inputs["Czas symulacji"].get())
        }

        traffic = self.generate_all_traffic(p)
        channels = [0] * p['chan']
        # Kolejka przechowuje: (czas_obsługi, czas_przyjścia)
        queue = []
        served, rejected = 0, 0
        total_waiting_time = 0
        served_from_queue = 0

        for sec in range(p['sim_time'] + 1):
            arrivals = [t for t in traffic if int(t['arrival']) == sec]

            # Aktualizacja liczników Poisson/Gauss w GUI
            if arrivals:
                self.lbl_poisson_x.config(text=str(len(arrivals)))
                self.lbl_gauss_x.config(text=str(int(arrivals[0]['duration'])))

            for c in arrivals:
                free_idx = next((i for i, v in enumerate(channels) if v <= 0), None)
                if free_idx is not None:
                    channels[free_idx] = c['duration']
                    served += 1
                elif len(queue) < p['q_max']:
                    queue.append((c['duration'], c['arrival']))
                else:
                    rejected += 1

                # Wypełnianie tabeli
                self.tree.insert('', 'end', values=(
                    len(arrivals), int(c['duration']), served + rejected,
                    round(c['arrival'], 1), c['duration'],
                    round(c['gap'], 3), round(1 / p['mean'], 3),
                    round(sum(1 for x in channels if x > 0) / p['chan'], 2)
                ))

            # Logika kanałów
            for i in range(len(channels)):
                if channels[i] > 0:
                    channels[i] -= 1
                    self.chan_canvas.itemconfig(self.rects[i], fill="red")
                    self.chan_canvas.itemconfig(self.texts[i], text=str(channels[i]))

                # Jeśli kanał wolny, weź z kolejki
                if channels[i] <= 0:
                    if queue:
                        dur, arr_t = queue.pop(0)
                        channels[i] = dur
                        served += 1
                        served_from_queue += 1
                        total_waiting_time += (sec - arr_t)
                        self.chan_canvas.itemconfig(self.rects[i], fill="red")
                        self.chan_canvas.itemconfig(self.texts[i], text=str(dur))
                    else:
                        self.chan_canvas.itemconfig(self.rects[i], fill="green")
                        self.chan_canvas.itemconfig(self.texts[i], text="")

            # Statystyki do wykresów
            self.history['time'].append(sec)
            self.history['Q'].append(len(queue))

            # W (Średni czas oczekiwania)
            avg_w = total_waiting_time / served_from_queue if served_from_queue > 0 else 0
            self.history['W'].append(avg_w)

            # Ro (Natężenie)
            ro = sum(1 for c in channels if c > 0) / p['chan']
            self.history['Ro'].append(ro)

            # Aktualizacja UI
            self.update_plots()
            self.lbl_sim_time.config(text=f"Czas symulacji: {sec} / {p['sim_time']}")
            # --- Nowy Panel Statystyk (zamiast luźnego lbl_stats) ---
            # --- WKLEIĆ TO W MIEJSCE USUNIĘTEGO BLOKU ---
            self.lbl_served.config(text=f"Obsłużone: {served}")
            self.lbl_rejected.config(text=f"Odrzucone: {rejected}")
            self.lbl_queue_status.config(text=f"Kolejka: {len(queue)} / {p['q_max']}")
            time.sleep(0.5)  # Przyspieszono dla testów

        self.is_running = False

    def update_plots(self):
        # Q - Kolejka (Góra)
        self.ax_q.clear()
        self.ax_q.plot(self.history['time'], self.history['Q'], 'r')
        self.ax_q.set_title("Długość kolejki (Q)")

        # W - Oczekiwanie (Środek)
        self.ax_w.clear()
        self.ax_w.plot(self.history['time'], self.history['W'], 'b')
        self.ax_w.set_title("Średni czas oczekiwania (W)")

        # Wykres Ro - Natężenie (Dół)
        self.ax_ro.clear()
        self.ax_ro.plot(self.history['time'], self.history['Ro'], 'g')
        self.ax_ro.set_title("Natężenie ruchu (Ro)")

        # OTO ROZWIĄZANIE:
        # Ustawienie stałej skali od 0 do np. 1.2 lub 1.5
        self.ax_ro.set_ylim(0, 1.2)

        # Opcjonalnie: wymuszenie pokazywania konkretnych jednostek na osi Y
        # self.ax_ro.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2])
        self.fig.tight_layout()
        self.canvas_plot.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = BaseStationApp(root)
    root.mainloop()