import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import webbrowser
import pyperclip
import threading
from datetime import datetime
from engines import x1337, tpb, yts

class TorrentGUI:
    def __init__(self, root):
        self.root = root
        self.engines = {
            "1337x": x1337.X1337Engine,
            "The Pirate Bay": tpb.TPBEngine,
            "YTS Movies": yts.YTSEngine
        }
        self.selected_engines = list(self.engines.keys())
        self.all_torrents = []
        self.current_page = 1
        self.search_query = ""
        self.loading = False
        self.sort_column = ""
        self.sort_reverse = False
        
        self.setup_ui()
    
    def setup_ui(self):
        self.root.title("Torrent Search")
        self.root.geometry("1200x800")
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure('Treeview', rowheight=25)
        self.style.configure('Treeview.Heading', font=('Helvetica', 10, 'bold'))
        
        self.create_search_frame()
        self.create_engine_selection()
        self.create_results_tree()
        self.create_magnet_frame()
        self.create_button_frame()
        self.create_status_bar()
    
    def create_engine_selection(self):
        frame = ttk.Frame(self.root, padding="5")
        frame.pack(fill=tk.X)
        
        ttk.Label(frame, text="Search Engines:").pack(side=tk.LEFT, padx=5)
        
        self.engine_vars = {}
        for engine in self.engines:
            var = tk.BooleanVar(value=True)
            self.engine_vars[engine] = var
            cb = ttk.Checkbutton(frame, text=engine, variable=var, 
                                command=self.update_selected_engines)
            cb.pack(side=tk.LEFT, padx=5)
    
    def update_selected_engines(self):
        self.selected_engines = [
            engine for engine, var in self.engine_vars.items() if var.get()
        ]
    
    def create_search_frame(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.X)
        
        ttk.Label(frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(frame, width=60)
        self.search_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.search_entry.bind('<Return>', lambda e: self.do_search())
        
        ttk.Button(frame, text="Search", command=self.do_search).pack(side=tk.LEFT, padx=5)
    
    def create_results_tree(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.tree = ttk.Treeview(frame, columns=('engine', 'seeds', 'leeches', 'size', 'date'), selectmode='browse')
        
        # Configure columns
        columns = {
            '#0': {'text': 'Name', 'anchor': tk.W, 'width': 400, 'command': lambda: self.sort_tree('name')},
            'engine': {'text': 'Engine', 'anchor': tk.CENTER, 'width': 80, 'command': lambda: self.sort_tree('engine')},
            'seeds': {'text': 'Seeds ↑', 'anchor': tk.CENTER, 'width': 70, 'command': lambda: self.sort_tree('seeds')},
            'leeches': {'text': 'Leeches', 'anchor': tk.CENTER, 'width': 70, 'command': lambda: self.sort_tree('leeches')},
            'size': {'text': 'Size', 'anchor': tk.CENTER, 'width': 90, 'command': lambda: self.sort_tree('size')},
            'date': {'text': 'Date', 'anchor': tk.CENTER, 'width': 100, 'command': lambda: self.sort_tree('date')}
        }
        
        for col, config in columns.items():
            self.tree.heading(col, text=config['text'], anchor=config['anchor'], command=config.get('command'))
            self.tree.column(col, width=config['width'], anchor=config['anchor'])
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        y_scroll.grid(row=0, column=1, sticky=tk.NS)
        x_scroll.grid(row=1, column=0, sticky=tk.EW)
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
    
    def create_magnet_frame(self):
        frame = ttk.LabelFrame(self.root, text="Magnet Link", padding="10")
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.magnet_text = scrolledtext.ScrolledText(frame, height=4, wrap=tk.WORD)
        self.magnet_text.pack(fill=tk.BOTH, expand=True)
    
    def create_button_frame(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.X)
        
        self.view_more_btn = ttk.Button(frame, text="View More Results", command=self.view_more, state=tk.DISABLED)
        self.view_more_btn.pack(side=tk.LEFT, padx=5)
        
        self.get_magnet_btn = ttk.Button(frame, text="Get Magnet Link", command=self.get_magnet_threaded, state=tk.DISABLED)
        self.get_magnet_btn.pack(side=tk.LEFT, padx=5)
        
        self.copy_btn = ttk.Button(frame, text="Copy Magnet", command=self.copy_magnet, state=tk.DISABLED)
        self.copy_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_magnet_btn = ttk.Button(frame, text="Open Magnet", command=self.open_in_browser, state=tk.DISABLED)
        self.open_magnet_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_page_btn = ttk.Button(frame, text="Open Torrent Page", command=self.open_torrent_page, state=tk.DISABLED)
        self.open_page_btn.pack(side=tk.LEFT, padx=5)
    
    def create_status_bar(self):
        self.status_var = tk.StringVar()
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X, side=tk.BOTTOM)
    
    def do_search(self):
        query = self.search_entry.get().strip()
        if not query or not self.selected_engines:
            messagebox.showwarning("Warning", "Please enter a search term and select at least one engine")
            return
            
        self.search_query = query
        self.all_torrents = []
        self.current_page = 1
        self.status_var.set("Searching...")
        self.root.update_idletasks()
        
        # Disable buttons during search
        self.view_more_btn.config(state=tk.DISABLED)
        self.get_magnet_btn.config(state=tk.DISABLED)
        self.copy_btn.config(state=tk.DISABLED)
        self.open_magnet_btn.config(state=tk.DISABLED)
        self.open_page_btn.config(state=tk.DISABLED)
        
        # Start search in new threads for each engine
        for engine_name in self.selected_engines:
            threading.Thread(
                target=self.perform_search,
                args=(self.engines[engine_name], query, 1),
                daemon=True
            ).start()
    
    def perform_search(self, engine, query, page):
        try:
            new_torrents = engine.search(query, page)
            self.root.after(0, self.handle_search_results, new_torrents)
        except Exception as e:
            self.root.after(0, self.handle_search_error, str(e))
    
    def handle_search_results(self, new_torrents):
        if new_torrents:
            self.all_torrents.extend(new_torrents)
            self.display_results()
            self.status_var.set(f"Found {len(self.all_torrents)} results")
            self.view_more_btn.config(state=tk.NORMAL)
        else:
            self.status_var.set("No results found" if not self.all_torrents else "No more results")
            if not self.all_torrents:
                messagebox.showinfo("Info", "No results found for your search")
    
    def handle_search_error(self, error):
        self.status_var.set("Error during search")
        messagebox.showerror("Error", f"Search failed: {error}")
    
    def display_results(self):
        self.tree.delete(*self.tree.get_children())
        
        for torrent in self.all_torrents:
            self.tree.insert('', 'end', text=torrent['name'], 
                           values=(torrent['engine'], torrent['seeds'], 
                                  torrent['leeches'], torrent['size'], 
                                  torrent['date']))
        
        # Auto-select first item if available
        if self.tree.get_children():
            self.tree.selection_set(self.tree.get_children()[0])
            self.tree.focus(self.tree.get_children()[0])
    
    def view_more(self):
        if self.loading:
            return
            
        self.current_page += 1
        self.status_var.set(f"Loading page {self.current_page}...")
        self.view_more_btn.config(state=tk.DISABLED)
        self.root.update_idletasks()
        
        for engine_name in self.selected_engines:
            threading.Thread(
                target=self.perform_search,
                args=(self.engines[engine_name], self.search_query, self.current_page),
                daemon=True
            ).start()
    
    def get_magnet_threaded(self):
        selected = self.tree.selection()
        if not selected or self.loading:
            return
            
        item = selected[0]
        idx = self.tree.index(item)
        torrent = self.all_torrents[idx]
        
        # Check if we already have magnet (TPB/YTS)
        if 'magnet' in torrent and torrent['magnet']:
            self.root.after(0, self.handle_magnet_result, torrent['magnet'])
            return
            
        self.status_var.set(f"Fetching magnet from {torrent['engine']}...")
        self.get_magnet_btn.config(state=tk.DISABLED)
        self.loading = True
        self.root.update_idletasks()
        
        threading.Thread(
            target=self.fetch_magnet,
            args=(self.engines[torrent['engine']], torrent['url']),
            daemon=True
        ).start()
    
    def fetch_magnet(self, engine, url):
        magnet = engine.get_magnet(url)
        self.root.after(0, self.handle_magnet_result, magnet)
    
    def handle_magnet_result(self, magnet):
        self.loading = False
        if magnet:
            self.magnet_text.delete(1.0, tk.END)
            self.magnet_text.insert(tk.END, magnet)
            self.copy_btn.config(state=tk.NORMAL)
            self.open_magnet_btn.config(state=tk.NORMAL)
            self.status_var.set("Magnet link ready")
        else:
            self.status_var.set("Could not retrieve magnet link")
            messagebox.showerror("Error", "Could not retrieve magnet link")
        
        self.get_magnet_btn.config(state=tk.NORMAL)
    
    def on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.get_magnet_btn.config(state=tk.NORMAL)
            self.open_page_btn.config(state=tk.NORMAL)
        else:
            self.get_magnet_btn.config(state=tk.DISABLED)
            self.open_page_btn.config(state=tk.DISABLED)
            self.open_magnet_btn.config(state=tk.DISABLED)
            self.copy_btn.config(state=tk.DISABLED)
    
    def open_torrent_page(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        item = selected[0]
        idx = self.tree.index(item)
        torrent = self.all_torrents[idx]
        
        try:
            webbrowser.open(torrent['url'])
            self.status_var.set(f"Opened {torrent['name']} in browser")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open page: {str(e)}")
            self.status_var.set("Error opening page")
    
    def sort_tree(self, column):
        if column == self.sort_column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # Update column headers
        for col in ['name', 'engine', 'seeds', 'leeches', 'size', 'date']:
            header_text = col.capitalize()
            if col == self.sort_column:
                header_text += " ↓" if self.sort_reverse else " ↑"
            self.tree.heading(col if col != 'name' else '#0', text=header_text)
        
        # Sort the data
        if column == 'name':
            self.all_torrents.sort(key=lambda x: x['name'].lower(), reverse=self.sort_reverse)
        elif column == 'engine':
            self.all_torrents.sort(key=lambda x: x['engine'], reverse=self.sort_reverse)
        elif column == 'seeds':
            self.all_torrents.sort(key=lambda x: int(x['seeds']), reverse=self.sort_reverse)
        elif column == 'leeches':
            self.all_torrents.sort(key=lambda x: int(x['leeches']), reverse=self.sort_reverse)
        elif column == 'size':
            self.all_torrents.sort(key=self.parse_size, reverse=self.sort_reverse)
        elif column == 'date':
            self.all_torrents.sort(key=self.parse_date, reverse=self.sort_reverse)
        
        self.display_results()
    
    def parse_size(self, item):
        size = item['size']
        if 'GB' in size:
            return float(size.replace('GB', '').strip())
        elif 'MB' in size:
            return float(size.replace('MB', '').strip()) / 1024
        elif 'KB' in size:
            return float(size.replace('KB', '').strip()) / (1024**2)
        return 0
    
    def parse_date(self, item):
        date_str = item['date']
        try:
            if "'" in date_str:  # "Sep. 3rd '12"
                year = "20" + date_str.split("'")[1] if len(date_str.split("'")[1]) == 2 else date_str.split("'")[1]
                month_day = date_str.split("'")[0].strip()
                month = month_day.split()[0].replace('.', '')
                day = month_day.split()[1][:-2]  # Remove 'rd', 'th', etc.
                return datetime.strptime(f"{month} {day} {year}", "%b %d %Y")
            elif '-' in date_str:  # YYYY-MM-DD format
                return datetime.strptime(date_str, "%Y-%m-%d")
            else:
                return datetime.strptime(date_str, "%b %d %Y")
        except:
            return datetime.min
    
    def copy_magnet(self):
        magnet = self.magnet_text.get(1.0, tk.END).strip()
        if magnet:
            try:
                pyperclip.copy(magnet)
                self.status_var.set("Magnet link copied to clipboard")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy to clipboard: {str(e)}")
    
    def open_in_browser(self):
        magnet = self.magnet_text.get(1.0, tk.END).strip()
        if magnet:
            try:
                webbrowser.open(magnet)
                self.status_var.set("Opened in default torrent client")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open link: {str(e)}")