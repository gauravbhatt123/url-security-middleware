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
    def __init__(self):
        # Initialize cache hit/miss counters
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_entries = 0
        self.max_cache_size = 20
        
        # Initialize security stats
        self.security_stats = {
            'total_requests': 0,
            'safe_urls': 0,
            'malicious_urls': 0,
            'blocked_urls': 0,
            'avg_score': 0.0
        }
        
        self.setup_main_window()
        self.setup_variables()
        self.create_windows()
        self.setup_monitoring()
        
    def setup_main_window(self):
        """Setup the main window"""
        if CUSTOM_TKINTER_AVAILABLE:
            self.main_window = ctk.CTk()
            self.main_window.title("🚀 Multi-threaded Proxy Web Server")
            self.main_window.geometry("600x700")
            self.main_window.configure(fg_color="#2b2b2b")
            self.main_window.resizable(True, True)
        else:
            self.main_window = tk.Tk()
            self.main_window.title("🚀 Multi-threaded Proxy Web Server")
            self.main_window.geometry("600x700")
            self.main_window.configure(bg='#2b2b2b')
            self.main_window.resizable(True, True)
        
        # Center the window
        self.main_window.update_idletasks()
        x = (self.main_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.main_window.winfo_screenheight() // 2) - (700 // 2)
        self.main_window.geometry(f"600x700+{x}+{y}")
        
        # Bind window close event
        self.main_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_variables(self):
        """Setup variables for the GUI"""
        self.port_var = tk.StringVar(value="3040")
        self.cache_var = tk.StringVar(value="20")
        self.process = None
        self.latency_data = []
        self.request_count = 0
        self.cache_entries = []
        self.monitoring = True
        self.windows = {}
        
    def create_windows(self):
        """Create all the separate windows"""
        self.create_control_panel()
        self.create_logs_window()
        self.create_cache_window()
        self.create_request_window()
        self.create_latency_window()
        
    def create_control_panel(self):
        """Create the main control panel"""
        # Title
        if CUSTOM_TKINTER_AVAILABLE:
            title_label = ctk.CTkLabel(
                self.main_window,
                text="🚀 Proxy Server Control Center",
                font=ctk.CTkFont(size=28, weight="bold")
            )
            title_label.pack(pady=(30, 20))
        else:
            title_label = tk.Label(
                self.main_window,
                text="🚀 Proxy Server Control Center",
                font=('Arial', 28, 'bold'),
                bg='#2b2b2b',
                fg='white'
            )
            title_label.pack(pady=(30, 20))
        
        # Server configuration frame
        config_frame = ctk.CTkFrame(self.main_window) if CUSTOM_TKINTER_AVAILABLE else tk.Frame(self.main_window, bg='#3a3a3a')
        config_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        # Port configuration
        port_frame = ctk.CTkFrame(config_frame) if CUSTOM_TKINTER_AVAILABLE else tk.Frame(config_frame, bg='#4a4a4a')
        port_frame.pack(fill="x", padx=20, pady=15)
        
        if CUSTOM_TKINTER_AVAILABLE:
            ctk.CTkLabel(
                port_frame,
                text="🔌 Server Configuration",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=(10, 15))
            
            # Port input
            port_input_frame = ctk.CTkFrame(port_frame)
            port_input_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            ctk.CTkLabel(
                port_input_frame,
                text="Port:",
                font=ctk.CTkFont(size=14)
            ).pack(side="left", padx=(0, 10))
            
            self.port_var = ctk.CTkEntry(
                port_input_frame,
                textvariable=self.port_var,
                width=100,
                font=ctk.CTkFont(size=14)
            )
            self.port_var.pack(side="left", padx=(0, 20))
            
            # Cache size input
            ctk.CTkLabel(
                port_input_frame,
                text="Cache Size:",
                font=ctk.CTkFont(size=14)
            ).pack(side="left", padx=(0, 10))
            
            self.cache_var = ctk.CTkEntry(
                port_input_frame,
                textvariable=self.cache_var,
                width=100,
                font=ctk.CTkFont(size=14)
            )
            self.cache_var.pack(side="left")
        else:
            tk.Label(
                port_frame,
                text="🔌 Server Configuration",
                font=('Arial', 16, 'bold'),
                bg='#4a4a4a',
                fg='white'
            ).pack(pady=(10, 15))
            
            # Port input
            port_input_frame = tk.Frame(port_frame, bg='#4a4a4a')
            port_input_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            tk.Label(
                port_input_frame,
                text="Port:",
                font=('Arial', 14),
                bg='#4a4a4a',
                fg='white'
            ).pack(side="left", padx=(0, 10))
            
            self.port_var = tk.Entry(
                port_input_frame,
                textvariable=self.port_var,
                width=10,
                font=('Arial', 14)
            )
            self.port_var.pack(side="left", padx=(0, 20))
            
            # Cache size input
            tk.Label(
                port_input_frame,
                text="Cache Size:",
                font=('Arial', 14),
                bg='#4a4a4a',
                fg='white'
            ).pack(side="left", padx=(0, 10))
            
            self.cache_var = tk.Entry(
                port_input_frame,
                textvariable=self.cache_var,
                width=10,
                font=('Arial', 14)
            )
            self.cache_var.pack(side="left")
        
        # Control buttons frame
        control_frame = ctk.CTkFrame(self.main_window) if CUSTOM_TKINTER_AVAILABLE else tk.Frame(self.main_window, bg='#3a3a3a')
        control_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        if CUSTOM_TKINTER_AVAILABLE:
            ctk.CTkLabel(
                control_frame,
                text="🎮 Control Panel",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=(15, 15))
            
            # Start/Stop buttons
            button_frame = ctk.CTkFrame(control_frame)
            button_frame.pack(fill="x", padx=20, pady=(0, 15))
            
            self.start_btn = ctk.CTkButton(
                button_frame,
                text="▶️ Start Proxy",
                command=self.start_proxy,
                fg_color="#28a745",
                hover_color="#218838",
                font=ctk.CTkFont(size=18, weight="bold"),
                height=50
            )
            self.start_btn.pack(side="left", padx=(0, 10), fill="x", expand=True)
            
            self.stop_btn = ctk.CTkButton(
                button_frame,
                text="⏹️ Stop Proxy",
                command=self.stop_proxy,
                fg_color="#dc3545",
                hover_color="#c82333",
                font=ctk.CTkFont(size=18, weight="bold"),
                height=50
            )
            self.stop_btn.pack(side="left", fill="x", expand=True)
        else:
            tk.Label(
                control_frame,
                text="🎮 Control Panel",
                font=('Arial', 16, 'bold'),
                bg='#3a3a3a',
                fg='white'
            ).pack(pady=(15, 15))
            
            # Start/Stop buttons
            button_frame = tk.Frame(control_frame, bg='#3a3a3a')
            button_frame.pack(fill="x", padx=20, pady=(0, 15))
            
            self.start_btn = tk.Button(
                button_frame,
                text="▶️ Start Proxy",
                command=self.start_proxy,
                bg='#28a745',
                fg='white',
                font=('Arial', 18, 'bold'),
                relief="flat",
                height=2
            )
            self.start_btn.pack(side="left", padx=(0, 10), fill="x", expand=True)
            
            self.stop_btn = tk.Button(
                button_frame,
                text="⏹️ Stop Proxy",
                command=self.stop_proxy,
                bg='#dc3545',
                fg='white',
                font=('Arial', 18, 'bold'),
                relief="flat",
                height=2
            )
            self.stop_btn.pack(side="left", fill="x", expand=True)
        
        # Window buttons frame
        windows_frame = ctk.CTkFrame(self.main_window) if CUSTOM_TKINTER_AVAILABLE else tk.Frame(self.main_window, bg='#3a3a3a')
        windows_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        if CUSTOM_TKINTER_AVAILABLE:
            ctk.CTkLabel(
                windows_frame,
                text="📊 Monitoring Windows",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=(15, 15))
            
            # Create a grid of buttons
            buttons_frame = ctk.CTkFrame(windows_frame)
            buttons_frame.pack(pady=(0, 15))
            
            # Configure grid columns
            buttons_frame.grid_columnconfigure(0, weight=1)
            buttons_frame.grid_columnconfigure(1, weight=1)
            
            # Row 1
            self.logs_btn = ctk.CTkButton(
                buttons_frame,
                text="📋 Logs",
                command=self.open_logs_window,
                fg_color="#007bff",
                hover_color="#0056b3",
                height=40
            )
            self.logs_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            
            self.cache_btn = ctk.CTkButton(
                buttons_frame,
                text="💾 Cache",
                command=self.open_cache_window,
                fg_color="#007bff",
                hover_color="#0056b3",
                height=40
            )
            self.cache_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            # Row 2
            self.requests_btn = ctk.CTkButton(
                buttons_frame,
                text="🌐 Requests",
                command=self.open_request_window,
                fg_color="#007bff",
                hover_color="#0056b3",
                height=40
            )
            self.requests_btn.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
            
            self.latency_btn = ctk.CTkButton(
                buttons_frame,
                text="📈 Latency",
                command=self.open_latency_window,
                fg_color="#007bff",
                hover_color="#0056b3",
                height=40
            )
            self.latency_btn.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
            
            # Row 3 - Security
            self.security_btn = ctk.CTkButton(
                buttons_frame,
                text="🛡️ Security",
                command=self.open_security_window,
                fg_color="#dc3545",
                hover_color="#c82333",
                height=40
            )
            self.security_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        else:
            tk.Label(
                windows_frame,
                text="📊 Monitoring Windows",
                font=('Arial', 16, 'bold'),
                bg='#3a3a3a',
                fg='white'
            ).pack(pady=(15, 15))
            
            # Create a grid of buttons
            buttons_frame = tk.Frame(windows_frame, bg='#3a3a3a')
            buttons_frame.pack(pady=(0, 15))
            
            # Configure grid columns
            buttons_frame.grid_columnconfigure(0, weight=1)
            buttons_frame.grid_columnconfigure(1, weight=1)
            
            # Row 1
            self.logs_btn = tk.Button(
                buttons_frame,
                text="📋 Logs",
                command=self.open_logs_window,
                bg='#007bff',
                fg='white',
                relief="flat",
                height=2
            )
            self.logs_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            
            self.cache_btn = tk.Button(
                buttons_frame,
                text="💾 Cache",
                command=self.open_cache_window,
                bg='#007bff',
                fg='white',
                relief="flat",
                height=2
            )
            self.cache_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            # Row 2
            self.requests_btn = tk.Button(
                buttons_frame,
                text="🌐 Requests",
                command=self.open_request_window,
                bg='#007bff',
                fg='white',
                relief="flat",
                height=2
            )
            self.requests_btn.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
            
            self.latency_btn = tk.Button(
                buttons_frame,
                text="📈 Latency",
                command=self.open_latency_window,
                bg='#007bff',
                fg='white',
                relief="flat",
                height=2
            )
            self.latency_btn.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
            
            # Row 3 - Security
            self.security_btn = tk.Button(
                buttons_frame,
                text="🛡️ Security",
                command=self.open_security_window,
                bg='#dc3545',
                fg='white',
                relief="flat",
                height=2
            )
            self.security_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
    
    def create_logs_window(self):
        """Create the logs window"""
        if CUSTOM_TKINTER_AVAILABLE:
            self.logs_window = ctk.CTkToplevel(self.main_window)
            self.logs_window.title("📊 Proxy Logs")
            self.logs_window.geometry("800x600")
            self.logs_window.withdraw()  # Hide initially
        else:
            self.logs_window = tk.Toplevel(self.main_window)
            self.logs_window.title("📊 Proxy Logs")
            self.logs_window.geometry("800x600")
            self.logs_window.withdraw()
            self.logs_window.configure(bg='#2b2b2b')
        
        # Title
        if CUSTOM_TKINTER_AVAILABLE:
            title = ctk.CTkLabel(self.logs_window, text="📊 Real-time Proxy Logs", font=ctk.CTkFont(size=20, weight="bold"))
            title.pack(pady=(20, 10))
            
            # Control frame
            control_frame = ctk.CTkFrame(self.logs_window)
            control_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            self.clear_logs_btn = ctk.CTkButton(
                control_frame,
                text="🗑️ Clear Logs",
                command=self.clear_logs,
                fg_color="#6c757d",
                hover_color="#5a6268"
            )
            self.clear_logs_btn.pack(side="left", padx=(0, 10))
            
            self.open_log_file_btn = ctk.CTkButton(
                control_frame,
                text="📁 Open Log File",
                command=self.open_log_file
            )
            self.open_log_file_btn.pack(side="left")
            
            # Logs text area
            self.logs_text = ctk.CTkTextbox(self.logs_window, font=ctk.CTkFont(family="Consolas", size=11))
            self.logs_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            
        else:
            title = tk.Label(self.logs_window, text="📊 Real-time Proxy Logs", font=('Arial', 16, 'bold'), fg='white', bg='#2b2b2b')
            title.pack(pady=(20, 10))
            
            control_frame = tk.Frame(self.logs_window, bg='#2b2b2b')
            control_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            self.clear_logs_btn = tk.Button(
                control_frame,
                text="🗑️ Clear Logs",
                command=self.clear_logs,
                bg='#6c757d',
                fg='white',
                relief="flat"
            )
            self.clear_logs_btn.pack(side="left", padx=(0, 10))
            
            self.open_log_file_btn = tk.Button(
                control_frame,
                text="📁 Open Log File",
                command=self.open_log_file,
                bg='#007bff',
                fg='white',
                relief="flat"
            )
            self.open_log_file_btn.pack(side="left")
            
            self.logs_text = scrolledtext.ScrolledText(
                self.logs_window,
                font=('Consolas', 10),
                bg='#1e1e1e',
                fg='#00ff00',
                insertbackground='white'
            )
            self.logs_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.windows['logs'] = self.logs_window
    
    def create_cache_window(self):
        """Create the cache window"""
        if CUSTOM_TKINTER_AVAILABLE:
            self.cache_window = ctk.CTkToplevel(self.main_window)
            self.cache_window.title("💾 Cache State")
            self.cache_window.geometry("900x500")
            self.cache_window.withdraw()
        else:
            self.cache_window = tk.Toplevel(self.main_window)
            self.cache_window.title("💾 Cache State")
            self.cache_window.geometry("900x500")
            self.cache_window.withdraw()
            self.cache_window.configure(bg='#2b2b2b')
        
        # Title
        if CUSTOM_TKINTER_AVAILABLE:
            title = ctk.CTkLabel(self.cache_window, text="💾 Cache State Monitor", font=ctk.CTkFont(size=20, weight="bold"))
            title.pack(pady=(20, 10))
            
            # Stats frame
            stats_frame = ctk.CTkFrame(self.cache_window)
            stats_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            self.cache_stats_label = ctk.CTkLabel(
                stats_frame,
                text="Cache: 0/20 entries | Hits: 0 | Misses: 0",
                font=ctk.CTkFont(size=14)
            )
            self.cache_stats_label.pack(pady=10)
            
            # Add refresh button
            refresh_frame = ctk.CTkFrame(self.cache_window)
            refresh_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            self.refresh_cache_btn = ctk.CTkButton(
                refresh_frame,
                text="🔄 Refresh Cache",
                command=self.refresh_cache_display,
                fg_color="#6c757d",
                hover_color="#5a6268"
            )
            self.refresh_cache_btn.pack(side="left", padx=(0, 10))
            
            self.clear_cache_btn = ctk.CTkButton(
                refresh_frame,
                text="🗑️ Clear Cache Display",
                command=self.clear_cache_display,
                fg_color="#dc3545",
                hover_color="#c82333"
            )
            self.clear_cache_btn.pack(side="left")
            
            # Add test entry button for debugging
            self.test_cache_btn = ctk.CTkButton(
                refresh_frame,
                text="🧪 Test Cache Entry",
                command=self.add_test_cache_entry,
                fg_color="#17a2b8",
                hover_color="#138496"
            )
            self.test_cache_btn.pack(side="left", padx=(10, 0))
            
            # Add test hit/miss buttons for debugging
            self.test_hit_btn = ctk.CTkButton(
                refresh_frame,
                text="🎯 Test Hit",
                command=self.test_cache_hit,
                fg_color="#28a745",
                hover_color="#218838"
            )
            self.test_hit_btn.pack(side="left", padx=(10, 0))
            
            self.test_miss_btn = ctk.CTkButton(
                refresh_frame,
                text="❌ Test Miss",
                command=self.test_cache_miss,
                fg_color="#ffc107",
                hover_color="#e0a800"
            )
            self.test_miss_btn.pack(side="left", padx=(10, 0))
            
            # Add test latency button for debugging
            self.test_latency_btn = ctk.CTkButton(
                refresh_frame,
                text="⏱️ Test Latency",
                command=self.test_latency_tracking,
                fg_color="#6f42c1",
                hover_color="#5a32a3"
            )
            self.test_latency_btn.pack(side="left", padx=(10, 0))
            
            # Cache table
            self.cache_tree = ttk.Treeview(
                self.cache_window,
                columns=("URL", "Path", "Size (KB)", "Freq", "GDSF Score", "Last Access"),
                show="headings",
                height=10
            )
            
            # Configure columns
            self.cache_tree.heading("URL", text="URL")
            self.cache_tree.heading("Path", text="Path")
            self.cache_tree.heading("Size (KB)", text="Size (KB)")
            self.cache_tree.heading("Freq", text="Frequency")
            self.cache_tree.heading("GDSF Score", text="GDSF Score")
            self.cache_tree.heading("Last Access", text="Last Access")
            
            # Set column widths
            self.cache_tree.column("URL", width=150)
            self.cache_tree.column("Path", width=100)
            self.cache_tree.column("Size (KB)", width=80)
            self.cache_tree.column("Freq", width=80)
            self.cache_tree.column("GDSF Score", width=100)
            self.cache_tree.column("Last Access", width=100)
            
            # Scrollbar
            cache_scrollbar = ttk.Scrollbar(self.cache_window, orient="vertical", command=self.cache_tree.yview)
            self.cache_tree.configure(yscrollcommand=cache_scrollbar.set)
            
            self.cache_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            cache_scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=(0, 20))
        
        self.windows['cache'] = self.cache_window
    
    def create_request_window(self):
        """Create the request testing window"""
        if CUSTOM_TKINTER_AVAILABLE:
            self.request_window = ctk.CTkToplevel(self.main_window)
            self.request_window.title("🌐 Request Tester")
            self.request_window.geometry("1000x700")
            self.request_window.withdraw()
        else:
            self.request_window = tk.Toplevel(self.main_window)
            self.request_window.title("🌐 Request Tester")
            self.request_window.geometry("1000x700")
            self.request_window.withdraw()
            self.request_window.configure(bg='#2b2b2b')
        
        # Title
        if CUSTOM_TKINTER_AVAILABLE:
            title = ctk.CTkLabel(self.request_window, text="🌐 Request Tester", font=ctk.CTkFont(size=20, weight="bold"))
            title.pack(pady=(20, 10))
            
            # URL input frame
            url_frame = ctk.CTkFrame(self.request_window)
            url_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            ctk.CTkLabel(url_frame, text="URL:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(10, 5))
            self.url_var = tk.StringVar(value="https://www.google.com")
            self.url_entry = ctk.CTkEntry(url_frame, textvariable=self.url_var, width=400)
            self.url_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)
            
            self.send_button = ctk.CTkButton(
                url_frame,
                text="🚀 Send Request",
                command=self.send_request,
                fg_color="#28a745",
                hover_color="#218838"
            )
            self.send_button.pack(side="right", padx=(0, 10))
            
            # Quick test buttons
            quick_frame = ctk.CTkFrame(self.request_window)
            quick_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            quick_urls = [
                ("🌐 HTTP Test", "http://httpbin.org/get"),
                ("🔒 HTTPS Test", "https://httpbin.org/get"),
                ("🔍 Google", "https://www.google.com"),
                ("📚 GitHub API", "https://api.github.com/users/octocat"),
                ("📄 JSON Test", "https://jsonplaceholder.typicode.com/posts/1")
            ]
            
            for i, (text, url) in enumerate(quick_urls):
                btn = ctk.CTkButton(
                    quick_frame,
                    text=text,
                    command=lambda u=url: self.set_url(u),
                    width=180,
                    height=35
                )
                btn.grid(row=i//3, column=i%3, padx=5, pady=5)
            
            quick_frame.grid_columnconfigure(0, weight=1)
            quick_frame.grid_columnconfigure(1, weight=1)
            quick_frame.grid_columnconfigure(2, weight=1)
            
            # Response frame
            response_frame = ctk.CTkFrame(self.request_window)
            response_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            
            ctk.CTkLabel(response_frame, text="📄 Response", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
            
            self.response_area = ctk.CTkTextbox(response_frame, font=ctk.CTkFont(family="Consolas", size=11))
            self.response_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
        else:
            title = tk.Label(self.request_window, text="🌐 Request Tester", font=('Arial', 16, 'bold'), fg='white', bg='#2b2b2b')
            title.pack(pady=(20, 10))
            
            url_frame = tk.Frame(self.request_window, bg='#2b2b2b')
            url_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            tk.Label(url_frame, text="URL:", fg='white', bg='#2b2b2b', font=('Arial', 12)).pack(side="left", padx=(10, 5))
            self.url_var = tk.StringVar(value="https://www.google.com")
            self.url_entry = tk.Entry(url_frame, textvariable=self.url_var, width=50, bg='#404040', fg='white')
            self.url_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)
            
            self.send_button = tk.Button(
                url_frame,
                text="🚀 Send Request",
                command=self.send_request,
                bg='#28a745',
                fg='white',
                relief="flat"
            )
            self.send_button.pack(side="right", padx=(0, 10))
            
            quick_frame = tk.Frame(self.request_window, bg='#2b2b2b')
            quick_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            quick_urls = [
                ("🌐 HTTP Test", "http://httpbin.org/get"),
                ("🔒 HTTPS Test", "https://httpbin.org/get"),
                ("🔍 Google", "https://www.google.com"),
                ("📚 GitHub API", "https://api.github.com/users/octocat"),
                ("📄 JSON Test", "https://jsonplaceholder.typicode.com/posts/1")
            ]
            
            for i, (text, url) in enumerate(quick_urls):
                btn = tk.Button(
                    quick_frame,
                    text=text,
                    command=lambda u=url: self.set_url(u),
                    bg='#007bff',
                    fg='white',
                    relief="flat",
                    width=20,
                    height=2
                )
                btn.grid(row=i//3, column=i%3, padx=5, pady=5)
            
            quick_frame.grid_columnconfigure(0, weight=1)
            quick_frame.grid_columnconfigure(1, weight=1)
            quick_frame.grid_columnconfigure(2, weight=1)
            
            response_frame = tk.Frame(self.request_window, bg='#2b2b2b')
            response_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            
            tk.Label(response_frame, text="📄 Response", fg='white', bg='#2b2b2b', font=('Arial', 14, 'bold')).pack(pady=(10, 5))
            
            self.response_area = scrolledtext.ScrolledText(
                response_frame,
                font=('Consolas', 10),
                bg='#1e1e1e',
                fg='#00ff00',
                insertbackground='white'
            )
            self.response_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.windows['request'] = self.request_window
    
    def create_latency_window(self):
        """Create the latency monitoring window"""
        if CUSTOM_TKINTER_AVAILABLE:
            self.latency_window = ctk.CTkToplevel(self.main_window)
            self.latency_window.title("📈 Latency Monitor")
            self.latency_window.geometry("800x600")
            self.latency_window.withdraw()
        else:
            self.latency_window = tk.Toplevel(self.main_window)
            self.latency_window.title("📈 Latency Monitor")
            self.latency_window.geometry("800x600")
            self.latency_window.withdraw()
            self.latency_window.configure(bg='#2b2b2b')
        
        # Title
        if CUSTOM_TKINTER_AVAILABLE:
            title = ctk.CTkLabel(self.latency_window, text="📈 Request Latency Monitor", font=ctk.CTkFont(size=20, weight="bold"))
            title.pack(pady=(20, 10))
            
            # Stats frame
            stats_frame = ctk.CTkFrame(self.latency_window)
            stats_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            self.latency_stats_label = ctk.CTkLabel(
                stats_frame,
                text="Requests: 0 | Avg Latency: 0ms | Min: 0ms | Max: 0ms",
                font=ctk.CTkFont(size=14)
            )
            self.latency_stats_label.pack(pady=10)
            
        else:
            title = tk.Label(self.latency_window, text="📈 Request Latency Monitor", font=('Arial', 16, 'bold'), fg='white', bg='#2b2b2b')
            title.pack(pady=(20, 10))
            
            stats_frame = tk.Frame(self.latency_window, bg='#2b2b2b')
            stats_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            self.latency_stats_label = tk.Label(
                stats_frame,
                text="Requests: 0 | Avg Latency: 0ms | Min: 0ms | Max: 0ms",
                font=('Arial', 12),
                fg='white',
                bg='#2b2b2b'
            )
            self.latency_stats_label.pack(pady=10)
        
        # Create matplotlib figure with dark theme
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#2b2b2b')
        
        # Style the plot
        self.ax.grid(True, alpha=0.3, color='#404040')
        self.ax.set_xlabel('Request #', color='white', fontsize=12)
        self.ax.set_ylabel('Latency (ms)', color='white', fontsize=12)
        self.ax.tick_params(colors='white')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.latency_window)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.windows['latency'] = self.latency_window
    
    def center_window(self, window):
        """Center a window on screen"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')
    
    def open_logs_window(self):
        """Open the logs window"""
        if 'logs' in self.windows and self.windows['logs'] and self.windows['logs'].winfo_exists():
            if self.windows['logs'].state() == 'withdrawn':
                self.windows['logs'].deiconify()
                self.center_window(self.windows['logs'])
            else:
                self.windows['logs'].lift()
    
    def open_cache_window(self):
        """Open the cache window"""
        if 'cache' in self.windows and self.windows['cache'] and self.windows['cache'].winfo_exists():
            if self.windows['cache'].state() == 'withdrawn':
                self.windows['cache'].deiconify()
                self.center_window(self.windows['cache'])
            else:
                self.windows['cache'].lift()
    
    def open_request_window(self):
        """Open the request window"""
        if 'request' in self.windows and self.windows['request'] and self.windows['request'].winfo_exists():
            if self.windows['request'].state() == 'withdrawn':
                self.windows['request'].deiconify()
                self.center_window(self.windows['request'])
            else:
                self.windows['request'].lift()
    
    def open_latency_window(self):
        """Open the latency window"""
        if 'latency' in self.windows and self.windows['latency'] and self.windows['latency'].winfo_exists():
            if self.windows['latency'].state() == 'withdrawn':
                self.windows['latency'].deiconify()
                self.center_window(self.windows['latency'])
            else:
                self.windows['latency'].lift()
    
    def open_security_window(self):
        """Open the security/malware detection window"""
        if 'security' in self.windows and self.windows['security'] and self.windows['security'].winfo_exists():
            self.windows['security'].deiconify()
            self.windows['security'].lift()
        else:
            self.create_security_window()
    
    def create_security_window(self):
        """Create the security window for malware detection display"""
        if CUSTOM_TKINTER_AVAILABLE:
            self.security_window = ctk.CTkToplevel(self.main_window)
            self.security_window.title("🛡️ Security Monitor")
            self.security_window.geometry("800x600")
            self.security_window.configure(fg_color="#2b2b2b")
        else:
            self.security_window = tk.Toplevel(self.main_window)
            self.security_window.title("🛡️ Security Monitor")
            self.security_window.geometry("800x600")
            self.security_window.configure(bg='#2b2b2b')
        
        self.windows['security'] = self.security_window
        
        # Title
        if CUSTOM_TKINTER_AVAILABLE:
            title_label = ctk.CTkLabel(
                self.security_window,
                text="🛡️ Security Monitor",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(pady=20)
        else:
            title_label = tk.Label(
                self.security_window,
                text="🛡️ Security Monitor",
                font=('Arial', 24, 'bold'),
                bg='#2b2b2b',
                fg='white'
            )
            title_label.pack(pady=20)
        
        # Security stats frame
        stats_frame = ctk.CTkFrame(self.security_window) if CUSTOM_TKINTER_AVAILABLE else tk.Frame(self.security_window, bg='#3a3a3a')
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Stats display
        if CUSTOM_TKINTER_AVAILABLE:
            self.security_stats_label = ctk.CTkLabel(
                stats_frame,
                text="Total: 0 | Safe: 0 | Malicious: 0 | Blocked: 0 | Avg Score: 0.00",
                font=ctk.CTkFont(size=14)
            )
            self.security_stats_label.pack(pady=10)
        else:
            self.security_stats_label = tk.Label(
                stats_frame,
                text="Total: 0 | Safe: 0 | Malicious: 0 | Blocked: 0 | Avg Score: 0.00",
                font=('Arial', 14),
                bg='#3a3a3a',
                fg='white'
            )
            self.security_stats_label.pack(pady=10)
        
        # Control buttons frame
        control_frame = ctk.CTkFrame(self.security_window) if CUSTOM_TKINTER_AVAILABLE else tk.Frame(self.security_window, bg='#3a3a3a')
        control_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        if CUSTOM_TKINTER_AVAILABLE:
            self.test_malware_btn = ctk.CTkButton(
                control_frame,
                text="🧪 Test Malware Detection",
                command=self.test_malware_detection,
                fg_color="#17a2b8",
                hover_color="#138496"
            )
            self.test_malware_btn.pack(side="left", padx=(0, 10))
            
            self.clear_security_btn = ctk.CTkButton(
                control_frame,
                text="🗑️ Clear Security Log",
                command=self.clear_security_log,
                fg_color="#6c757d",
                hover_color="#5a6268"
            )
            self.clear_security_btn.pack(side="left", padx=(0, 10))
            
            self.refresh_security_btn = ctk.CTkButton(
                control_frame,
                text="🔄 Refresh Security Data",
                command=self.refresh_security_data,
                fg_color="#28a745",
                hover_color="#218838"
            )
            self.refresh_security_btn.pack(side="left")
        else:
            self.test_malware_btn = tk.Button(
                control_frame,
                text="🧪 Test Malware Detection",
                command=self.test_malware_detection,
                bg='#17a2b8',
                fg='white',
                relief="flat"
            )
            self.test_malware_btn.pack(side="left", padx=(0, 10))
            
            self.clear_security_btn = tk.Button(
                control_frame,
                text="🗑️ Clear Security Log",
                command=self.clear_security_log,
                bg='#6c757d',
                fg='white',
                relief="flat"
            )
            self.clear_security_btn.pack(side="left", padx=(0, 10))
            
            self.refresh_security_btn = tk.Button(
                control_frame,
                text="🔄 Refresh Security Data",
                command=self.refresh_security_data,
                bg='#28a745',
                fg='white',
                relief="flat"
            )
            self.refresh_security_btn.pack(side="left")
        
        # Security log frame
        log_frame = ctk.CTkFrame(self.security_window) if CUSTOM_TKINTER_AVAILABLE else tk.Frame(self.security_window, bg='#3a3a3a')
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        if CUSTOM_TKINTER_AVAILABLE:
            log_label = ctk.CTkLabel(
                log_frame,
                text="🔍 Security Analysis Log",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            log_label.pack(pady=10)
        else:
            log_label = tk.Label(
                log_frame,
                text="🔍 Security Analysis Log",
                font=('Arial', 16, 'bold'),
                bg='#3a3a3a',
                fg='white'
            )
            log_label.pack(pady=10)
        
        # Security log text area
        if CUSTOM_TKINTER_AVAILABLE:
            self.security_log_text = ctk.CTkTextbox(
                log_frame,
                font=ctk.CTkFont(size=12),
                fg_color="#1e1e1e",
                text_color="#ffffff"
            )
            self.security_log_text.pack(fill="both", expand=True, padx=10, pady=10)
        else:
            self.security_log_text = tk.Text(
                log_frame,
                font=('Consolas', 12),
                bg='#1e1e1e',
                fg='#ffffff',
                insertbackground='white'
            )
            self.security_log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollbar for non-customtkinter
        if not CUSTOM_TKINTER_AVAILABLE:
            scrollbar = tk.Scrollbar(log_frame, command=self.security_log_text.yview)
            scrollbar.pack(side="right", fill="y")
            self.security_log_text.config(yscrollcommand=scrollbar.set)
        
        # Initialize security log
        self.security_log_text.insert("end", "🛡️ Security Monitor Started\n")
        self.security_log_text.insert("end", "=" * 50 + "\n")
        self.security_log_text.insert("end", "Waiting for security events...\n\n")
        
        # Bind window close event
        self.security_window.protocol("WM_DELETE_WINDOW", lambda: self.security_window.withdraw())
    
    def test_malware_detection(self):
        """Test the malware detection system with sample URLs"""
        test_urls = [
            "https://www.google.com",  # Should be safe
            "https://httpbin.org/get",  # Should be safe
            "http://free-bitcoin.ru/get-rich-now",  # Should be flagged
            "https://secure-login.ph1sh.xyz/index.php?id=123",  # Should be flagged
            "http://malware-download.biz/<script>alert(1)</script>"  # Should be flagged
        ]
        
        self.log_security_event("🧪 Testing malware detection system...")
        
        for url in test_urls:
            try:
                # Call the URL security middleware
                result = self.check_url_security(url)
                self.log_security_event(f"🔍 {url}")
                self.log_security_event(f"   Prediction: {result['prediction']}")
                self.log_security_event(f"   Score: {result['score']}")
                self.log_security_event(f"   Safe: {'✅ YES' if result['is_safe'] else '❌ NO'}")
                if result.get('explanation'):
                    self.log_security_event(f"   Explanation: {result['explanation']}")
                self.log_security_event("")
                
                # Update stats
                self.update_security_stats(result)
                
            except Exception as e:
                self.log_security_event(f"❌ Error testing {url}: {str(e)}")
    
    def check_url_security(self, url):
        """Check URL security using the middleware"""
        try:
            import subprocess
            import json
            
            # Call the URL checker script
            cmd = ["cd", "../url-security-middleware", "&&", "./venv/bin/python3", "url_checker.py", url]
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            # Parse the output
            output = result.stdout
            prediction = "unknown"
            score = 0.0
            is_safe = True
            explanation = ""
            
            for line in output.split('\n'):
                if line.startswith('PREDICTION:'):
                    prediction = line.split(':', 1)[1].strip()
                elif line.startswith('SCORE:'):
                    try:
                        score = float(line.split(':', 1)[1].strip())
                    except:
                        score = 0.0
                elif line.startswith('RESULT:'):
                    try:
                        result_value = int(line.split(':', 1)[1].strip())
                        is_safe = (result_value == 0)
                    except:
                        is_safe = True
                elif line.startswith('EXPLANATION:'):
                    explanation = line.split(':', 1)[1].strip()
            
            return {
                'prediction': prediction,
                'score': score,
                'is_safe': is_safe,
                'explanation': explanation
            }
            
        except Exception as e:
            return {
                'prediction': 'error',
                'score': 1.0,
                'is_safe': False,
                'explanation': f'Error: {str(e)}'
            }
    
    def log_security_event(self, message):
        """Log a security event to the security log"""
        try:
            if hasattr(self, 'security_log_text') and self.security_log_text and self.security_log_text.winfo_exists():
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_entry = f"[{timestamp}] {message}\n"
                self.security_log_text.insert("end", log_entry)
                self.security_log_text.see("end")
            else:
                print(f"[SECURITY] {message}")
        except Exception as e:
            print(f"[SECURITY] Error logging: {e}")
    
    def update_security_stats(self, result):
        """Update security statistics"""
        try:
            self.security_stats['total_requests'] += 1
            
            if result['is_safe']:
                self.security_stats['safe_urls'] += 1
            else:
                self.security_stats['malicious_urls'] += 1
                self.security_stats['blocked_urls'] += 1
            
            # Update average score
            total_score = self.security_stats['avg_score'] * (self.security_stats['total_requests'] - 1) + result['score']
            self.security_stats['avg_score'] = total_score / self.security_stats['total_requests']
            
            # Update display
            self.update_security_stats_display()
            
        except Exception as e:
            print(f"Error updating security stats: {e}")
    
    def update_security_stats_display(self):
        """Update the security stats display"""
        try:
            if hasattr(self, 'security_stats_label') and self.security_stats_label and self.security_stats_label.winfo_exists():
                stats_text = f"Total: {self.security_stats['total_requests']} | Safe: {self.security_stats['safe_urls']} | Malicious: {self.security_stats['malicious_urls']} | Blocked: {self.security_stats['blocked_urls']} | Avg Score: {self.security_stats['avg_score']:.2f}"
                self.security_stats_label.configure(text=stats_text)
        except Exception as e:
            print(f"Error updating security stats display: {e}")
    
    def clear_security_log(self):
        """Clear the security log"""
        try:
            if hasattr(self, 'security_log_text') and self.security_log_text and self.security_log_text.winfo_exists():
                self.security_log_text.delete(1.0, "end")
                self.security_log_text.insert("end", "🛡️ Security Monitor Started\n")
                self.security_log_text.insert("end", "=" * 50 + "\n")
                self.security_log_text.insert("end", "Security log cleared.\n\n")
        except Exception as e:
            print(f"Error clearing security log: {e}")
    
    def refresh_security_data(self):
        """Refresh security data from logs"""
        try:
            # Try to read from the proxy's security log
            log_file = "../proxy/logs/url_security.log"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-20:]  # Last 20 lines
                    
                    self.log_security_event("🔄 Refreshing from security log...")
                    for line in recent_lines:
                        if line.strip():
                            self.log_security_event(line.strip())
                    self.log_security_event("")
            else:
                self.log_security_event("ℹ️ No security log file found. Start the proxy to see security events.")
                
        except Exception as e:
            self.log_security_event(f"❌ Error refreshing security data: {str(e)}")
    
    def parse_security_event(self, output):
        """Parse security events from proxy output"""
        try:
            # Look for URL security check results
            if 'URL security check' in output:
                # Extract URL and result
                url_match = re.search(r'URL: ([^\s]+)', output)
                if url_match:
                    url = url_match.group(1)
                    
                    # Determine if it's safe or malicious
                    is_safe = 'safe' in output.lower() and 'malicious' not in output.lower()
                    
                    # Create a basic result structure
                    result = {
                        'prediction': 'benign' if is_safe else 'malicious',
                        'score': 0.0 if is_safe else 0.8,
                        'is_safe': is_safe,
                        'explanation': 'URL security check completed'
                    }
                    
                    # Log to security window
                    self.log_security_event(f"🔍 Security Check: {url}")
                    self.log_security_event(f"   Result: {'✅ SAFE' if is_safe else '❌ MALICIOUS'}")
                    self.log_security_event(f"   Score: {result['score']}")
                    self.log_security_event("")
                    
                    # Update stats
                    self.update_security_stats(result)
                    
        except Exception as e:
            print(f"Error parsing security event: {e}")
    
    def setup_monitoring(self):
        """Setup monitoring thread"""
        self.monitor_thread = threading.Thread(target=self.monitor_output, daemon=True)
        self.monitor_thread.start()
    
    def log_message(self, message):
        """Add a message to the logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Check if logs_text exists and is valid before using it
        if hasattr(self, 'logs_text') and self.logs_text and self.logs_text.winfo_exists():
            try:
                if CUSTOM_TKINTER_AVAILABLE:
                    self.logs_text.insert("end", log_entry)
                    self.logs_text.see("end")
                else:
                    self.logs_text.insert("end", log_entry)
                    self.logs_text.see("end")
            except Exception:
                # If logging fails, just print to console
                print(f"[{timestamp}] {message}")
        else:
            # If logs window not available, print to console
            print(f"[{timestamp}] {message}")
    
    def clear_logs(self):
        """Clear the logs"""
        if CUSTOM_TKINTER_AVAILABLE:
            self.logs_text.delete("1.0", "end")
        else:
            self.logs_text.delete("1.0", "end")
    
    def start_proxy(self):
        """Start the proxy server"""
        try:
            if self.process:
                self.log_message("⚠️ Proxy server is already running!")
                return
            
            port = self.port_var.get()
            cache_size = self.cache_var.get()
            
            # Validate inputs
            try:
                port_num = int(port)
                if port_num < 1 or port_num > 65535:
                    raise ValueError("Port must be between 1 and 65535")
            except ValueError:
                self.log_message("❌ Invalid port number!")
                return
            
            try:
                cache_num = int(cache_size)
                if cache_num < 1 or cache_num > 1000:
                    raise ValueError("Cache size must be between 1 and 1000")
            except ValueError:
                self.log_message("❌ Invalid cache size!")
                return
            
            # Build command
            cmd = f"cd ../proxy && ./proxy_server {port} {cache_size}"
            
            self.log_message(f"🚀 Starting proxy server on port {port} with cache size {cache_size}...")
            
            # Start proxy process
            self.process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Start monitoring
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_output, daemon=True)
            self.monitor_thread.start()
            
            self.log_message("✅ Proxy server started successfully!")
            
            # Auto-open logs window after a delay
            self.main_window.after(1000, self.open_logs_window)
            
        except Exception as e:
            self.log_message(f"❌ Failed to start proxy server: {str(e)}")
            self.process = None
    
    def stop_proxy(self):
        """Stop the proxy server"""
        try:
            if not self.process:
                self.log_message("⚠️ Proxy server is not running!")
                return
            
            self.log_message("🛑 Stopping proxy server...")
            
            # Stop monitoring
            self.monitoring = False
            
            # Terminate process
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                self.process = None
            
            self.log_message("✅ Proxy server stopped successfully!")
            
        except Exception as e:
            self.log_message(f"❌ Error stopping proxy server: {str(e)}")
            self.process = None
    
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
            response_text = f"✅ Request Successful!\n"
            response_text += f"Status: {response.status_code}\n"
            response_text += f"Latency: {latency:.2f}ms\n"
            response_text += f"Size: {len(response.content)} bytes\n"
            response_text += f"Headers:\n"
            
            for header, value in response.headers.items():
                response_text += f"  {header}: {value}\n"
            
            response_text += f"\n📄 Body (first 1000 chars):\n"
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
            error_msg = f"❌ Request failed: {str(e)}"
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
            self.ax.plot(x, self.latency_data, 'o-', color='#00ff00', linewidth=2, markersize=6, alpha=0.8)
            
            # Style the plot
            self.ax.grid(True, alpha=0.3, color='#404040')
            self.ax.set_xlabel('Request #', color='white', fontsize=12)
            self.ax.set_ylabel('Latency (ms)', color='white', fontsize=12)
            self.ax.tick_params(colors='white')
            
            # Set y-axis limits
            if max(self.latency_data) > 0:
                self.ax.set_ylim(0, max(self.latency_data) * 1.1)
            
            # Update stats
            avg_latency = sum(self.latency_data) / len(self.latency_data)
            min_latency = min(self.latency_data)
            max_latency = max(self.latency_data)
            
            stats_text = f"Requests: {len(self.latency_data)} | Avg: {avg_latency:.1f}ms | Min: {min_latency:.1f}ms | Max: {max_latency:.1f}ms"
            
            if CUSTOM_TKINTER_AVAILABLE:
                self.latency_stats_label.configure(text=stats_text)
            else:
                self.latency_stats_label.configure(text=stats_text)
            
            self.canvas.draw()
    
    def update_cache_tree(self, entry_num, url, path, size, freq, score):
        """Update the cache tree with new data"""
        try:
            print(f"[DEBUG] update_cache_tree called with: entry={entry_num}, url={url}, path={path}, size={size}, freq={freq}, score={score}")
            
            # Check if this entry already exists
            existing_item = None
            for item in self.cache_tree.get_children():
                item_values = self.cache_tree.item(item)['values']
                if item_values and len(item_values) > 0 and item_values[0] == url and item_values[1] == path:
                    existing_item = item
                    break
            
            # Add new item with timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Convert size to KB if it's a number
            try:
                size_kb = f"{float(size)/1024:.1f}" if size.replace('.', '').replace('-', '').isdigit() else size
            except:
                size_kb = size
            
            # Format score for better readability
            try:
                score_formatted = f"{float(score):.4f}" if score.replace('.', '').replace('-', '').replace('e', '').replace('E', '').isdigit() else score
            except:
                score_formatted = score
            
            print(f"[DEBUG] Formatted values: size_kb={size_kb}, score_formatted={score_formatted}")
            
            if existing_item:
                # Update existing item
                print(f"[DEBUG] Updating existing item: {existing_item}")
                self.cache_tree.item(existing_item, values=(url, path, size_kb, freq, score_formatted, timestamp))
            else:
                # Add new item
                print(f"[DEBUG] Adding new item to cache tree")
                self.cache_tree.insert("", "end", values=(url, path, size_kb, freq, score_formatted, timestamp))
            
            # Update cache stats
            total_entries = len(self.cache_tree.get_children())
            stats_text = f"Cache: {total_entries}/{self.cache_var.get()} entries | Hits: {self.cache_hits} | Misses: {self.cache_misses}"
            
            print(f"[DEBUG] Updated stats: {stats_text}")
            
            if hasattr(self, 'cache_stats_label') and self.cache_stats_label and self.cache_stats_label.winfo_exists():
                try:
                    if CUSTOM_TKINTER_AVAILABLE:
                        self.cache_stats_label.configure(text=stats_text)
                    else:
                        self.cache_stats_label.configure(text=stats_text)
                    print(f"[DEBUG] Cache stats label updated successfully")
                except Exception as e:
                    print(f"[DEBUG] Error updating cache stats label: {e}")
                    
        except Exception as e:
            print(f"Error updating cache tree: {e}")
            import traceback
            traceback.print_exc()
    
    def refresh_cache_display(self):
        """Refresh the cache display by clearing and repopulating the treeview"""
        if CUSTOM_TKINTER_AVAILABLE:
            self.cache_tree.delete(*self.cache_tree.get_children())
            self.cache_stats_label.configure(text="Cache: 0/20 entries | Hits: 0 | Misses: 0")
        else:
            self.cache_tree.delete(*self.cache_tree.get_children())
            self.cache_stats_label.configure(text="Cache: 0/20 entries | Hits: 0 | Misses: 0")
        self.log_message("Cache display refreshed.")
    
    def clear_cache_display(self):
        """Clear the cache display in the treeview"""
        if CUSTOM_TKINTER_AVAILABLE:
            self.cache_tree.delete(*self.cache_tree.get_children())
            self.cache_stats_label.configure(text="Cache: 0/20 entries | Hits: 0 | Misses: 0")
        else:
            self.cache_tree.delete(*self.cache_tree.get_children())
            self.cache_stats_label.configure(text="Cache: 0/20 entries | Hits: 0 | Misses: 0")
        self.log_message("Cache display cleared.")

    def update_cache_stats_display(self):
        """Update the cache stats display with current hit/miss counts"""
        try:
            if hasattr(self, 'cache_stats_label') and self.cache_stats_label and self.cache_stats_label.winfo_exists():
                stats_text = f"Cache: {self.cache_entries}/{self.max_cache_size} entries | Hits: {self.cache_hits} | Misses: {self.cache_misses}"
                self.cache_stats_label.configure(text=stats_text)
        except Exception as e:
            print(f"Error updating cache stats display: {e}")
    
    def add_test_cache_entry(self):
        """Add a test cache entry to the treeview for debugging"""
        if CUSTOM_TKINTER_AVAILABLE:
            self.update_cache_tree("1", "https://test.com/test", "/test.html", "1024", "1", "1.0000")
            self.log_message("Test cache entry added.")
        else:
            self.update_cache_tree("1", "https://test.com/test", "/test.html", "1024", "1", "1.0000")
            self.log_message("Test cache entry added.")
    
    def test_cache_hit(self):
        """Simulate a cache hit for debugging"""
        self.cache_hits += 1
        self.update_cache_stats_display()
        self.log_message("Simulated Cache HIT!")
    
    def test_cache_miss(self):
        """Simulate a cache miss for debugging"""
        self.cache_misses += 1
        self.update_cache_stats_display()
        self.log_message("Simulated Cache MISS!")
    
    def test_latency_tracking(self):
        """Test the latency tracking functionality"""
        if hasattr(self, 'last_request_latency'):
            self.log_message("⏱️ Latency Tracking Test:")
            for domain, latency in self.last_request_latency.items():
                self.log_message(f"   {domain}: {latency}ms")
            if not self.last_request_latency:
                self.log_message("   No latency data stored yet")
        else:
            self.log_message("⏱️ Latency tracking not initialized")
        
        # Test with a sample latency
        if not hasattr(self, 'last_request_latency'):
            self.last_request_latency = {}
        self.last_request_latency['test.example.com'] = 1234.56
        self.log_message("✅ Added test latency: test.example.com = 1234.56ms")
    
    def monitor_output(self):
        """Monitor the proxy output"""
        while self.monitoring:
            if self.process:
                try:
                    output = self.process.stdout.readline()
                    if output:
                        # Clean up the output for better readability
                        clean_output = output.strip()
                        
                        # Parse cache state from output - improved regex patterns
                        cache_patterns = [
                            r'Entry (\d+): ([^ ]+) size=([^ ]+) freq=(\d+) score=([^ ]+)',
                            r'Entry (\d+): ([^ ]+) size=([^ ]+) freq=(\d+) score=([^ ]+)',
                            r'=== Cache State ===',
                            r'Total entries: (\d+)/(\d+)',
                            r'Hits: (\d+)',
                            r'Misses: (\d+)'
                        ]
                        
                        # Check for cache entries
                        cache_match = re.search(r'Entry (\d+): ([^ ]+)  size=([^ ]+)  freq=(\d+)  score=([^ ]+)', clean_output)
                        if cache_match:
                            entry_num = cache_match.group(1)
                            full_url = cache_match.group(2)
                            size = cache_match.group(3)
                            freq = cache_match.group(4)
                            score = cache_match.group(5)
                            
                            # Debug logging
                            print(f"[DEBUG] Cache entry found: Entry {entry_num}, URL: {full_url}, Size: {size}, Freq: {freq}, Score: {score}")
                            
                            # Split URL and path
                            if '/' in full_url:
                                url = full_url.split('/', 1)[0]
                                path = '/' + full_url.split('/', 1)[1]
                            else:
                                url = full_url
                                path = "/"
                            
                            print(f"[DEBUG] Parsed: URL={url}, Path={path}")
                            
                            # Simple logic: if freq > 1, it's a hit; if freq = 1, it's a miss
                            if int(freq) > 1:
                                self.cache_hits += 1
                                print(f"[DEBUG] Cache HIT detected for {url} (freq={freq})")
                            else:
                                self.cache_misses += 1
                                print(f"[DEBUG] Cache MISS detected for {url} (freq={freq})")
                            
                            # Update cache tree only if window exists
                            if hasattr(self, 'cache_tree') and self.cache_tree and self.cache_tree.winfo_exists():
                                try:
                                    self.main_window.after(0, self.update_cache_tree, entry_num, url, path, size, freq, score)
                                    print(f"[DEBUG] Cache tree update scheduled for Entry {entry_num}")
                                except Exception as e:
                                    print(f"[DEBUG] Error scheduling cache update: {e}")
                            else:
                                print(f"[DEBUG] Cache tree not available or not valid")
                        
                        # Check for cache state summary
                        cache_state_match = re.search(r'Size  : (\d+) / (\d+)', clean_output)
                        if cache_state_match:
                            current_entries = cache_state_match.group(1)
                            max_entries = cache_state_match.group(2)
                            
                            # Update our internal counters
                            self.cache_entries = int(current_entries)
                            self.max_cache_size = int(max_entries)
                            
                            # Update cache stats if available
                            if hasattr(self, 'cache_stats_label') and self.cache_stats_label and self.cache_stats_label.winfo_exists():
                                try:
                                    hits_match = re.search(r'Hits  : (\d+)', clean_output)
                                    misses_match = re.search(r'Misses: (\d+)', clean_output)
                                    
                                    if hits_match:
                                        self.cache_hits = int(hits_match.group(1))
                                    if misses_match:
                                        self.cache_misses = int(misses_match.group(1))
                                    
                                    stats_text = f"Cache: {self.cache_entries}/{self.max_cache_size} entries | Hits: {self.cache_hits} | Misses: {self.cache_misses}"
                                    self.main_window.after(0, lambda: self.cache_stats_label.configure(text=stats_text))
                                except Exception:
                                    pass
                        
                        # Check for malware detection results
                        if 'PREDICTION:' in clean_output:
                            prediction_match = re.search(r'PREDICTION: ([^\n]+)', clean_output)
                            if prediction_match:
                                prediction = prediction_match.group(1).strip()
                                
                                # Look for score and explanation in nearby lines
                                score = 0.0
                                explanation = ""
                                
                                # Check if this is a benign (allowlisted) result
                                if 'Trusted domain (allowlisted)' in clean_output:
                                    score = 0.0
                                    explanation = "Trusted domain (allowlisted)"
                                elif prediction == 'benign':
                                    score = 0.1
                                    explanation = "ML model classified as benign"
                                else:
                                    score = 0.8
                                    explanation = f"ML model classified as {prediction}"
                                
                                # Log security event
                                self.main_window.after(0, self.log_security_event, f"🔍 Malware Detection: {prediction.upper()}")
                                self.main_window.after(0, self.log_security_event, f"   Score: {score}")
                                self.main_window.after(0, self.log_security_event, f"   Explanation: {explanation}")
                                self.main_window.after(0, self.log_security_event, "")
                                
                                # Update security stats
                                result = {
                                    'prediction': prediction,
                                    'score': score,
                                    'is_safe': prediction == 'benign',
                                    'explanation': explanation
                                }
                                self.main_window.after(0, self.update_security_stats, result)
                        
                        # Format and log the output for better readability
                        try:
                            # Skip very verbose or repetitive output
                            if any(skip in clean_output.lower() for skip in ['debug', 'verbose', 'tensorflow', 'cuda']):
                                continue
                            
                            # Check for request completion to track latency
                            if 'Request completed in' in clean_output:
                                latency_match = re.search(r'Request completed in ([0-9.]+)ms', clean_output)
                                if latency_match:
                                    latency_ms = float(latency_match.group(1))
                                    
                                    # Try to extract the URL from the request
                                    if 'Sending request to:' in clean_output:
                                        url_match = re.search(r'Sending request to: ([^\n]+)', clean_output)
                                        if url_match:
                                            request_url = url_match.group(1).strip()
                                            # Extract domain from URL
                                            if '://' in request_url:
                                                domain = request_url.split('://', 1)[1].split('/', 1)[0]
                                            else:
                                                domain = request_url.split('/', 1)[0]
                                            
                                            # Store latency for this domain
                                            if not hasattr(self, 'last_request_latency'):
                                                self.last_request_latency = {}
                                            self.last_request_latency[domain] = latency_ms
                                            print(f"[DEBUG] Stored latency for {domain}: {latency_ms}ms")
                            
                            # Check for cache hit/miss events
                            if 'HTTPS Cache HIT, serving from cache' in clean_output:
                                self.cache_hits += 1
                                self.main_window.after(0, self.log_message, "🎯 Cache HIT - Serving from cache")
                                self.main_window.after(0, self.update_cache_stats_display)
                            elif 'HTTPS Cache MISS, fetching from server' in clean_output:
                                self.cache_misses += 1
                                self.main_window.after(0, self.log_message, "❌ Cache MISS - Fetching from server")
                                self.main_window.after(0, self.update_cache_stats_display)
                            elif 'Cache HIT' in clean_output or 'cache hit' in clean_output.lower():
                                self.cache_hits += 1
                                self.main_window.after(0, self.log_message, "🎯 Cache HIT - Serving from cache")
                                self.main_window.after(0, self.update_cache_stats_display)
                            elif 'Cache MISS' in clean_output or 'cache miss' in clean_output.lower():
                                self.cache_misses += 1
                                self.main_window.after(0, self.log_message, "❌ Cache MISS - Fetching from server")
                                self.main_window.after(0, self.update_cache_stats_display)
                            # Format cache state output
                            elif '=== Cache State ===' in clean_output:
                                self.main_window.after(0, self.log_message, "🔄 Cache State Update:")
                            elif 'Entry' in clean_output and 'size=' in clean_output:
                                # Don't log individual cache entries to avoid spam
                                continue
                            elif 'HTTPS response cached successfully' in clean_output:
                                self.main_window.after(0, self.log_message, "✅ Response cached successfully")
                            elif 'HTTP/1.1 200' in clean_output:
                                self.main_window.after(0, self.log_message, "✅ HTTP 200 OK Response")
                            elif 'HTTP/1.1 404' in clean_output:
                                self.main_window.after(0, self.log_message, "❌ HTTP 404 Not Found")
                            elif 'HTTP/1.1 500' in clean_output:
                                self.main_window.after(0, self.log_message, "❌ HTTP 500 Server Error")
                            elif 'Accepted new connection' in clean_output:
                                self.main_window.after(0, self.log_message, "🔗 New connection accepted")
                            elif 'Listening on port' in clean_output:
                                self.main_window.after(0, self.log_message, f"🎧 {clean_output}")
                            elif 'Cache size:' in clean_output:
                                self.main_window.after(0, self.log_message, f"💾 {clean_output}")
                            elif 'Sending request to:' in clean_output:
                                self.main_window.after(0, self.log_message, f"🚀 {clean_output}")
                            elif 'Request completed in' in clean_output:
                                self.main_window.after(0, self.log_message, f"⏱️ {clean_output}")
                            elif 'Request failed:' in clean_output:
                                self.main_window.after(0, self.log_message, f"💥 {clean_output}")
                            elif 'URL security check' in clean_output or 'malware detection' in clean_output.lower():
                                # Security-related events
                                if 'blocked' in clean_output.lower() or 'malicious' in clean_output.lower():
                                    self.main_window.after(0, self.log_message, f"🚫 {clean_output}")
                                    # Try to parse security details
                                    self.parse_security_event(clean_output)
                                else:
                                    self.main_window.after(0, self.log_message, f"🛡️ {clean_output}")
                            elif clean_output and len(clean_output) > 10:  # Only log meaningful output
                                self.main_window.after(0, self.log_message, clean_output)
                        
                        except Exception:
                            # If main window is destroyed, just print to console
                            print(f"[PROXY] {clean_output}")
                        
                except Exception as e:
                    pass
            
            time.sleep(0.1)
    
    def on_closing(self):
        """Handle application closing"""
        try:
            # Stop proxy if running
            if self.process:
                self.stop_proxy()
            
            # Stop monitoring
            self.monitoring = False
            
            # Close all windows
            for window_name, window in self.windows.items():
                if window and window.winfo_exists():
                    try:
                        window.destroy()
                    except:
                        pass
            
            # Destroy main window
            self.main_window.destroy()
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
            self.main_window.destroy()
    
    def setup_variables(self):
        """Setup variables for the GUI"""
        self.port_var = tk.StringVar(value="3040")
        self.cache_var = tk.StringVar(value="20")
        self.process = None
        self.latency_data = []
        self.request_count = 0
        self.cache_entries = []
        self.monitoring = True
        self.windows = {}

def main():
    app = ModernProxyGUI()
    
    # Set up closing handler
    app.main_window.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    app.main_window.mainloop()

if __name__ == "__main__":
    main()
