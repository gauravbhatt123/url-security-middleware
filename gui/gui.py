import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import os
import signal
import threading
import logging
from logging.handlers import RotatingFileHandler
import re

from http.client import BadStatusLine

# Optional requests import
try:
    import requests
    from requests.exceptions import ReadTimeout, ConnectionError
except ImportError:
    requests = None
    ReadTimeout = ConnectionError = Exception

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Setup logging to file
if not os.path.exists('logs'):
    os.makedirs('logs')
log_file = 'logs/proxy.log'
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger('proxy_logger')
logger.setLevel(logging.INFO)
logger.addHandler(handler)


class ProxyControlPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Proxy Server Control Panel")
        self.proxy_process = None
        self.latencies = []       # list of (seq_no, latency_ms)
        self.next_seq = 1

        if requests is None:
            messagebox.showwarning(
                "Dependency Missing",
                "The 'requests' module is not installed. 'Send Request' will be disabled.\n"
                "Install via: pip install requests"
            )

        self._build_ui()

    def _build_ui(self):
        # Configuration frame
        cfg = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        cfg.pack(fill='x', padx=10, pady=5)
        ttk.Label(cfg, text="Port:").grid(row=0, column=0)
        self.port_var = tk.StringVar(value='3490')
        ttk.Entry(cfg, textvariable=self.port_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Label(cfg, text="Cache Size:").grid(row=0, column=2)
        self.cache_var = tk.StringVar(value='5')
        ttk.Entry(cfg, textvariable=self.cache_var, width=10).grid(row=0, column=3, padx=5)
        self.start_button = ttk.Button(cfg, text="Start Proxy", command=self.start_proxy)
        self.start_button.grid(row=0, column=4, padx=5)
        self.stop_button = ttk.Button(cfg, text="Stop Proxy", command=self.stop_proxy, state='disabled')
        self.stop_button.grid(row=0, column=5, padx=5)

        # Paned window for logs and cache
        pane = ttk.PanedWindow(self.root, orient='horizontal')
        pane.pack(fill='both', expand=True, padx=10, pady=5)

        # Logs
        log_frame = ttk.LabelFrame(pane, text="Logs")
        self.log_area = scrolledtext.ScrolledText(log_frame, width=60, height=20)
        self.log_area.pack(fill='both', expand=True)
        self.log_area.insert(tk.END, "Ready to start the proxy server...\n")
        ttk.Button(log_frame, text="Open Log File", command=self.open_log_file).pack(pady=5)
        pane.add(log_frame, weight=1)

        # Cache table
        cache_frame = ttk.LabelFrame(pane, text="Cache State")
        cols = ('URL', 'Path', 'Size', 'Freq', 'Latency', 'Score')
        self.cache_table = ttk.Treeview(cache_frame, columns=cols, show='headings')
        for c in cols:
            self.cache_table.heading(c, text=c)
            self.cache_table.column(c, width=100)
        self.cache_table.pack(fill='both', expand=True)
        pane.add(cache_frame, weight=1)

        # Bottom: request & plot
        bottom = ttk.Frame(self.root)
        bottom.pack(fill='both', expand=True, padx=10, pady=5)

        # Request panel
        req = ttk.LabelFrame(bottom, text="Send Request", padding=10)
        req.pack(side='left', fill='both', expand=True)
        ttk.Label(req, text="URL:").grid(row=0, column=0)
        self.url_entry = ttk.Entry(req, width=50)
        self.url_entry.grid(row=0, column=1, padx=5)
        self.send_button = ttk.Button(req, text="Send", command=self.send_request, state='disabled')
        self.send_button.grid(row=0, column=2, padx=5)
        if requests is None:
            self.send_button.config(state='disabled')
        self.response_area = scrolledtext.ScrolledText(req, width=60, height=10)
        self.response_area.grid(row=1, column=0, columnspan=3, pady=5)

        # Latency plot
        fig = plt.Figure(figsize=(4,2))
        self.ax = fig.add_subplot(111)
        self.line, = self.ax.plot([], [], marker='o', linestyle='-')
        self.ax.set_title('Request Latency (ms)')
        self.ax.set_xlabel('Request #')
        self.ax.set_ylabel('Latency (ms)')
        self.canvas = FigureCanvasTkAgg(fig, master=bottom)
        self.canvas.get_tk_widget().pack(side='right', fill='both', expand=True)

    def start_proxy(self):
        if self.proxy_process:
            return
        self.proxy_ready = False
        cmd = [os.path.abspath("../proxy/proxy")]
        self.log_area.insert(tk.END, f"Starting proxy: {' '.join(cmd)}\n")
        self.log_area.see(tk.END)
        self.cache_table.delete(*self.cache_table.get_children())
        self.send_button.config(state='disabled')
        self.proxy_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
            encoding='utf-8',
            errors='replace',
            preexec_fn=os.setsid
        )
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        threading.Thread(target=self._read_output, daemon=True).start()

    def _read_output(self):
        in_cache = False
        entry = {}
        for line in self.proxy_process.stdout:
            self.log_area.insert(tk.END, line)
            self.log_area.see(tk.END)
            logger.info(line.strip())

            # detect when cache dump starts
            if 'Cache State Starting' in line:
                in_cache = True
                self.cache_table.delete(*self.cache_table.get_children())
                entry = {}
                continue

            # detect end of each entry
            if in_cache and 'Cache State Ending' in line:
                # only insert if we have a complete entry
                if 'Score' in entry:
                    vals = [entry.get(c, '') for c in ['URL','Path','Size','Freq','Latency','Score']]
                    self.cache_table.insert('', 'end', values=vals)
                entry = {}
                continue

            # collect fields while in cache mode
            if in_cache:
                # match entry start (optional)
                if re.match(r'Entry \d+:', line):
                    entry = {}
                for key, pat in [
                    ('URL',     r'URL\s*:\s*(.*)'),
                    ('Path',    r'Path\s*:\s*(.*)'),
                    ('Size',    r'Size\s*:\s*([\d\.]+)'),
                    ('Freq',    r'Freq\s*:\s*(\d+)'),
                    ('Latency', r'Latency\s*:\s*([\d\.]+)'),
                    ('Score',   r'Score\s*:\s*([\d\.]+)')
                ]:
                    m = re.search(pat, line)
                    if m:
                        entry[key] = m.group(1)
                continue

            # proxy ready detection
            if 'Proxy listening on port' in line and not getattr(self, 'proxy_ready', False):
                self.proxy_ready = True
                self.send_button.config(state='normal')

        # process ended
        self.stop_proxy()

    def stop_proxy(self):
        if self.proxy_process:
            os.killpg(os.getpgid(self.proxy_process.pid), signal.SIGTERM)
            self.log_area.insert(tk.END, "Proxy stopped.\n")
            self.proxy_process = None
        self.send_button.config(state='disabled')
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def open_log_file(self):
        os.system(f"xdg-open '{os.path.abspath(log_file)}'")

    def send_request(self):
        if not requests:
            messagebox.showerror("Error", "Requests module missing.")
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a URL.")
            return

        try:
            resp = requests.get(
                url,
                proxies={"http": f"http://localhost:{self.port_var.get()}"},
                timeout=5
            )
            latency_ms = resp.elapsed.total_seconds() * 1000

            # record with a running sequence number
            self.latencies.append((self.next_seq, latency_ms))
            self.next_seq += 1

            # trim to last 50
            if len(self.latencies) > 50:
                self.latencies = self.latencies[-50:]

            # redraw
            self.update_plot()

            text = (
                f"Status: {resp.status_code}\n\n"
                f"Headers:\n{resp.headers}\n\n"
                f"Body:\n{resp.text}"
            )
            self.response_area.delete(1.0, tk.END)
            self.response_area.insert(tk.END, text)

        except ReadTimeout:
            messagebox.showerror(
                "Request Timeout",
                f"Request to {url} timed out after 5 seconds."
            )

        except ConnectionError as ce:
            if isinstance(ce.args[-1], BadStatusLine) or 'BadStatusLine' in repr(ce):
                messagebox.showinfo("Cache Hit", f"URL already in cache:\n{url}")
            else:
                messagebox.showerror("Connection Error", str(ce))

        except Exception as e:
            messagebox.showerror("Request Error", str(e))

    def update_plot(self):
        if not self.latencies:
            return

        seqs, vals = zip(*self.latencies)
        x = np.array(seqs)
        y = np.array(vals)

        self.line.set_data(x, y)
        self.ax.relim()
        self.ax.autoscale_view()
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(x, rotation=45, fontsize='small')
        self.canvas.draw_idle()


if __name__ == '__main__':
    root = tk.Tk()
    app = ProxyControlPanel(root)
    root.mainloop()
