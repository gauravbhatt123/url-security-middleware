import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import time
import requests
import re
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Try to import CustomTkinter, fall back to regular tkinter if not available
try:
    import customtkinter as ctk
    CUSTOM_TKINTER_AVAILABLE = True
except ImportError:
    import tkinter as ctk
    CUSTOM_TKINTER_AVAILABLE = False
    print("CustomTkinter not available, using regular tkinter")

class ModernProxyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Proxy Server Control Panel")
        
        # Configure CustomTkinter if available
        if CUSTOM_TKINTER_AVAILABLE:
            ctk.set_appearance_mode("light")
            ctk.set_default_color_theme("blue")
            self.root.geometry("1200x800")
        else:
            self.root.geometry("1200x800")
            self.root.configure(bg='#ffffff')
        
        self.process = None
        self.latency_data = []
        self.request_count = 0
        
        # Create main container
        self.create_main_layout()
        self.create_styles()
        self.setup_variables()
        self.create_widgets()
        self.setup_layout()
        
        # Start monitoring thread
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_output, daemon=True)
        self.monitor_thread.start()

    def create_main_layout(self):
        """Create the main layout structure"""
        if CUSTOM_TKINTER_AVAILABLE:
            # Create main frame with padding
            self.main_frame = ctk.CTkFrame(self.root)
            self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create top control panel
            self.control_frame = ctk.CTkFrame(self.main_frame)
            self.control_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # Create bottom content area
            self.content_frame = ctk.CTkFrame(self.main_frame)
            self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
            # Create left and right panels
            self.left_panel = ctk.CTkFrame(self.content_frame)
            self.left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
            
            self.right_panel = ctk.CTkFrame(self.content_frame)
            self.right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))
        else:
            # Fallback to regular tkinter
            self.main_frame = tk.Frame(self.root, bg='#ffffff')
            self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            self.control_frame = tk.Frame(self.main_frame, bg='#f8f9fa', relief="raised", bd=2)
            self.control_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            self.content_frame = tk.Frame(self.main_frame, bg='#ffffff')
            self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
            self.left_panel = tk.Frame(self.content_frame, bg='#f8f9fa', relief="sunken", bd=2)
            self.left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
            
            self.right_panel = tk.Frame(self.content_frame, bg='#f8f9fa', relief="sunken", bd=2)
            self.right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))

    def create_styles(self):
        """Create custom styles for widgets"""
        if not CUSTOM_TKINTER_AVAILABLE:
            style = ttk.Style()
            style.theme_use('clam')
            
            # Configure styles for light theme
            style.configure('Light.TFrame', background='#f8f9fa')
            style.configure('Light.TLabel', background='#f8f9fa', foreground='black')
            style.configure('Light.TButton', background='#007bff', foreground='white')
            style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#007bff')

    def setup_variables(self):
        """Setup variables for the GUI"""
        self.port_var = tk.StringVar(value="3040")
        self.cache_var = tk.StringVar(value="20")
        self.url_var = tk.StringVar(value="https://httpbin.org/get")
        self.status_var = tk.StringVar(value="Ready to start the proxy server...")

    def create_widgets(self):
        """Create all widgets"""
        self.create_control_panel()
        self.create_logs_section()
        self.create_cache_section()
        self.create_request_section()
        self.create_latency_graph()

    def create_control_panel(self):
        """Create the top control panel"""
        if CUSTOM_TKINTER_AVAILABLE:
            # Title
            title_label = ctk.CTkLabel(
                self.control_frame, 
                text="Advanced Proxy Server Control Panel",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title_label.pack(pady=(10, 20))
            
            # Control buttons frame
            controls_frame = ctk.CTkFrame(self.control_frame)
            controls_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            # Port and Cache inputs
            input_frame = ctk.CTkFrame(controls_frame)
            input_frame.pack(side="left", padx=10, pady=10)
            
            ctk.CTkLabel(input_frame, text="Port:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 5))
            port_entry = ctk.CTkEntry(input_frame, textvariable=self.port_var, width=80)
            port_entry.pack(side="left", padx=(0, 20))
            
            ctk.CTkLabel(input_frame, text="Cache Size:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 5))
            cache_entry = ctk.CTkEntry(input_frame, textvariable=self.cache_var, width=80)
            cache_entry.pack(side="left", padx=(0, 20))
            
            # Buttons
            button_frame = ctk.CTkFrame(controls_frame)
            button_frame.pack(side="right", padx=10, pady=10)
            
            self.start_button = ctk.CTkButton(
                button_frame,
                text="Start Proxy",
                command=self.start_proxy,
                fg_color="#28a745",
                hover_color="#218838",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            self.start_button.pack(side="left", padx=5)
            
            self.stop_button = ctk.CTkButton(
                button_frame,
                text="Stop Proxy",
                command=self.stop_proxy,
                fg_color="#dc3545",
                hover_color="#c82333",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            self.stop_button.pack(side="left", padx=5)
            
            # Status indicator
            self.status_label = ctk.CTkLabel(
                self.control_frame,
                textvariable=self.status_var,
                font=ctk.CTkFont(size=12)
            )
            self.status_label.pack(pady=(0, 10))
            
        else:
            # Fallback to regular tkinter
            title_label = tk.Label(
                self.control_frame,
                text="Advanced Proxy Server Control Panel",
                font=('Arial', 16, 'bold'),
                fg='black',
                bg='#f8f9fa'
            )
            title_label.pack(pady=(10, 20))
            
            controls_frame = tk.Frame(self.control_frame, bg='#f8f9fa')
            controls_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            input_frame = tk.Frame(controls_frame, bg='#f8f9fa')
            input_frame.pack(side="left", padx=10, pady=10)
            
            tk.Label(input_frame, text="Port:", fg='black', bg='#f8f9fa').pack(side="left", padx=(10, 5))
            port_entry = tk.Entry(input_frame, textvariable=self.port_var, width=8, bg='white', fg='black')
            port_entry.pack(side="left", padx=(0, 20))
            
            tk.Label(input_frame, text="Cache Size:", fg='black', bg='#f8f9fa').pack(side="left", padx=(0, 5))
            cache_entry = tk.Entry(input_frame, textvariable=self.cache_var, width=8, bg='white', fg='black')
            cache_entry.pack(side="left", padx=(0, 20))
            
            button_frame = tk.Frame(controls_frame, bg='#f8f9fa')
            button_frame.pack(side="right", padx=10, pady=10)
            
            self.start_button = tk.Button(
                button_frame,
                text="Start Proxy",
                command=self.start_proxy,
                bg='#28a745',
                fg='white',
                font=('Arial', 10, 'bold'),
                relief="flat",
                padx=15,
                pady=5
            )
            self.start_button.pack(side="left", padx=5)
            
            self.stop_button = tk.Button(
                button_frame,
                text="Stop Proxy",
                command=self.stop_proxy,
                bg='#dc3545',
                fg='white',
                font=('Arial', 10, 'bold'),
                relief="flat",
                padx=15,
                pady=5
            )
            self.stop_button.pack(side="left", padx=5)
            
            self.status_label = tk.Label(
                self.control_frame,
                textvariable=self.status_var,
                fg='black',
                bg='#f8f9fa',
                font=('Arial', 10)
            )
            self.status_label.pack(pady=(0, 10))

    def create_logs_section(self):
        """Create the logs section"""
        if CUSTOM_TKINTER_AVAILABLE:
            # Logs frame
            logs_frame = ctk.CTkFrame(self.left_panel)
            logs_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Logs header
            logs_header = ctk.CTkFrame(logs_frame)
            logs_header.pack(fill="x", padx=10, pady=(10, 5))
            
            ctk.CTkLabel(
                logs_header,
                text="Proxy Logs",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(side="left")
            
            self.open_log_button = ctk.CTkButton(
                logs_header,
                text="Open Log File",
                command=self.open_log_file,
                width=120,
                font=ctk.CTkFont(size=10)
            )
            self.open_log_button.pack(side="right")
            
            # Logs text area
            self.logs_text = ctk.CTkTextbox(logs_frame, height=200)
            self.logs_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
        else:
            logs_frame = tk.Frame(self.left_panel, bg='#f8f9fa')
            logs_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            logs_header = tk.Frame(logs_frame, bg='#f8f9fa')
            logs_header.pack(fill="x", padx=10, pady=(10, 5))
            
            tk.Label(
                logs_header,
                text="Proxy Logs",
                fg='black',
                bg='#f8f9fa',
                font=('Arial', 12, 'bold')
            ).pack(side="left")
            
            self.open_log_button = tk.Button(
                logs_header,
                text="Open Log File",
                command=self.open_log_file,
                bg='#007bff',
                fg='white',
                relief="flat",
                padx=10,
                pady=2
            )
            self.open_log_button.pack(side="right")
            
            self.logs_text = scrolledtext.ScrolledText(
                logs_frame,
                height=12,
                bg='white',
                fg='black',
                font=('Consolas', 9)
            )
            self.logs_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def create_cache_section(self):
        """Create the cache state section"""
        if CUSTOM_TKINTER_AVAILABLE:
            cache_frame = ctk.CTkFrame(self.right_panel)
            cache_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Cache header
            ctk.CTkLabel(
                cache_frame,
                text="Cache State",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=(10, 10))
            
            # Cache table
            self.cache_tree = ttk.Treeview(
                cache_frame,
                columns=("URL", "Path", "Size", "Freq", "Score"),
                show="headings",
                height=8
            )
            
            # Configure columns
            self.cache_tree.heading("URL", text="URL")
            self.cache_tree.heading("Path", text="Path")
            self.cache_tree.heading("Size", text="Size")
            self.cache_tree.heading("Freq", text="Freq")
            self.cache_tree.heading("Score", text="Score")
            
            self.cache_tree.column("URL", width=150)
            self.cache_tree.column("Path", width=100)
            self.cache_tree.column("Size", width=80)
            self.cache_tree.column("Freq", width=60)
            self.cache_tree.column("Score", width=80)
            
            self.cache_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
        else:
            cache_frame = tk.Frame(self.right_panel, bg='#f8f9fa')
            cache_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            tk.Label(
                cache_frame,
                text="Cache State",
                fg='black',
                bg='#f8f9fa',
                font=('Arial', 12, 'bold')
            ).pack(pady=(10, 10))
            
            self.cache_tree = ttk.Treeview(
                cache_frame,
                columns=("URL", "Path", "Size", "Freq", "Score"),
                show="headings",
                height=8
            )
            
            self.cache_tree.heading("URL", text="URL")
            self.cache_tree.heading("Path", text="Path")
            self.cache_tree.heading("Size", text="Size")
            self.cache_tree.heading("Freq", text="Freq")
            self.cache_tree.heading("Score", text="Score")
            
            self.cache_tree.column("URL", width=150)
            self.cache_tree.column("Path", width=100)
            self.cache_tree.column("Size", width=80)
            self.cache_tree.column("Freq", width=60)
            self.cache_tree.column("Score", width=80)
            
            self.cache_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def create_request_section(self):
        """Create the request section"""
        if CUSTOM_TKINTER_AVAILABLE:
            request_frame = ctk.CTkFrame(self.left_panel)
            request_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))
            
            # Request header
            ctk.CTkLabel(
                request_frame,
                text="Send Request",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=(10, 10))
            
            # URL input
            url_frame = ctk.CTkFrame(request_frame)
            url_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            ctk.CTkLabel(url_frame, text="URL:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 5))
            self.url_entry = ctk.CTkEntry(url_frame, textvariable=self.url_var, width=300)
            self.url_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)
            
            # Quick test buttons
            quick_frame = ctk.CTkFrame(request_frame)
            quick_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            quick_urls = [
                ("HTTP Test", "http://httpbin.org/get"),
                ("HTTPS Test", "https://httpbin.org/get"),
                ("Google", "https://google.com"),
                ("GitHub API", "https://api.github.com/users/octocat"),
                ("JSON Test", "https://jsonplaceholder.typicode.com/posts/1")
            ]
            
            for i, (text, url) in enumerate(quick_urls):
                btn = ctk.CTkButton(
                    quick_frame,
                    text=text,
                    command=lambda u=url: self.set_url(u),
                    width=120,
                    font=ctk.CTkFont(size=10)
                )
                btn.grid(row=i//3, column=i%3, padx=5, pady=2)
            
            # Send button
            send_frame = ctk.CTkFrame(request_frame)
            send_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            self.send_button = ctk.CTkButton(
                send_frame,
                text="Send Request",
                command=self.send_request,
                fg_color="#007bff",
                hover_color="#0056b3",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            self.send_button.pack(side="left", padx=(0, 10))
            
            # Info label
            self.info_label = ctk.CTkLabel(
                send_frame,
                text="For HTTPS requests, SSL verification is disabled for MITM proxy",
                font=ctk.CTkFont(size=10),
                text_color="#6c757d"
            )
            self.info_label.pack(side="left")
            
            # Response area
            response_frame = ctk.CTkFrame(request_frame)
            response_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
            ctk.CTkLabel(
                response_frame,
                text="Response",
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(pady=(10, 5))
            
            self.response_area = ctk.CTkTextbox(response_frame, height=150)
            self.response_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
        else:
            request_frame = tk.Frame(self.left_panel, bg='#f8f9fa')
            request_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))
            
            tk.Label(
                request_frame,
                text="Send Request",
                fg='black',
                bg='#f8f9fa',
                font=('Arial', 12, 'bold')
            ).pack(pady=(10, 10))
            
            url_frame = tk.Frame(request_frame, bg='#f8f9fa')
            url_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            tk.Label(url_frame, text="URL:", fg='black', bg='#f8f9fa').pack(side="left", padx=(10, 5))
            self.url_entry = tk.Entry(url_frame, textvariable=self.url_var, width=40, bg='white', fg='black')
            self.url_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)
            
            quick_frame = tk.Frame(request_frame, bg='#f8f9fa')
            quick_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            quick_urls = [
                ("HTTP Test", "http://httpbin.org/get"),
                ("HTTPS Test", "https://httpbin.org/get"),
                ("Google", "https://google.com"),
                ("GitHub API", "https://api.github.com/users/octocat"),
                ("JSON Test", "https://jsonplaceholder.typicode.com/posts/1")
            ]
            
            for i, (text, url) in enumerate(quick_urls):
                btn = tk.Button(
                    quick_frame,
                    text=text,
                    command=lambda u=url: self.set_url(u),
                    bg='#007bff',
                    fg='white',
                    relief="flat",
                    padx=8,
                    pady=2
                )
                btn.grid(row=i//3, column=i%3, padx=5, pady=2)
            
            send_frame = tk.Frame(request_frame, bg='#f8f9fa')
            send_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            self.send_button = tk.Button(
                send_frame,
                text="Send Request",
                command=self.send_request,
                bg='#007bff',
                fg='white',
                relief="flat",
                padx=15,
                pady=5
            )
            self.send_button.pack(side="left", padx=(0, 10))
            
            self.info_label = tk.Label(
                send_frame,
                text="For HTTPS requests, SSL verification is disabled for MITM proxy",
                fg='#6c757d',
                bg='#f8f9fa',
                font=('Arial', 9)
            )
            self.info_label.pack(side="left")
            
            response_frame = tk.Frame(request_frame, bg='#f8f9fa')
            response_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
            tk.Label(
                response_frame,
                text="Response",
                fg='black',
                bg='#f8f9fa',
                font=('Arial', 10, 'bold')
            ).pack(pady=(10, 5))
            
            self.response_area = scrolledtext.ScrolledText(
                response_frame,
                height=8,
                bg='white',
                fg='black',
                font=('Consolas', 9)
            )
            self.response_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def create_latency_graph(self):
        """Create the latency graph"""
        if CUSTOM_TKINTER_AVAILABLE:
            graph_frame = ctk.CTkFrame(self.right_panel)
            graph_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))
            
            ctk.CTkLabel(
                graph_frame,
                text="Request Latency (ms)",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=(10, 10))
            
        else:
            graph_frame = tk.Frame(self.right_panel, bg='#f8f9fa')
            graph_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))
            
            tk.Label(
                graph_frame,
                text="Request Latency (ms)",
                fg='black',
                bg='#f8f9fa',
                font=('Arial', 12, 'bold')
            ).pack(pady=(10, 10))
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.ax.set_facecolor('white')
        self.fig.patch.set_facecolor('white')
        
        # Style the plot
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel('Request #', color='black')
        self.ax.set_ylabel('Latency (ms)', color='black')
        self.ax.tick_params(colors='black')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def setup_layout(self):
        """Setup the final layout"""
        # Initial log message
        self.log_message("Advanced Proxy Server Control Panel initialized")
        self.log_message("Ready to start the proxy server...")

    def log_message(self, message):
        """Add a message to the logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        if CUSTOM_TKINTER_AVAILABLE:
            self.logs_text.insert("end", log_entry)
            self.logs_text.see("end")
        else:
            self.logs_text.insert("end", log_entry)
            self.logs_text.see("end")

    def start_proxy(self):
        """Start the proxy server"""
        if self.process:
            self.log_message("Proxy is already running!")
            return
        
        try:
            proxy_path = os.path.abspath("../proxy/proxy_server")
            cmd = [proxy_path]
            cwd = os.path.dirname(proxy_path)
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=cwd
            )
            
            self.status_var.set("Proxy server started successfully!")
            self.log_message("Proxy server started successfully!")
            self.log_message(f"Listening on port {self.port_var.get()}")
            self.log_message(f"Cache size: {self.cache_var.get()} entries")
            
        except Exception as e:
            self.log_message(f"Failed to start proxy: {str(e)}")
            self.status_var.set("Failed to start proxy server")

    def stop_proxy(self):
        """Stop the proxy server"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None
                self.status_var.set("Proxy server stopped")
                self.log_message("Proxy server stopped")
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process = None
                self.status_var.set("Proxy server force killed")
                self.log_message("Proxy server force killed")
        else:
            self.log_message("No proxy process to stop")

    def open_log_file(self):
        """Open the log file"""
        log_file = "../proxy/logs/proxy.log"
        if os.path.exists(log_file):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(log_file)
                else:  # Linux/Mac
                    subprocess.run(['xdg-open', log_file])
            except Exception as e:
                self.log_message(f"Failed to open log file: {str(e)}")
        else:
            self.log_message("Log file not found")

    def set_url(self, url):
        """Set the URL in the entry field"""
        self.url_var.set(url)

    def send_request(self):
        """Send a request through the proxy"""
        url = self.url_var.get()
        if not url:
            self.log_message("Please enter a URL")
            return
        
        try:
            self.log_message(f"Sending request to: {url}")
            
            # Configure proxies
            proxies = {
                'http': f'http://localhost:{self.port_var.get()}',
                'https': f'http://localhost:{self.port_var.get()}'
            }
            
            start_time = time.time()
            
            # Send request
            response = requests.get(
                url,
                proxies=proxies,
                verify=False,  # Disable SSL verification for MITM
                timeout=30
            )
            
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Update latency data
            self.request_count += 1
            self.latency_data.append(latency)
            self.update_latency_graph()
            
            # Format response
            response_text = f"Request Successful!\n"
            response_text += f"Status: {response.status_code}\n"
            response_text += f"Latency: {latency:.2f}ms\n"
            response_text += f"Size: {len(response.content)} bytes\n"
            response_text += f"Headers:\n"
            
            for header, value in response.headers.items():
                response_text += f"  {header}: {value}\n"
            
            response_text += f"\nBody (first 1000 chars):\n"
            response_text += response.text[:1000]
            
            if len(response.text) > 1000:
                response_text += "\n... (truncated)"
            
            # Update response area
            if CUSTOM_TKINTER_AVAILABLE:
                self.response_area.delete("1.0", "end")
                self.response_area.insert("1.0", response_text)
            else:
                self.response_area.delete("1.0", "end")
                self.response_area.insert("1.0", response_text)
            
            self.log_message(f"Request completed in {latency:.2f}ms")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            self.log_message(error_msg)
            
            if CUSTOM_TKINTER_AVAILABLE:
                self.response_area.delete("1.0", "end")
                self.response_area.insert("1.0", error_msg)
            else:
                self.response_area.delete("1.0", "end")
                self.response_area.insert("1.0", error_msg)

    def update_latency_graph(self):
        """Update the latency graph"""
        if len(self.latency_data) > 0:
            self.ax.clear()
            
            # Plot data
            x = list(range(1, len(self.latency_data) + 1))
            self.ax.plot(x, self.latency_data, 'b-o', linewidth=2, markersize=6)
            
            # Style the plot
            self.ax.grid(True, alpha=0.3)
            self.ax.set_xlabel('Request #', color='black')
            self.ax.set_ylabel('Latency (ms)', color='black')
            self.ax.tick_params(colors='black')
            
            # Set y-axis limits
            if max(self.latency_data) > 0:
                self.ax.set_ylim(0, max(self.latency_data) * 1.1)
            
            self.canvas.draw()

    def monitor_output(self):
        """Monitor the proxy output"""
        while self.monitoring:
            if self.process:
                try:
                    output = self.process.stdout.readline()
                    if output:
                        # Parse cache state from output - match the actual format from logs
                        # Format: "Entry 1: httpbin.org/get size=478 freq=1 score=0.003"
                        cache_match = re.search(r'Entry (\d+): ([^ ]+) size=([^ ]+) freq=(\d+) score=([^ ]+)', output)
                        if cache_match:
                            entry_num = cache_match.group(1)
                            full_url = cache_match.group(2)  # This contains both URL and path
                            size = cache_match.group(3)
                            freq = cache_match.group(4)
                            score = cache_match.group(5)
                            
                            # Split URL and path - URL is the domain, path is everything after
                            if '/' in full_url:
                                url = full_url.split('/', 1)[0]  # Get domain part
                                path = '/' + full_url.split('/', 1)[1]  # Get path part
                            else:
                                url = full_url
                                path = "/"
                            
                            # Update cache tree
                            self.root.after(0, self.update_cache_tree, entry_num, url, path, size, freq, score)
                            # Debug log
                            self.root.after(0, self.log_message, f"Parsed cache entry: {url} {path} size={size} freq={freq} score={score}")
                        
                        # Log the output
                        self.root.after(0, self.log_message, output.strip())
                        
                except Exception as e:
                    pass
            
            time.sleep(0.1)

    def update_cache_tree(self, entry_num, url, path, size, freq, score):
        """Update the cache tree with new data"""
        # Clear existing items
        for item in self.cache_tree.get_children():
            self.cache_tree.delete(item)
        
        # Add new item
        self.cache_tree.insert("", "end", values=(url, path, size, freq, score))

    def on_closing(self):
        """Handle window closing"""
        self.monitoring = False
        if self.process:
            self.stop_proxy()
        self.root.destroy()

def main():
    root = ctk.CTk() if CUSTOM_TKINTER_AVAILABLE else tk.Tk()
    app = ModernProxyGUI(root)
    
    # Set up closing handler
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()
