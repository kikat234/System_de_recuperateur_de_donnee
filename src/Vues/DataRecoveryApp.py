import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from datetime import datetime
from pathlib import Path
import threading
import platform
import mmap
from Modeles.AnalyseDesSystemesDeFichiers import FileSystemAnalyzer
from Modeles.DiskDetector import DiskDetector
from Modeles.RecoveryLogger import RecoveryLogger
from Modeles.FilePreview import FilePreview
from Modeles.FileCarver import FileCarver
from Modeles.AnalysePartition import PartitionAnalyzer
from Modeles.RaportGenerator import ReportGenerator
from Modeles.DataAnalyzer import DataAnalyzer
from Modeles.FileScanner import FileScanner
from Modeles.SignatureFichiers import FILE_SIGNATURES
# Import optionnel de PIL pour l'aperçu d'images
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  Pillow n'est pas installé. Les aperçus d'images ne seront pas disponibles.")
    print("   Pour installer : pip install Pillow")
class DataRecoveryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tonio Recovery")
        self.root.geometry("1200x800")
        
        self.logger = RecoveryLogger()
        self.analyzer = DataAnalyzer(self.logger)
        self.scanner = FileScanner(self.logger)
        self.carver = FileCarver(self.logger)
        self.partition_analyzer = PartitionAnalyzer(self.logger)
        self.fs_analyzer = FileSystemAnalyzer(self.logger)
        self.report_generator = ReportGenerator(self.logger)
        self.current_data = None
        self.current_file = None
        self.max_read_gb = tk.DoubleVar(value=2.0)
        self.current_data = None
        self.scan_results = []
        self.current_preview = None
        self.report_data = {}
        self.source_path = ""
        
        self.create_ui()
        
    def get_file_type_emoji(self, file_type):
        """Retourne un emoji approprié pour chaque type de fichier"""
        emojis = {
            'PDF': '📕', 'PNG': '🖼️', 'JPEG': '📷', 'JPEG_ALT': '📷',
            'ZIP': '📦', 'DOCX': '📘', 'XLSX': '📊', 'GIF': '🎬',
            'GIF87': '🎬', 'BMP': '🖼️', 'MP3': '🎵', 'MP4': '🎬',
            'AVI': '🎬', 'EXE': '⚙️', 'RAR': '📦', '7Z': '📦'
        }
        return emojis.get(file_type, '📄')
    
    def select_all_file_types(self):
        """Sélectionne tous les types de fichiers"""
        for var in self.file_type_vars.values():
            var.set(True)
    
    def deselect_all_file_types(self):
        """Désélectionne tous les types de fichiers"""
        for var in self.file_type_vars.values():
            var.set(False)
    
    def select_image_types(self):
        """Sélectionne uniquement les images"""
        self.deselect_all_file_types()
        image_types = ['PNG', 'JPEG', 'JPEG_ALT', 'GIF', 'GIF87', 'BMP']
        for file_type in image_types:
            if file_type in self.file_type_vars:
                self.file_type_vars[file_type].set(True)
    
    def select_document_types(self):
        """Sélectionne uniquement les documents"""
        self.deselect_all_file_types()
        doc_types = ['PDF', 'DOCX', 'XLSX']
        for file_type in doc_types:
            if file_type in self.file_type_vars:
                self.file_type_vars[file_type].set(True)
    
    def select_media_types(self):
        """Sélectionne uniquement les médias"""
        self.deselect_all_file_types()
        media_types = ['MP3', 'MP4', 'AVI']
        for file_type in media_types:
            if file_type in self.file_type_vars:
                self.file_type_vars[file_type].set(True)
    
    def get_selected_file_types(self):
        """Retourne la liste des types sélectionnés"""
        return [file_type for file_type, var in self.file_type_vars.items() if var.get()]
    
    def create_ui(self):
        # Notebook pour onglets
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Onglet 1: Sélection et Analyse
        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text="📁 Sélection & Analyse")
        self.create_selection_tab(tab1)
        
        # Onglet 2: Partitions et Système de fichiers
        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text="💾 Partitions & FS")
        self.create_partition_tab(tab2)
        
        # Onglet 3: Récupération de fichiers
        tab3 = ttk.Frame(notebook)
        notebook.add(tab3, text="🔍 Récupération")
        self.create_recovery_tab(tab3)
        
        # Onglet 4: Rapport
        tab4 = ttk.Frame(notebook)
        notebook.add(tab4, text="📊 Rapport")
        self.create_report_tab(tab4)
        
        # Onglet 5: Logs
        tab5 = ttk.Frame(notebook)
        notebook.add(tab5, text="📋 Logs")
        self.create_logs_tab(tab5)
        
    def create_selection_tab(self, parent):
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Section Sélection
        select_frame = ttk.LabelFrame(main_frame, text="Sélection du Source", padding="10")
        select_frame.pack(fill=tk.X, pady=5)
        
        # Type de source
        type_frame = ttk.Frame(select_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        self.source_type = tk.StringVar(value="file")
        ttk.Radiobutton(type_frame, text="📄 Fichier/Image disque", variable=self.source_type, 
                       value="file").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(type_frame, text="💾 Disque/USB", variable=self.source_type, 
                       value="disk").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(type_frame, text="📂 Dossier", variable=self.source_type, 
                       value="folder").pack(side=tk.LEFT, padx=10)
        
        # Options de scan
        options_frame = ttk.Frame(select_frame)
        options_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(options_frame, text="Options:").pack(side=tk.LEFT, padx=5)
        self.enable_filtering = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Filtrer les faux positifs (recommandé)", 
                       variable=self.enable_filtering).pack(side=tk.LEFT, padx=10)
        # Option: limite de lecture en GB (pour fallback si mmap indisponible)
        ttk.Label(options_frame, text="Max read (GB):").pack(side=tk.LEFT, padx=8)
        tk.Spinbox(options_frame, from_=0.1, to=1024, increment=0.1, width=6, 
               textvariable=self.max_read_gb).pack(side=tk.LEFT, padx=2)
        
        # ← NOUVEAU: Filtrage par type de fichier
        ttk.Separator(select_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        filter_frame = ttk.LabelFrame(select_frame, text="🎯 Filtrer les types de fichiers à rechercher", padding="10")
        filter_frame.pack(fill=tk.X, pady=5)
        
        # Sélection rapide
        quick_frame = ttk.Frame(filter_frame)
        quick_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(quick_frame, text="✅ Tous", 
                  command=self.select_all_file_types).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="❌ Aucun", 
                  command=self.deselect_all_file_types).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="🖼️  Images", 
                  command=self.select_image_types).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="📄 Documents", 
                  command=self.select_document_types).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="🎵 Médias", 
                  command=self.select_media_types).pack(side=tk.LEFT, padx=2)
        
        # Checkboxes pour chaque type
        self.file_type_vars = {}
        checkbox_frame = ttk.Frame(filter_frame)
        checkbox_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Créer les checkboxes en colonne
        file_types = sorted(FILE_SIGNATURES.keys())
        cols = 4
        for idx, file_type in enumerate(file_types):
            row = idx // cols
            col = idx % cols
            
            var = tk.BooleanVar(value=True)
            self.file_type_vars[file_type] = var
            
            # Emoji par type
            emoji = self.get_file_type_emoji(file_type)
            
            frame = ttk.Frame(checkbox_frame)
            frame.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            
            ttk.Checkbutton(frame, text=f"{emoji} {file_type}", 
                           variable=var).pack()
        
        # Sélection
        path_frame = ttk.Frame(select_frame)
        path_frame.pack(fill=tk.X, pady=10)
        
        self.source_var = tk.StringVar()
        ttk.Label(path_frame, text="Source:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(path_frame, textvariable=self.source_var, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="📂 Parcourir", command=self.browse_source).pack(side=tk.LEFT, padx=2)
        
        # Bouton de chargement
        ttk.Button(select_frame, text="🚀 Charger et Analyser", 
                  command=self.load_data, style='Accent.TButton').pack(pady=10)
        
        # Section Analyse
        analysis_frame = ttk.LabelFrame(main_frame, text="Résultats de l'Analyse", padding="10")
        analysis_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Informations
        info_frame = ttk.Frame(analysis_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        # Grille d'informations
        ttk.Label(info_frame, text="📏 Taille:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.size_label = ttk.Label(info_frame, text="0 octets", font=('', 10, 'bold'))
        self.size_label.grid(row=0, column=1, sticky=tk.W, padx=10, pady=2)
        
        ttk.Label(info_frame, text="📊 Récupérabilité:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.recovery_label = ttk.Label(info_frame, text="N/A", font=('', 10, 'bold'))
        self.recovery_label.grid(row=1, column=1, sticky=tk.W, padx=10, pady=2)
        
        ttk.Label(info_frame, text="🗂️ Partitions:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.partition_count_label = ttk.Label(info_frame, text="N/A")
        self.partition_count_label.grid(row=2, column=1, sticky=tk.W, padx=10, pady=2)
        
        ttk.Label(info_frame, text="💾 Système de fichiers:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.fs_label = ttk.Label(info_frame, text="N/A")
        self.fs_label.grid(row=3, column=1, sticky=tk.W, padx=10, pady=2)
        
        ttk.Label(info_frame, text="📦 Fichiers détectés:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        self.files_count_label = ttk.Label(info_frame, text="0")
        self.files_count_label.grid(row=4, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Barre de progression
        progress_frame = ttk.Frame(analysis_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack()
        
        self.progress = ttk.Progressbar(progress_frame, length=600, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Aperçu hexadécimal
        hex_frame = ttk.LabelFrame(analysis_frame, text="Aperçu Hexadécimal (512 premiers octets)", padding="10")
        hex_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.hex_text = scrolledtext.ScrolledText(hex_frame, width=80, height=12, 
                                                  font=("Courier", 9))
        self.hex_text.pack(fill=tk.BOTH, expand=True)
        
    def create_partition_tab(self, parent):
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame pour les informations de partition
        partition_frame = ttk.LabelFrame(main_frame, text="Informations de Partition", padding="10")
        partition_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.partition_text = scrolledtext.ScrolledText(partition_frame, width=100, height=15,
                                                        font=("Courier", 10))
        self.partition_text.pack(fill=tk.BOTH, expand=True)
        
        # Frame pour les systèmes de fichiers
        fs_frame = ttk.LabelFrame(main_frame, text="Systèmes de Fichiers Détectés", padding="10")
        fs_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.fs_text = scrolledtext.ScrolledText(fs_frame, width=100, height=15,
                                                 font=("Courier", 10))
        self.fs_text.pack(fill=tk.BOTH, expand=True)
        
    def create_recovery_tab(self, parent):
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panneau supérieur: Contrôles
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(top_frame, text="Les fichiers sont automatiquement détectés lors du chargement", 
                 font=('', 9, 'italic')).pack(side=tk.LEFT, padx=10)
        
        # PanedWindow pour diviser la vue
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Panneau gauche: Liste des fichiers
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=2)
        
        results_frame = ttk.LabelFrame(left_frame, text="Fichiers Détectés", padding="5")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ('Type', 'Offset', 'Taille')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='tree headings', height=20)
        
        self.tree.heading('#0', text='ID')
        self.tree.column('#0', width=50)
        self.tree.heading('Type', text='Type')
        self.tree.column('Type', width=100)
        self.tree.heading('Offset', text='Offset')
        self.tree.column('Offset', width=120)
        self.tree.heading('Taille', text='Taille')
        self.tree.column('Taille', width=120)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_file_select)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Boutons d'export
        export_frame = ttk.Frame(left_frame)
        export_frame.pack(fill=tk.X, pady=5)
        ttk.Button(export_frame, text="💾 Extraire sélection", 
                  command=self.extract_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="💾 Extraire tout", 
                  command=self.extract_all).pack(side=tk.LEFT, padx=5)
        
        # Panneau droit: Aperçu
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        preview_frame = ttk.LabelFrame(right_frame, text="Aperçu du Fichier", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Zone d'aperçu image
        self.preview_canvas = tk.Canvas(preview_frame, bg='white', width=300, height=300)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Zone d'aperçu texte
        self.preview_text = scrolledtext.ScrolledText(preview_frame, width=40, height=15,
                                                      font=("Courier", 9))
        self.preview_text.pack(fill=tk.BOTH, expand=True)
    
    def create_report_tab(self, parent):
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="📊 Générer le rapport complet", 
                  command=self.generate_full_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Exporter le rapport", 
                  command=self.export_report).pack(side=tk.LEFT, padx=5)
        
        # Zone de rapport
        report_frame = ttk.LabelFrame(main_frame, text="Rapport de Récupération", padding="10")
        report_frame.pack(fill=tk.BOTH, expand=True)
        
        self.report_text = scrolledtext.ScrolledText(report_frame, width=120, height=35,
                                                     font=("Courier", 9))
        self.report_text.pack(fill=tk.BOTH, expand=True)
        
    def create_logs_tab(self, parent):
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        log_frame = ttk.LabelFrame(main_frame, text="Journal des Opérations", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=120, height=30,
                                                  font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        button_frame = ttk.Frame(log_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="💾 Exporter logs (TXT)", 
                  command=lambda: self.export_logs('txt')).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Exporter logs (JSON)", 
                  command=lambda: self.export_logs('json')).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Effacer", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=5)
    
    def update_log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, value, message=""):
        self.progress['value'] = value
        if message:
            self.progress_label.config(text=message)
        self.root.update_idletasks()
    
    def browse_source(self):
        """Ouvre le dialogue de sélection selon le type"""
        source_type = self.source_type.get()
        
        if source_type == "file":
            filename = filedialog.askopenfilename(
                title="Sélectionner un fichier",
                filetypes=[
                    ("Tous les fichiers", "*.*"),
                    ("Images disque", "*.img *.dd *.raw *.iso"),
                    ("Fichiers binaires", "*.bin")
                ]
            )
            if filename:
                self.source_var.set(filename)
                
        elif source_type == "folder":
            foldername = filedialog.askdirectory(title="Sélectionner un dossier")
            if foldername:
                self.source_var.set(foldername)
                
        elif source_type == "disk":
            # Afficher une liste de disques
            disks = DiskDetector.list_disks()
            if not disks:
                messagebox.showwarning("Attention", 
                    "Aucun disque détecté. Lancez l'application en tant qu'administrateur.")
                return
            # Créer une fenêtre de sélection
            disk_window = tk.Toplevel(self.root)
            disk_window.title("Sélectionner un disque")
            disk_window.geometry("400x300")
            
            ttk.Label(disk_window, text="Disques disponibles:", font=('', 10, 'bold')).pack(pady=10)
            
            listbox = tk.Listbox(disk_window, height=10)
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            for disk, info in disks:
                listbox.insert(tk.END, f"{disk} - {info}")
            
            def select_disk():
                selection = listbox.curselection()
                if selection:
                    selected = listbox.get(selection[0])
                    disk_path = selected.split(' - ')[0]
                    self.source_var.set(disk_path)
                    disk_window.destroy()
            
            ttk.Button(disk_window, text="Sélectionner", command=select_disk).pack(pady=10)
    
    def load_data(self):
        source = self.source_var.get()
        source_type = self.source_type.get()
        
        if not source:
            messagebox.showerror("Erreur", "Veuillez sélectionner une source")
            return
        
        self.source_path = source
        
        def load_thread(source, source_type):  # ← Ajouter les paramètres
            try:
                self.update_progress(0, "Chargement des données...")
                self.update_log(self.logger.log(f"Début du chargement: {source}"))
                # Cleanup previous mappings/handles
                try:
                    if getattr(self, 'current_data', None) is not None:
                        try:
                            if isinstance(self.current_data, mmap.mmap):
                                self.current_data.close()
                        except Exception:
                            pass
                        self.current_data = None
                except Exception:
                    pass
                try:
                    if getattr(self, 'current_file', None):
                        try:
                            self.current_file.close()
                        except Exception:
                            pass
                        self.current_file = None
                except Exception:
                    pass
                
                if source_type == "folder":
                    # Scanner un dossier: lire tous les fichiers
                    self.update_log(self.logger.log(f"Scan du dossier: {source}"))
                    all_data = bytearray()
                    file_count = 0
                    
                    for root, dirs, files in os.walk(source):
                        for file in files:
                            filepath = os.path.join(root, file)
                            try:
                                with open(filepath, 'rb') as f:
                                    data = f.read()
                                    all_data.extend(data)
                                    file_count += 1
                                    self.update_log(self.logger.log(f"Lu: {filepath} ({len(data)} octets)"))
                            except Exception as e:
                                self.update_log(self.logger.log(f"Erreur lecture {filepath}: {e}", "WARN"))
                    
                    self.current_data = bytes(all_data)
                    self.update_log(self.logger.log(f"Dossier scanné: {file_count} fichiers, {len(self.current_data)} octets"))
                    
                elif source_type == "disk":
                    # Lire un disque (nécessite privilèges)
                    self.update_log(self.logger.log(f"Lecture du disque: {source}"))
                    try:
                        # Sur Windows, ouvrir avec \\.\PhysicalDrive ou lettre de lecteur
                        if platform.system() == "Windows" and not source.startswith('\\\\.\\'):
                            # Convertir C:\ en \\.\C:
                            if len(source) == 3 and source[1] == ':':
                                source = f'\\\\.\\{source[0]}:'
                        
                        # Ouvrir le flux sans contexte afin de pouvoir conserver le handle
                        f = open(source, 'rb')
                        try:
                            try:
                                mm = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ)
                                # Conserver la référence au handle et à la mmap pour la durée de l'analyse
                                self.current_file = f
                                self.current_data = mm
                                self.update_log(self.logger.log(f"Disque mappé: {len(self.current_data)} octets (mmap)"))
                            except Exception:
                                # Fallback: lire une taille configurable par l'utilisateur (GB)
                                max_read_gb = max(0.1, float(self.max_read_gb.get() or 2.0))
                                max_read = int(max_read_gb * 1024 * 1024 * 1024)
                                self.current_data = f.read(max_read)
                                self.current_file = f
                                self.update_log(self.logger.log(f"Disque lu (fallback): {len(self.current_data)} octets"))
                        except Exception:
                            try:
                                f.close()
                            except:
                                pass
                            raise
                    except PermissionError:
                        messagebox.showerror("Erreur", 
                            "Accès refusé. Lancez l'application en tant qu'administrateur pour scanner un disque.")
                        return
                    
                else:  # fichier
                    with open(source, 'rb') as f:
                        self.current_data = f.read()
                    self.update_log(self.logger.log(f"Fichier lu: {len(self.current_data)} octets"))
                
                # Mise à jour de l'interface
                self.size_label.config(text=f"{len(self.current_data):,} octets ({len(self.current_data)//(1024*1024)} MB)")
                
                # Lancer toutes les analyses
                self.update_progress(20, "Analyse de l'intégrité...")
                self.analyze_integrity_silent()
                
                self.update_progress(40, "Analyse des partitions...")
                self.analyze_partitions_silent()
                
                self.update_progress(60, "Scan des signatures...")
                self.scan_files_silent()
                
                self.update_progress(80, "Génération de l'aperçu...")
                self.display_hex_preview()
                
                self.update_progress(100, "Analyse terminée!")
                
                messagebox.showinfo("Succès", 
                    f"Analyse terminée!\n\n"
                    f"Taille: {len(self.current_data):,} octets\n"
                    f"Fichiers détectés: {len(self.scan_results)}")
                
            except Exception as e:
                self.logger.log(f"Erreur: {e}", "ERROR")
                messagebox.showerror("Erreur", f"Impossible de charger: {e}")
        
        # ← Passer les variables en argument
        threading.Thread(target=load_thread, args=(source, source_type), daemon=True).start()
    
    def analyze_integrity_silent(self):
        """Analyse l'intégrité sans interaction utilisateur"""
        score = self.analyzer.estimate_recoverability(self.current_data)
        self.recovery_label.config(text=f"{score:.2f}%")
        color = "green" if score > 70 else "orange" if score > 40 else "red"
        self.recovery_label.config(foreground=color)
        self.report_data['recoverability_score'] = score
    
    def analyze_partitions_silent(self):
        """Analyse les partitions sans interaction"""
        self.partition_text.delete(1.0, tk.END)
        self.fs_text.delete(1.0, tk.END)
        
        # MBR
        mbr_info = self.partition_analyzer.detect_mbr(self.current_data)
        if mbr_info:
            self.partition_text.insert(tk.END, f"=== TABLE DE PARTITION {mbr_info['type']} ===\n\n")
            self.partition_count_label.config(text=f"{len(mbr_info['partitions'])} partitions")
            self.report_data['partitions'] = mbr_info
            
            for part in mbr_info['partitions']:
                self.partition_text.insert(tk.END, f"Partition {part['number']}:\n")
                self.partition_text.insert(tk.END, f"  Type: {part['type']} ({part['type_code']})\n")
                self.partition_text.insert(tk.END, f"  Statut: {part['status']}\n")
                self.partition_text.insert(tk.END, f"  Taille: {part['size_mb']:,} MB\n")
                self.partition_text.insert(tk.END, f"  Secteur: {part['start_sector']}\n\n")
        
        # GPT
        gpt_info = self.partition_analyzer.detect_gpt(self.current_data)
        if gpt_info:
            self.partition_text.insert(tk.END, f"\n=== TABLE GPT ===\n")
            self.partition_text.insert(tk.END, f"Partitions: {gpt_info['num_partitions']}\n")
        
        if not mbr_info and not gpt_info:
            self.partition_text.insert(tk.END, "Aucune table de partition détectée\n")
            self.partition_count_label.config(text="0")
        
        # Systèmes de fichiers
        fs_list = self.fs_analyzer.detect_filesystem(self.current_data)
        self.report_data['filesystems'] = fs_list
        
        if fs_list:
            fs_names = [fs['type'] for fs in fs_list]
            self.fs_label.config(text=", ".join(fs_names))
            
            for fs in fs_list:
                self.fs_text.insert(tk.END, f"=== {fs['type']} ===\n")
                if 'oem_name' in fs:
                    self.fs_text.insert(tk.END, f"OEM: {fs['oem_name']}\n")
                if 'volume_size_mb' in fs:
                    self.fs_text.insert(tk.END, f"Taille: {fs['volume_size_mb']:,} MB\n")
                if 'bytes_per_sector' in fs:
                    self.fs_text.insert(tk.END, f"Octets/secteur: {fs['bytes_per_sector']}\n")
                if 'sectors_per_cluster' in fs:
                    self.fs_text.insert(tk.END, f"Secteurs/cluster: {fs['sectors_per_cluster']}\n")
                self.fs_text.insert(tk.END, "\n")
        else:
            self.fs_text.insert(tk.END, "Aucun système de fichiers reconnu\n")
            self.fs_label.config(text="Inconnu")
    
    def scan_files_silent(self):
        """Scan des fichiers sans interaction"""
        self.tree.delete(*self.tree.get_children())
        
        def progress_callback(value):
            self.update_progress(60 + (value * 0.2), f"Scan: {value:.0f}%")
        
        # ← Récupérer les types sélectionnés
        selected_types = self.get_selected_file_types()
        
        if not selected_types:
            messagebox.showwarning("Attention", "Veuillez sélectionner au moins un type de fichier")
            return
        
        # ← Passer les types filtrés au scanner
        enable_filter = self.enable_filtering.get()
        self.scan_results = self.scanner.scan_signatures(
            self.current_data, 
            progress_callback, 
            enable_filter,
            selected_types=selected_types  # ← Nouveau paramètre
        )
        
        for idx, result in enumerate(self.scan_results, 1):
            # Estimer la taille
            file_data = self.carver.carve_file(self.current_data, result)
            size_str = f"{len(file_data):,} octets" if file_data else "N/A"
            result['size'] = len(file_data) if file_data else 0
            
            self.tree.insert('', tk.END, text=str(idx), values=(
                result['type'],
                f"0x{result['offset']:08X}",
                size_str
            ))
        
        self.files_count_label.config(text=str(len(self.scan_results)))
        self.report_data['recovered_files'] = self.scan_results
    
    def display_hex_preview(self, num_bytes=512):
        if not self.current_data:
            return
        
        self.hex_text.delete(1.0, tk.END)
        preview_data = self.current_data[:num_bytes]
        
        for i in range(0, len(preview_data), 16):
            chunk = preview_data[i:i+16]
            hex_part = ' '.join(f'{b:02x}' for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            self.hex_text.insert(tk.END, f"{i:08x}  {hex_part:<48}  {ascii_part}\n")
    
    def on_file_select(self, event):
        """Génère un aperçu quand un fichier est sélectionné"""
        selection = self.tree.selection()
        if not selection or not self.current_data:
            return
        
        item = selection[0]
        idx = int(self.tree.item(item)['text']) - 1
        file_info = self.scan_results[idx]
        
        def preview_thread():
            # Extraire le fichier
            file_data = self.carver.carve_file(self.current_data, file_info)
            
            if not file_data:
                return
            
            # Nettoyer l'aperçu précédent
            self.preview_canvas.delete("all")
            self.preview_text.delete(1.0, tk.END)
            
            file_type = file_info['type']
            
            # Aperçu image
            if file_type in ['PNG', 'JPEG', 'GIF', 'BMP']:
                if not PIL_AVAILABLE:
                    self.preview_text.insert(tk.END, f"Type: {file_type}\n")
                    self.preview_text.insert(tk.END, f"Taille: {len(file_data):,} octets\n\n")
                    self.preview_text.insert(tk.END, "⚠️  Pillow non installé\n\n")
                    self.preview_text.insert(tk.END, "Aperçu hexadécimal:\n")
                    preview_data = file_data[:256]
                    for i in range(0, len(preview_data), 16):
                        chunk = preview_data[i:i+16]
                        hex_part = ' '.join(f'{b:02x}' for b in chunk)
                        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                        self.preview_text.insert(tk.END, f"{i:04x}  {hex_part:<48}  {ascii_part}\n")
                else:
                    img = FilePreview.generate_image_preview(file_data)
                    if img:
                        self.current_preview = img
                        self.preview_canvas.create_image(150, 150, image=img)
                        self.preview_text.insert(tk.END, f"✅ Type: {file_type}\n")
                        self.preview_text.insert(tk.END, f"📏 Taille: {len(file_data):,} octets\n")
                        self.preview_text.insert(tk.END, f"📍 Offset: 0x{file_info['offset']:08X}\n")
                    else:
                        self.preview_text.insert(tk.END, "❌ Impossible de générer l'aperçu image\n")
            
            # Aperçu texte pour PDF
            elif file_type == 'PDF':
                preview = FilePreview.get_text_preview(file_data)
                self.preview_text.insert(tk.END, f"📄 Type: PDF\n")
                self.preview_text.insert(tk.END, f"📏 Taille: {len(file_data):,} octets\n")
                self.preview_text.insert(tk.END, f"📍 Offset: 0x{file_info['offset']:08X}\n\n")
                self.preview_text.insert(tk.END, "Aperçu du contenu:\n")
                self.preview_text.insert(tk.END, "-" * 40 + "\n")
                self.preview_text.insert(tk.END, preview)
            
            # Aperçu hexadécimal pour autres types
            else:
                self.preview_text.insert(tk.END, f"📦 Type: {file_type}\n")
                self.preview_text.insert(tk.END, f"📏 Taille: {len(file_data):,} octets\n")
                self.preview_text.insert(tk.END, f"📍 Offset: 0x{file_info['offset']:08X}\n\n")
                self.preview_text.insert(tk.END, "Aperçu hexadécimal:\n")
                
                preview_data = file_data[:256]
                for i in range(0, len(preview_data), 16):
                    chunk = preview_data[i:i+16]
                    hex_part = ' '.join(f'{b:02x}' for b in chunk)
                    ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                    self.preview_text.insert(tk.END, f"{i:04x}  {hex_part:<48}  {ascii_part}\n")
        
        threading.Thread(target=preview_thread, daemon=True).start()
    
    def extract_files(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner des fichiers à extraire")
            return
        
        output_dir = filedialog.askdirectory(title="Sélectionner le dossier de sortie")
        if not output_dir:
            return
        
        def extract_thread():
            success_count = 0
            total = len(selection)
            
            for i, item in enumerate(selection):
                idx = int(self.tree.item(item)['text']) - 1
                file_info = self.scan_results[idx]
                
                self.update_progress((i / total) * 100, f"Extraction {i+1}/{total}...")
                
                file_data = self.carver.carve_file(self.current_data, file_info)
                if file_data:
                    filepath = self.carver.save_carved_file(file_data, file_info['type'], output_dir, idx)
                    if filepath:
                        success_count += 1
                        file_info['extracted'] = True
                        file_info['filename'] = os.path.basename(filepath)
            
            self.update_progress(100, "Extraction terminée")
            self.update_log(self.logger.log(f"Extraction: {success_count}/{total} fichiers extraits"))
            messagebox.showinfo("Succès", f"{success_count} fichiers extraits vers:\n{output_dir}")
        
        threading.Thread(target=extract_thread, daemon=True).start()
    
    def extract_all(self):
        if not self.scan_results:
            messagebox.showwarning("Attention", "Aucun fichier à extraire")
            return
        
        response = messagebox.askyesno("Confirmation", 
            f"Extraire tous les {len(self.scan_results)} fichiers détectés?")
        if not response:
            return
        
        output_dir = filedialog.askdirectory(title="Sélectionner le dossier de sortie")
        if not output_dir:
            return
        
        def extract_thread():
            success_count = 0
            total = len(self.scan_results)
            
            for idx, file_info in enumerate(self.scan_results):
                self.update_progress((idx / total) * 100, f"Extraction {idx+1}/{total}...")
                
                file_data = self.carver.carve_file(self.current_data, file_info)
                if file_data:
                    filepath = self.carver.save_carved_file(file_data, file_info['type'], output_dir, idx)
                    if filepath:
                        success_count += 1
                        file_info['extracted'] = True
                        file_info['filename'] = os.path.basename(filepath)
            
            self.update_progress(100, "Extraction terminée")
            self.update_log(self.logger.log(f"Extraction complète: {success_count}/{total} fichiers"))
            messagebox.showinfo("Succès", f"{success_count} fichiers extraits vers:\n{output_dir}")
        
        threading.Thread(target=extract_thread, daemon=True).start()
    
    def generate_full_report(self):
        """Génère le rapport complet dans l'interface"""
        if not self.current_data:
            messagebox.showwarning("Attention", "Aucune donnée analysée")
            return
        
        self.report_text.delete(1.0, tk.END)
        
        # Préparer les données du rapport
        self.report_data['source'] = self.source_path
        self.report_data['total_size'] = len(self.current_data)
        
        # En-tête
        self.report_text.insert(tk.END, "=" * 80 + "\n")
        self.report_text.insert(tk.END, "RAPPORT DE RÉCUPÉRATION DE DONNÉES\n")
        self.report_text.insert(tk.END, "=" * 80 + "\n\n")
        
        self.report_text.insert(tk.END, f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.report_text.insert(tk.END, f"📁 Source: {self.source_path}\n")
        self.report_text.insert(tk.END, f"📏 Taille: {len(self.current_data):,} octets ({len(self.current_data)//(1024*1024)} MB)\n\n")
        
        # 1. Récupérabilité
        self.report_text.insert(tk.END, "-" * 80 + "\n")
        self.report_text.insert(tk.END, "1. ANALYSE DE RÉCUPÉRABILITÉ\n")
        self.report_text.insert(tk.END, "-" * 80 + "\n")
        score = self.report_data.get('recoverability_score', 0)
        self.report_text.insert(tk.END, f"Score: {score:.2f}%\n")
        if score > 70:
            self.report_text.insert(tk.END, "✅ Évaluation: EXCELLENTE - Les données sont en bon état\n")
        elif score > 40:
            self.report_text.insert(tk.END, "⚠️  Évaluation: MOYENNE - Récupération partielle possible\n")
        else:
            self.report_text.insert(tk.END, "❌ Évaluation: FAIBLE - Données fortement corrompues\n")
        self.report_text.insert(tk.END, "\n")
        
        # 2. Partitions
        self.report_text.insert(tk.END, "-" * 80 + "\n")
        self.report_text.insert(tk.END, "2. PARTITIONS DÉTECTÉES\n")
        self.report_text.insert(tk.END, "-" * 80 + "\n")
        if 'partitions' in self.report_data and self.report_data['partitions']:
            partitions = self.report_data['partitions']
            if 'partitions' in partitions and partitions['partitions']:
                for part in partitions['partitions']:
                    self.report_text.insert(tk.END, f"\n💾 Partition {part['number']}:\n")
                    self.report_text.insert(tk.END, f"   Type: {part['type']}\n")
                    self.report_text.insert(tk.END, f"   Statut: {part['status']}\n")
                    self.report_text.insert(tk.END, f"   Taille: {part['size_mb']:,} MB\n")
                    self.report_text.insert(tk.END, f"   Secteur de début: {part['start_sector']}\n")
            else:
                self.report_text.insert(tk.END, "Aucune partition détectée\n")
        else:
            self.report_text.insert(tk.END, "Aucune partition détectée\n")
        self.report_text.insert(tk.END, "\n")
        
        # 3. Systèmes de fichiers
        self.report_text.insert(tk.END, "-" * 80 + "\n")
        self.report_text.insert(tk.END, "3. SYSTÈMES DE FICHIERS\n")
        self.report_text.insert(tk.END, "-" * 80 + "\n")
        if 'filesystems' in self.report_data and self.report_data['filesystems']:
            for fs in self.report_data['filesystems']:
                self.report_text.insert(tk.END, f"\n🗂️  Type: {fs['type']}\n")
                if 'volume_size_mb' in fs:
                    self.report_text.insert(tk.END, f"   Taille: {fs['volume_size_mb']:,} MB\n")
                if 'oem_name' in fs:
                    self.report_text.insert(tk.END, f"     OEM: {fs['oem_name']}\n")
        else:
            self.report_text.insert(tk.END, "Aucun système de fichiers reconnu\n")
        self.report_text.insert(tk.END, "\n")
        
        # 4. Fichiers récupérés
        self.report_text.insert(tk.END, "-" * 80 + "\n")
        self.report_text.insert(tk.END, "4. FICHIERS DÉTECTÉS (SIGNATURE SCAN)\n")
        self.report_text.insert(tk.END, "-" * 80 + "\n")
        files = self.report_data.get('recovered_files', [])
        self.report_text.insert(tk.END, f"Total: {len(files)} fichiers détectés\n\n")
        
        # Statistiques par type
        file_types = {}
        total_size = 0
        for file_info in files:
            ftype = file_info['type']
            file_types[ftype] = file_types.get(ftype, 0) + 1
            total_size += file_info.get('size', 0)
        
        self.report_text.insert(tk.END, "📊 Répartition par type:\n")
        for ftype, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            self.report_text.insert(tk.END, f"   {ftype}: {count} fichier(s)\n")
        self.report_text.insert(tk.END, f"\n📦 Taille totale récupérable: {total_size:,} octets ({total_size//(1024*1024)} MB)\n\n")
        
        # Liste détaillée
        self.report_text.insert(tk.END, "📋 Liste détaillée:\n\n")
        for idx, file_info in enumerate(files, 1):
            status = "✅" if file_info.get('extracted') else "⏸️"
            self.report_text.insert(tk.END, f"{status} [{idx:04d}] {file_info['type']:<8} | ")
            self.report_text.insert(tk.END, f"Offset: 0x{file_info['offset']:08X} | ")
            self.report_text.insert(tk.END, f"Taille: {file_info.get('size', 0):>10,} octets")
            if file_info.get('extracted'):
                self.report_text.insert(tk.END, f" | {file_info.get('filename', 'N/A')}")
            self.report_text.insert(tk.END, "\n")
        
        self.report_text.insert(tk.END, "\n")
        self.report_text.insert(tk.END, "-" * 80 + "\n")
        self.report_text.insert(tk.END, "FIN DU RAPPORT\n")
        self.report_text.insert(tk.END, "=" * 80 + "\n")
        
        self.update_log(self.logger.log("Rapport généré"))
        messagebox.showinfo("Succès", "Rapport généré avec succès!")
    
    def export_report(self):
        """Exporte le rapport dans un fichier"""
        if not self.report_data:
            messagebox.showwarning("Attention", "Générez d'abord le rapport")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
            initialfile=f"rapport_recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            success = self.report_generator.generate_report(self.report_data, filename)
            if success:
                messagebox.showinfo("Succès", f"Rapport exporté vers:\n{filename}")
            else:
                messagebox.showerror("Erreur", "Erreur lors de l'export du rapport")
    
    def export_logs(self, format_type):
        if format_type == 'json':
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON", "*.json")],
                initialfile=f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            if filename:
                self.logger.export_json(filename)
        else:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Fichiers texte", "*.txt")],
                initialfile=f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.logger.get_logs())
        
        if filename:
            self.update_log(self.logger.log(f"Logs exportés vers {filename}"))
            messagebox.showinfo("Succès", "Logs exportés avec succès")
    
    def clear_logs(self):
        if messagebox.askyesno("Confirmation", "Effacer tous les logs?"):
            self.log_text.delete(1.0, tk.END)
            self.logger.logs.clear()
            self.update_log(self.logger.log("Logs effacés"))
