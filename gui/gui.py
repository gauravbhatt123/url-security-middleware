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
        self.port_var = tk.StringVar(value='3040')  # Fixed port to match proxy
        ttk.Entry(cfg, textvariable=self.port_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Label(cfg, text="Cache Size:").grid(row=0, column=2)
        self.cache_var = tk.StringVar(value='20')  # Fixed cache size to match proxy
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
        cols = ('URL', 'Path', 'Size', 'Freq', 'Score')
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
        
        # URL input row
        ttk.Label(req, text="URL:").grid(row=0, column=0, sticky='w')
        self.url_entry = ttk.Entry(req, width=50)
        self.url_entry.grid(row=0, column=1, padx=5, sticky='ew')
        self.url_entry.insert(0, "https://httpbin.org/get")  # Default URL
        
        # Quick URL buttons
        url_frame = ttk.Frame(req)
        url_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky='ew')
        
        quick_urls = [
            ("HTTP Test", "http://httpbin.org/get"),
            ("HTTPS Test", "https://httpbin.org/get"),
            ("Google", "https://google.com"),
            ("GitHub API", "https://api.github.com/users/octocat"),
            ("JSON Test", "https://httpbin.org/json")
        ]
        
        for i, (label, url) in enumerate(quick_urls):
            btn = ttk.Button(url_frame, text=label, 
                           command=lambda u=url: self.set_url(u))
            btn.pack(side='left', padx=2)
        
        self.send_button = ttk.Button(req, text="Send Request", command=self.send_request, state='disabled')
        self.send_button.grid(row=2, column=0, columnspan=3, pady=5)
        if requests is None:
            self.send_button.config(state='disabled')
        
        # Add HTTPS info
        info_label = ttk.Label(req, text="💡 For HTTPS requests, SSL verification is disabled for MITM proxy", 
                              foreground='blue', font=('TkDefaultFont', 8))
        info_label.grid(row=4, column=0, columnspan=3, pady=2)
        
        self.response_area = scrolledtext.ScrolledText(req, width=60, height=10)
        self.response_area.grid(row=5, column=0, columnspan=3, pady=5)

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
        
        # Fixed executable path
        proxy_path = os.path.abspath("../proxy/proxy_server")
        if not os.path.exists(proxy_path):
            messagebox.showerror("Error", f"Proxy executable not found at: {proxy_path}\nPlease compile the proxy first.")
            return
            
        cmd = [proxy_path]
        self.log_area.insert(tk.END, f"Starting proxy: {' '.join(cmd)}\n")
        self.log_area.see(tk.END)
        self.cache_table.delete(*self.cache_table.get_children())
        self.send_button.config(state='disabled')
        
        try:
            self.proxy_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=os.path.dirname(proxy_path)  # Run from proxy directory
            )
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            threading.Thread(target=self._read_output, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start proxy: {e}")
            self.log_area.insert(tk.END, f"Error: {e}\n")

    def _read_output(self):
        in_cache = False
        entry = {}
        cache_entries = []
        
        for line in self.proxy_process.stdout:
            self.log_area.insert(tk.END, line)
            self.log_area.see(tk.END)
            logger.info(line.strip())

            # detect when cache dump starts
            if '=== Cache State ===' in line:
                in_cache = True
                self.cache_table.delete(*self.cache_table.get_children())
                cache_entries = []
                continue

            # detect end of cache dump
            if in_cache and '===================' in line:
                in_cache = False
                # Update cache table with all entries
                for entry in cache_entries:
                    if entry:  # Only insert if we have a complete entry
                        vals = [entry.get(c, '') for c in ['URL','Path','Size','Freq','Score']]
                        self.cache_table.insert('', 'end', values=vals)
                continue

            # collect cache entries
            if in_cache:
                # Match cache entry format: "Entry X: host/path  size=Y  freq=Z  score=W"
                match = re.match(r'Entry \d+:\s*([^\s]+)([^\s]+)\s+size=([\d\.]+)\s+freq=(\d+)\s+score=([\d\.]+)', line)
                if match:
                    entry = {
                        'URL': match.group(1),
                        'Path': match.group(2),
                        'Size': match.group(3),
                        'Freq': match.group(4),
                        'Score': match.group(5)
                    }
                    cache_entries.append(entry)
                continue

            # proxy ready detection
            if 'Proxy listening on port' in line and not getattr(self, 'proxy_ready', False):
                self.proxy_ready = True
                self.send_button.config(state='normal')

        # process ended
        self.stop_proxy()

    def stop_proxy(self):
        if self.proxy_process:
            try:
                os.killpg(os.getpgid(self.proxy_process.pid), signal.SIGTERM)
            except:
                self.proxy_process.terminate()
            self.log_area.insert(tk.END, "Proxy stopped.\n")
            self.proxy_process = None
        self.send_button.config(state='disabled')
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def set_url(self, url):
        """Set URL in the entry field"""
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)

    def open_log_file(self):
        try:
            os.system(f"xdg-open '{os.path.abspath(log_file)}'")
        except:
            messagebox.showinfo("Log File", f"Log file location: {os.path.abspath(log_file)}")

    def send_request(self):
        if not requests:
            messagebox.showerror("Error", "Requests module missing.")
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a URL.")
            return

        # Show status in response area
        self.response_area.delete(1.0, tk.END)
        self.response_area.insert(tk.END, f"Sending request to: {url}\nPlease wait...\n")
        self.root.update()

        try:
            # Configure proxies for both HTTP and HTTPS
            proxies = {
                "http": f"http://localhost:{self.port_var.get()}",
                "https": f"http://localhost:{self.port_var.get()}"
            }
            
            # For HTTPS requests, we need to handle certificate verification
            if url.startswith("https://"):
                # Disable SSL verification for MITM proxy
                resp = requests.get(
                    url,
                    proxies=proxies,
                    timeout=10,
                    verify=False  # Disable SSL verification for MITM
                )
            else:
                resp = requests.get(
                    url,
                    proxies=proxies,
                    timeout=10
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

            # Format response for display
            headers_text = "\n".join([f"  {k}: {v}" for k, v in resp.headers.items()])
            
            # Truncate body if too long
            body_text = resp.text
            if len(body_text) > 2000:
                body_text = body_text[:2000] + "\n\n... (truncated)"
            
            text = (
                f"✅ Request Successful!\n\n"
                f"Status: {resp.status_code}\n"
                f"Latency: {latency_ms:.2f}ms\n"
                f"Size: {len(resp.text)} bytes\n\n"
                f"Headers:\n{headers_text}\n\n"
                f"Body:\n{body_text}"
            )
            self.response_area.delete(1.0, tk.END)
            self.response_area.insert(tk.END, text)

        except ReadTimeout:
            messagebox.showerror(
                "Request Timeout",
                f"Request to {url} timed out after 10 seconds."
            )
            self.response_area.delete(1.0, tk.END)
            self.response_area.insert(tk.END, f"❌ Timeout: Request to {url} timed out")

        except ConnectionError as ce:
            if isinstance(ce.args[-1], BadStatusLine) or 'BadStatusLine' in repr(ce):
                messagebox.showinfo("Cache Hit", f"URL already in cache:\n{url}")
            else:
                messagebox.showerror("Connection Error", str(ce))
                self.response_area.delete(1.0, tk.END)
                self.response_area.insert(tk.END, f"❌ Connection Error: {ce}")

        except Exception as e:
            messagebox.showerror("Request Error", str(e))
            self.response_area.delete(1.0, tk.END)
            self.response_area.insert(tk.END, f"❌ Error: {e}")

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
