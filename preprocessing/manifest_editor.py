import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
from typing import Dict, List, Any

class ManifestEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Manifest Editor")
        self.root.geometry("800x600")
        
        # Data storage
        self.manifest_data = {
            "language": "english",
            "duration_sec": 0.0,
            "roles": [],
            "recordings": [],
            "sources": {}
        }
        
        self.recording_frames = []
        self.role_vars = []
        
        self.create_widgets()
        
    def create_widgets(self):
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_manifest)
        file_menu.add_command(label="Open", command=self.load_manifest)
        file_menu.add_command(label="Save", command=self.save_manifest)
        file_menu.add_command(label="Save As", command=self.save_manifest_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs with scrollable content
        self.create_main_properties_tab()
        self.create_recordings_tab()
        self.create_sources_tab()
    
    def create_scrollable_frame(self, parent):
        """Create a scrollable frame within the given parent"""
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        return scrollable_frame
    
    def create_main_properties_tab(self):
        """Create the Main Properties tab"""
        # Create tab frame
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Main Properties")
        
        # Create scrollable content
        scrollable_frame = self.create_scrollable_frame(tab_frame)
        
        # Add main properties section
        self.create_main_properties_section(scrollable_frame)
    
    def create_recordings_tab(self):
        """Create the Recordings tab"""
        # Create tab frame
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Recordings")
        
        # Create scrollable content
        scrollable_frame = self.create_scrollable_frame(tab_frame)
        
        # Add recordings section
        self.create_recordings_section(scrollable_frame)
    
    def create_sources_tab(self):
        """Create the Global Sources tab"""
        # Create tab frame
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Global Sources")
        
        # Create scrollable content
        scrollable_frame = self.create_scrollable_frame(tab_frame)
        
        # Add sources section
        self.create_sources_section(scrollable_frame)
        
    def create_main_properties_section(self, parent):
        # Main properties frame
        main_props_frame = ttk.Frame(parent, padding=10)
        main_props_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Language
        ttk.Label(main_props_frame, text="Language:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.language_var = tk.StringVar(value="english")
        ttk.Entry(main_props_frame, textvariable=self.language_var, width=30).grid(row=0, column=1, sticky=tk.W)
        
        # Duration
        ttk.Label(main_props_frame, text="Duration (sec):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.duration_var = tk.StringVar(value="0.0")
        ttk.Entry(main_props_frame, textvariable=self.duration_var, width=30).grid(row=1, column=1, sticky=tk.W)
        
        # Roles
        ttk.Label(main_props_frame, text="Roles:").grid(row=2, column=0, sticky=tk.W + tk.N, padx=(0, 10))
        roles_frame = ttk.Frame(main_props_frame)
        roles_frame.grid(row=2, column=1, sticky=tk.W)
        
        self.roles_frame = roles_frame
        self.create_roles_widgets()
        
    def create_roles_widgets(self):
        # Clear existing role widgets
        for widget in self.roles_frame.winfo_children():
            widget.destroy()
        
        # If no roles exist, set default roles
        if not self.role_vars:
            default_roles = ["moderator", "vis", "domain"]
            self.role_vars = [tk.StringVar(value=role) for role in default_roles]
        
        # Create widgets for existing roles
        for i, var in enumerate(self.role_vars):
            ttk.Entry(self.roles_frame, textvariable=var, width=15).grid(row=i, column=0, padx=(0, 5), pady=2)
            ttk.Button(self.roles_frame, text="Remove", 
                      command=lambda idx=i: self.remove_role(idx)).grid(row=i, column=1, pady=2)
        
        ttk.Button(self.roles_frame, text="Add Role", command=self.add_role).grid(row=len(self.role_vars), column=0, pady=5)
        
    def add_role(self):
        var = tk.StringVar(value="new_role")
        self.role_vars.append(var)
        self.create_roles_widgets()
        self.update_recording_role_combos()
        
    def remove_role(self, index):
        if len(self.role_vars) > 1:
            self.role_vars.pop(index)
            self.create_roles_widgets()
            self.update_recording_role_combos()
    
    def update_recording_role_combos(self):
        """Update the role combobox values in all existing recordings"""
        current_roles = [var.get() for var in self.role_vars] if self.role_vars else ['moderator', 'vis', 'domain']
        for recording_data in self.recording_frames:
            if 'role_combo' in recording_data:
                recording_data['role_combo']['values'] = tuple(current_roles)
        
    def create_recordings_section(self, parent):
        # Recordings frame
        self.recordings_frame = ttk.Frame(parent, padding=10)
        self.recordings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Recordings container
        self.recordings_container = ttk.Frame(self.recordings_frame)
        self.recordings_container.pack(fill=tk.X)
        
        # Add recording button
        ttk.Button(self.recordings_frame, text="Add Recording", 
                  command=self.add_recording).pack(pady=5)
        
    def add_recording(self):
        recording_frame = ttk.LabelFrame(self.recordings_container, 
                                       text=f"Recording {len(self.recording_frames) + 1}", 
                                       padding=10)
        recording_frame.pack(fill=tk.X, pady=5)
        
        # Recording fields
        fields_frame = ttk.Frame(recording_frame)
        fields_frame.pack(fill=tk.X)
        
        # Directory
        ttk.Label(fields_frame, text="Directory:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        dir_var = tk.StringVar()
        dir_frame = ttk.Frame(fields_frame)
        dir_frame.grid(row=0, column=1, sticky=tk.W)
        ttk.Entry(dir_frame, textvariable=dir_var, width=35).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(dir_frame, text="Browse", 
                  command=lambda: self.browse_directory(dir_var)).pack(side=tk.LEFT)
        
        # ID
        ttk.Label(fields_frame, text="ID:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        id_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=id_var, width=40).grid(row=1, column=1, sticky=tk.W)
        
        # Role
        ttk.Label(fields_frame, text="Role:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        role_var = tk.StringVar()
        role_combo = ttk.Combobox(fields_frame, textvariable=role_var, width=37)
        # Get current roles from role_vars, or use defaults if empty
        current_roles = [var.get() for var in self.role_vars] if self.role_vars else ['moderator', 'vis', 'domain']
        role_combo['values'] = tuple(current_roles)
        role_combo.grid(row=2, column=1, sticky=tk.W)
        
        # Start time
        ttk.Label(fields_frame, text="Start Time (system):").grid(row=3, column=0, sticky=tk.W, padx=(0, 10))
        start_time_var = tk.StringVar(value="-1")
        ttk.Entry(fields_frame, textvariable=start_time_var, width=40).grid(row=3, column=1, sticky=tk.W)
        
        # Sources section
        sources_frame = ttk.LabelFrame(recording_frame, text="Sources", padding=5)
        sources_frame.pack(fill=tk.X, pady=5)
        
        sources_container = ttk.Frame(sources_frame)
        sources_container.pack(fill=tk.X)
        
        sources_vars = []
        
        def add_source():
            source_frame = ttk.Frame(sources_container)
            source_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(source_frame, text="Type:").grid(row=0, column=0, padx=(0, 5))
            type_var = tk.StringVar()
            ttk.Entry(source_frame, textvariable=type_var, width=20).grid(row=0, column=1, padx=(0, 5))
            
            ttk.Label(source_frame, text="Path:").grid(row=0, column=2, padx=(0, 5))
            path_var = tk.StringVar()
            path_frame = ttk.Frame(source_frame)
            path_frame.grid(row=0, column=3, padx=(0, 5))
            ttk.Entry(path_frame, textvariable=path_var, width=25).pack(side=tk.LEFT, padx=(0, 2))
            ttk.Button(path_frame, text="Browse", 
                      command=lambda: self.browse_file(path_var)).pack(side=tk.LEFT)
            
            ttk.Label(source_frame, text="Offset:").grid(row=0, column=4, padx=(0, 5))
            offset_var = tk.StringVar(value="0.0")
            ttk.Entry(source_frame, textvariable=offset_var, width=10).grid(row=0, column=5, padx=(0, 5))
            
            ttk.Button(source_frame, text="Remove", 
                      command=lambda: (source_frame.destroy(), sources_vars.remove((type_var, path_var, offset_var)))).grid(row=0, column=6)
            
            sources_vars.append((type_var, path_var, offset_var))
        
        ttk.Button(sources_frame, text="Add Source", command=add_source).pack(pady=2)
        
        # Remove recording button
        def remove_recording():
            recording_frame.destroy()
            self.recording_frames.remove(recording_data)
            self.update_recording_labels()
        
        ttk.Button(recording_frame, text="Remove Recording", 
                  command=remove_recording).pack(pady=5)
        
        # Store recording data
        recording_data = {
            'frame': recording_frame,
            'dir_var': dir_var,
            'id_var': id_var,
            'role_var': role_var,
            'role_combo': role_combo,
            'start_time_var': start_time_var,
            'sources_vars': sources_vars
        }
        
        self.recording_frames.append(recording_data)
        self.update_recording_labels()
        
    def _add_source_to_recording(self, recording_data, source_type="", source_path="", source_offset=0.0):
        """Helper method to add a source UI element to a recording"""
        # Find the sources container for this recording
        sources_container = None
        for child in recording_data['frame'].winfo_children():
            if isinstance(child, ttk.LabelFrame) and child.cget('text') == 'Sources':
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Frame):
                        sources_container = subchild
                        break
                break
        
        if sources_container:
            # Create the source UI widget
            source_frame = ttk.Frame(sources_container)
            source_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(source_frame, text="Type:").grid(row=0, column=0, padx=(0, 5))
            type_var = tk.StringVar(value=source_type)
            ttk.Entry(source_frame, textvariable=type_var, width=20).grid(row=0, column=1, padx=(0, 5))
            
            ttk.Label(source_frame, text="Path:").grid(row=0, column=2, padx=(0, 5))
            path_var = tk.StringVar(value=source_path)
            path_frame = ttk.Frame(source_frame)
            path_frame.grid(row=0, column=3, padx=(0, 5))
            ttk.Entry(path_frame, textvariable=path_var, width=25).pack(side=tk.LEFT, padx=(0, 2))
            ttk.Button(path_frame, text="Browse", 
                      command=lambda: self.browse_file(path_var)).pack(side=tk.LEFT)
            
            ttk.Label(source_frame, text="Offset:").grid(row=0, column=4, padx=(0, 5))
            offset_var = tk.StringVar(value=str(source_offset))
            ttk.Entry(source_frame, textvariable=offset_var, width=10).grid(row=0, column=5, padx=(0, 5))
            
            ttk.Button(source_frame, text="Remove", 
                      command=lambda: (source_frame.destroy(), recording_data['sources_vars'].remove((type_var, path_var, offset_var)))).grid(row=0, column=6)
            
            # Add the variables to the recording's sources_vars list
            recording_data['sources_vars'].append((type_var, path_var, offset_var))

    def update_recording_labels(self):
        for i, recording_data in enumerate(self.recording_frames):
            recording_data['frame'].configure(text=f"Recording {i + 1}")
    
    def create_sources_section(self, parent):
        # Global sources frame
        self.sources_frame = ttk.Frame(parent, padding=10)
        self.sources_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.sources_container = ttk.Frame(self.sources_frame)
        self.sources_container.pack(fill=tk.X)
        
        self.global_sources_vars = []
        
        ttk.Button(self.sources_frame, text="Add Global Source", 
                  command=self.add_global_source).pack(pady=5)
        
    def add_global_source(self):
        source_frame = ttk.Frame(self.sources_container)
        source_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(source_frame, text="Type:").grid(row=0, column=0, padx=(0, 5))
        type_var = tk.StringVar()
        type_entry = ttk.Entry(source_frame, textvariable=type_var, width=15)
        type_entry.grid(row=0, column=1, padx=(0, 5))
        
        # Subtype field (for videos)
        ttk.Label(source_frame, text="Subtype:").grid(row=0, column=2, padx=(0, 5))
        subtype_var = tk.StringVar()
        subtype_entry = ttk.Entry(source_frame, textvariable=subtype_var, width=15)
        subtype_entry.grid(row=0, column=3, padx=(0, 5))
        
        ttk.Label(source_frame, text="Path:").grid(row=0, column=4, padx=(0, 5))
        path_var = tk.StringVar()
        path_frame = ttk.Frame(source_frame)
        path_frame.grid(row=0, column=5, padx=(0, 5))
        ttk.Entry(path_frame, textvariable=path_var, width=30).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(path_frame, text="Browse", 
                  command=lambda: self.browse_file(path_var)).pack(side=tk.LEFT)
        
        ttk.Label(source_frame, text="Offset:").grid(row=0, column=6, padx=(0, 5))
        offset_var = tk.StringVar(value="0.0")
        ttk.Entry(source_frame, textvariable=offset_var, width=10).grid(row=0, column=7, padx=(0, 5))
        
        def remove_source():
            source_frame.destroy()
            self.global_sources_vars.remove((type_var, subtype_var, path_var, offset_var))
        
        ttk.Button(source_frame, text="Remove", command=remove_source).grid(row=0, column=8)
        
        self.global_sources_vars.append((type_var, subtype_var, path_var, offset_var))
    
    def new_manifest(self):
        self.manifest_data = {
            "language": "english",
            "duration_sec": 0.0,
            "roles": [],
            "recordings": [],
            "sources": {}
        }
        self.clear_form()
        
    def clear_form(self):
        # Clear main properties
        self.language_var.set("english")
        self.duration_var.set("0.0")
        
        # Clear roles
        self.role_vars.clear()
        self.create_roles_widgets()
        
        # Clear recordings
        for recording_data in self.recording_frames:
            recording_data['frame'].destroy()
        self.recording_frames.clear()
        
        # Clear global sources
        for widget in self.sources_container.winfo_children():
            widget.destroy()
        self.global_sources_vars.clear()
        
    def load_manifest(self):
        file_path = filedialog.askopenfilename(
            title="Open Manifest File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                self.clear_form()
                
                # Load main properties
                self.language_var.set(data.get("language", "english"))
                self.duration_var.set(str(data.get("duration_sec", 0.0)))
                
                # Load roles
                roles = data.get("roles", [])
                self.role_vars = [tk.StringVar(value=role) for role in roles]
                self.create_roles_widgets()
                
                # Load recordings
                for recording in data.get("recordings", []):
                    self.add_recording()
                    recording_data = self.recording_frames[-1]
                    
                    recording_data['dir_var'].set(recording.get("dir", ""))
                    recording_data['id_var'].set(recording.get("id", ""))
                    recording_data['role_var'].set(recording.get("role", ""))
                    recording_data['start_time_var'].set(str(recording.get("start_time_system_s", -1)))
                    
                    # Load sources for this recording
                    sources = recording.get("sources", {})
                    for source_type, source_data in sources.items():
                        # Create the source UI elements by calling the add_source functionality
                        self._add_source_to_recording(recording_data, source_type, 
                                                    source_data.get("path", ""), 
                                                    source_data.get("offset_sec", 0.0))
                
                # Load global sources
                global_sources = data.get("sources", {})
                for source_type, source_data in global_sources.items():
                    if isinstance(source_data, dict):
                        if "path" in source_data:
                            # Simple source (e.g., audio, notes_snapshots)
                            self.add_global_source()
                            type_var, subtype_var, path_var, offset_var = self.global_sources_vars[-1]
                            type_var.set(source_type)
                            subtype_var.set("")  # No subtype for simple sources
                            path_var.set(source_data.get("path", ""))
                            offset_var.set(str(source_data.get("offset_sec", 0.0)))
                        else:
                            # Nested source (e.g., videos with subtypes)
                            for subtype, subtype_data in source_data.items():
                                if isinstance(subtype_data, dict) and "path" in subtype_data:
                                    self.add_global_source()
                                    type_var, subtype_var, path_var, offset_var = self.global_sources_vars[-1]
                                    type_var.set(source_type)
                                    subtype_var.set(subtype)
                                    path_var.set(subtype_data.get("path", ""))
                                    offset_var.set(str(subtype_data.get("offset_sec", 0.0)))
                
                messagebox.showinfo("Success", "Manifest loaded successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load manifest: {str(e)}")
    
    def save_manifest(self):
        if hasattr(self, 'current_file_path'):
            self.save_to_file(self.current_file_path)
        else:
            self.save_manifest_as()
    
    def save_manifest_as(self):
        file_path = filedialog.asksaveasfilename(
            title="Save Manifest File",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            self.current_file_path = file_path
            self.save_to_file(file_path)
    
    def save_to_file(self, file_path):
        try:
            # Build manifest data from form
            manifest_data = {
                "language": self.language_var.get(),
                "duration_sec": float(self.duration_var.get()),
                "roles": [var.get() for var in self.role_vars if var.get().strip()],
                "recordings": [],
                "sources": {}
            }
            
            # Build recordings
            for recording_data in self.recording_frames:
                recording = {
                    "dir": recording_data['dir_var'].get(),
                    "id": recording_data['id_var'].get(),
                    "role": recording_data['role_var'].get(),
                    "start_time_system_s": int(recording_data['start_time_var'].get()) if recording_data['start_time_var'].get() != "-1" else -1,
                    "sources": {}
                }
                
                # Build sources for this recording
                for type_var, path_var, offset_var in recording_data['sources_vars']:
                    if type_var.get().strip() and path_var.get().strip():
                        recording["sources"][type_var.get()] = {
                            "path": path_var.get(),
                            "offset_sec": float(offset_var.get())
                        }
                
                manifest_data["recordings"].append(recording)
            
            # Build global sources
            for type_var, subtype_var, path_var, offset_var in self.global_sources_vars:
                if type_var.get().strip() and path_var.get().strip():
                    source_type = type_var.get()
                    subtype = subtype_var.get().strip()
                    
                    if subtype:
                        # Handle nested structure (e.g., videos with subtypes)
                        if source_type not in manifest_data["sources"]:
                            manifest_data["sources"][source_type] = {}
                        manifest_data["sources"][source_type][subtype] = {
                            "path": path_var.get(),
                            "offset_sec": float(offset_var.get())
                        }
                    else:
                        # Handle simple structure (e.g., audio, notes_snapshots)
                        manifest_data["sources"][source_type] = {
                            "path": path_var.get(),
                            "offset_sec": float(offset_var.get())
                        }
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(manifest_data, f, indent=4)
            
            messagebox.showinfo("Success", f"Manifest saved to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save manifest: {str(e)}")
    
    def browse_file(self, path_var):
        """Open file dialog to select a file and update the path variable"""
        file_path = filedialog.askopenfilename(
            title="Select File",
            filetypes=[
                ("All files", "*.*"),
                ("CSV files", "*.csv"),
                ("JSON files", "*.json"),
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("Audio files", "*.wav *.mp3 *.aac *.flac"),
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff")
            ]
        )
        if file_path:
            path_var.set(file_path)
    
    def browse_directory(self, path_var):
        """Open directory dialog to select a directory and update the path variable"""
        directory_path = filedialog.askdirectory(
            title="Select Directory"
        )
        if directory_path:
            path_var.set(directory_path)

def main():
    root = tk.Tk()
    app = ManifestEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
