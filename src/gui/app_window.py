import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import zipfile
import requests
from utils.github_manager import GitHubManager
from config import LAUNCHER_VERSION
from PIL import Image, ImageTk
import sys

def get_resource_path(relative_path):
    """Retourne le chemin absolu d'une ressource, que l'application soit exécutée depuis un exécutable ou le code source."""
    if hasattr(sys, '_MEIPASS'):
        # Si l'application est exécutée depuis un exécutable PyInstaller
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(relative_path)

class AppWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("sm64coopdx Launcher")
        self.root.geometry("800x600")
        self.root.minsize(600, 600)

        # Création du Notebook pour les onglets
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Onglet "Launch Game"
        self.launch_tab = tk.Frame(notebook)
        notebook.add(self.launch_tab, text="Launch Game")

        # Onglet "Manage Builds"
        self.manage_tab = tk.Frame(notebook)
        notebook.add(self.manage_tab, text="Manage Builds")

        # Onglet "About"
        self.about_tab = tk.Frame(notebook)
        notebook.add(self.about_tab, text="About")

        # Contenu de l'onglet "Launch Game"
        self.setup_launch_tab()

        # Contenu de l'onglet "Manage Builds"
        self.setup_manage_tab()

        # Contenu de l'onglet "Manage Builds"
        self.setup_about_tab()

        # Charger les versions installées au démarrage
        self.refresh_versions()

    def setup_launch_tab(self):
        """Configure l'onglet pour lancer le jeu."""
        # Label principal
        label = tk.Label(self.launch_tab, text="Welcome to sm64coopdx Launcher!", font=("Arial", 16))
        label.pack(pady=20)

        # Déterminer le chemin du logo
        logo_path = get_resource_path(os.path.join("src", "res", "img", "logo.png"))

        # Charger et redimensionner le logo avec Pillow
        if os.path.exists(logo_path):
            try:
                pil_image = Image.open(logo_path)
                resized_image = pil_image.resize((512, 256), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(resized_image)
                logo_label = tk.Label(self.launch_tab, image=self.logo_image)
                logo_label.pack(pady=10)
            except Exception as e:
                print(f"Error loading logo: {e}")
                messagebox.showerror("Error", f"Failed to load the logo image.\nDetails: {e}")
        else:
            messagebox.showerror("Error", f"Logo file not found: {logo_path}")

        # Conteneur pour les widgets en bas
        bottom_frame = tk.Frame(self.launch_tab)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # Label pour indiquer "Version:" au-dessus de la combobox
        version_label_text = tk.Label(bottom_frame, text="Build:", font=("Arial", 10))
        version_label_text.pack(side=tk.LEFT, padx=(10,0))

        # Drop-down list pour les versions installées (en bas à gauche)
        self.version_combobox = ttk.Combobox(bottom_frame, state="readonly", width=30)
        self.version_combobox.pack(side=tk.LEFT, padx=(2, 50), fill=tk.X, expand=True)

        # Conteneur pour le bouton Launch (centré)
        launch_frame = tk.Frame(self.launch_tab)
        launch_frame.pack(side=tk.BOTTOM, pady=10)

        # Bouton pour lancer une version (centré)
        self.launch_button = tk.Button(launch_frame, text="Launch", state=tk.DISABLED, font=("Arial", 12), width=15, command=self.launch_version)
        self.launch_button.pack(anchor="center")

        # Afficher la version du launcher (en bas à droite)
        self.version_label = tk.Label(bottom_frame, text=f"v{LAUNCHER_VERSION}", font=("Arial", 10))
        self.version_label.pack(side=tk.RIGHT, padx=10)

        # Lier la sélection dans la Combobox à l'activation du bouton "Launch"
        self.version_combobox.bind("<<ComboboxSelected>>", self.on_version_select)

    def setup_manage_tab(self):
        """Configure l'onglet pour gérer les versions."""
        # Conteneur principal
        top_frame = tk.Frame(self.manage_tab)
        top_frame.pack(fill=tk.X, pady=5)

        # Label "Builds"
        versions_label = tk.Label(top_frame, text="Builds:", font=("Arial", 14))
        versions_label.pack(side=tk.LEFT, padx=(20,0))

        # Zone de filtre avec un hint
        filter_entry = tk.Entry(top_frame, width=30, fg="grey")
        filter_entry.pack(side=tk.LEFT, padx=5)
        filter_entry.insert(0, "Filter by name...")

        def on_focus_in(event):
            """Supprime le hint lorsque l'utilisateur clique dans la zone de texte."""
            if filter_entry.get() == "Filter by name...":
                filter_entry.delete(0, tk.END)
                filter_entry.config(fg="black")

        def on_focus_out(event):
            """Réaffiche le hint si la zone de texte est vide lorsque l'utilisateur clique ailleurs."""
            if not filter_entry.get():
                filter_entry.insert(0, "Filter by name...")
                filter_entry.config(fg="grey")

        # Lier les événements focus
        filter_entry.bind("<FocusIn>", on_focus_in)
        filter_entry.bind("<FocusOut>", on_focus_out)

        # Boutons
        rename_button = tk.Button(top_frame, text="Rename", state=tk.DISABLED, command=self.rename_version)
        rename_button.pack(side=tk.LEFT, padx=5)

        delete_button = tk.Button(top_frame, text="Delete", state=tk.DISABLED, command=self.delete_version)
        delete_button.pack(side=tk.LEFT, padx=5)

        # Bouton Refresh
        refresh_button = tk.Button(top_frame, text="Refresh", command=self.refresh_versions)
        refresh_button.pack(side=tk.LEFT, padx=5)

        # Bouton Install New (collé à droite)
        install_button = tk.Button(top_frame, text="Install New", command=self.download_version)
        install_button.pack(side=tk.RIGHT, padx=(5,20))

        # Conteneur pour le tableau avec padding
        table_frame = tk.Frame(self.manage_tab)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)  # Ajout de padding (20px)

        # Tableau pour afficher les versions
        columns = ("folder_name", "game_version", "renderer")
        self.version_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        self.version_table.heading("folder_name", text="Folder Name")
        self.version_table.heading("game_version", text="Game Version")
        self.version_table.heading("renderer", text="Renderer")
        self.version_table.column("folder_name", width=200)
        self.version_table.column("game_version", width=100)
        self.version_table.column("renderer", width=100)
        self.version_table.pack(fill=tk.BOTH, expand=True)

        # Lier la sélection dans le tableau à l'activation des boutons
        self.version_table.bind("<<TreeviewSelect>>", lambda e: self.on_version_table_select(rename_button, delete_button, open_folder_button))

        # Conteneur pour les boutons sous le tableau
        bottom_frame = tk.Frame(self.manage_tab)
        bottom_frame.pack(fill=tk.X, pady=(0,10))

        # Bouton "Open Version Folder"
        open_folder_button = tk.Button(bottom_frame, text="Open Version Folder", state=tk.DISABLED, command=self.open_version_folder)
        open_folder_button.pack(side=tk.LEFT, padx=20)

        # Activer le bouton "Open Version Folder" lorsqu'une version est sélectionnée
        self.version_table.bind("<<TreeviewSelect>>", lambda e: self.on_version_table_select(rename_button, delete_button, open_folder_button))

    def setup_about_tab(self):
        """Configure l'onglet 'About'."""
        about_label = tk.Label(self.about_tab, text="About sm64coopdx Launcher", font=("Arial", 16))
        about_label.pack(pady=20)

        # Afficher une description du launcher
        description_label = tk.Label(self.about_tab, text="This launcher helps you manage and launch sm64coopdx versions.", font=("Arial", 12))
        description_label.pack(pady=10)

        # Ajouter un label "Official Links"
        links_label = tk.Label(
            self.about_tab,
            text="Official Links:",
            font=("Arial", 14, "bold")
        )
        links_label.pack(pady=10)

        # Ajouter un lien vers le site officiel
        site_link_label = tk.Label(
            self.about_tab,
            text="Website: sm64coopdx.com",
            font=("Arial", 12),
            fg="blue",
            cursor="hand2"
        )
        site_link_label.pack(pady=5)
        site_link_label.bind("<Button-1>", lambda e: os.system("start https://sm64coopdx.com/"))

        # Ajouter un lien vers le Discord
        discord_link_label = tk.Label(
            self.about_tab,
            text="Discord: Join the community",
            font=("Arial", 12),
            fg="blue",
            cursor="hand2"
        )
        discord_link_label.pack(pady=5)
        discord_link_label.bind("<Button-1>", lambda e: os.system("start https://discord.gg/TJVKHS4"))

        # Ajouter un lien vers le GitHub
        github_link_label = tk.Label(
            self.about_tab,
            text="GitHub: sm64coopdx repository",
            font=("Arial", 12),
            fg="blue",
            cursor="hand2"
        )
        github_link_label.pack(pady=5)
        github_link_label.bind("<Button-1>", lambda e: os.system("start https://github.com/coop-deluxe/sm64coopdx"))

        # Afficher l'auteur du launcher
        author_label = tk.Label(self.about_tab, text=f"Launcher Author: Skeltan", font=("Arial", 12))
        author_label.pack(pady=(20, 0))

        # Afficher la version du launcher
        version_label = tk.Label(self.about_tab, text=f"Launcher Version: {LAUNCHER_VERSION}", font=("Arial", 12))
        version_label.pack(pady=0)

    def refresh_versions(self):
        """Met à jour la liste des versions installées."""
        versions_directory = "versions"

        if not os.path.exists(versions_directory):
            os.makedirs(versions_directory)

        # Effacer le tableau actuel
        for row in self.version_table.get_children():
            self.version_table.delete(row)

        # Effacer les éléments de la combobox
        self.version_combobox["values"] = []

        # Parcourir les sous-dossiers dans "versions"
        versions = []
        for version in os.listdir(versions_directory):
            version_path = os.path.join(versions_directory, version)
            if os.path.isdir(version_path):
                # Lire les variables depuis "variables.txt"
                variables_file_path = os.path.join(version_path, "launcher_variables")
                game_version = "Unknown"
                renderer = "Unknown"
                if os.path.exists(variables_file_path):
                    with open(variables_file_path, "r") as variables_file:
                        for line in variables_file:
                            key, value = line.strip().split("=", 1)
                            if key == "game_version":
                                game_version = value
                            elif key == "renderer":
                                renderer = value

                # Ajouter la version au tableau
                self.version_table.insert("", "end", values=(version, game_version, renderer))

                # Ajouter la version à la liste des versions
                versions.append(version)

        # Mettre à jour la combobox avec les versions disponibles
        if versions:
            self.version_combobox["values"] = versions
            self.version_combobox.set(versions[0])  # Sélectionner la première version par défaut
        else:
            self.version_combobox.set("No versions of sm64coopdx installed")

    def on_version_select(self, event):
        """Handles enabling/disabling buttons based on version selection."""
        selected_version = self.version_combobox.get()
        if selected_version and selected_version != "No versions of sm64coopdx installed":
            self.launch_button.config(state=tk.NORMAL)
        else:
            self.launch_button.config(state=tk.DISABLED)

    def on_version_table_select(self, rename_button, delete_button, open_folder_button):
        """Active les boutons Rename, Delete et Open Folder lorsqu'une version est sélectionnée."""
        selected_items = self.version_table.selection()
        if selected_items:
            rename_button.config(state=tk.NORMAL)
            delete_button.config(state=tk.NORMAL)
            open_folder_button.config(state=tk.NORMAL)
        else:
            rename_button.config(state=tk.DISABLED)
            delete_button.config(state=tk.DISABLED)
            open_folder_button.config(state=tk.DISABLED)

    def launch_version(self):
        """Lance la version sélectionnée en exécutant son fichier .exe."""
        selected_version = self.version_combobox.get()
        if not selected_version or selected_version == "No versions of sm64coopdx installed":
            messagebox.showerror("Error", "Please select a valid version to launch.")
            return

        # Utiliser le nom fixe "sm64coopdx.exe"
        exe_path = os.path.join("versions", selected_version, "sm64coopdx.exe")

        if os.path.exists(exe_path):
            try:
                subprocess.Popen([exe_path], shell=True)  # Lancer l'exécutable
                messagebox.showinfo("Success", f"Launching '{selected_version}'...")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch '{selected_version}'.\n{e}")
        else:
            messagebox.showerror("Error", f"Executable not found for version '{selected_version}'.")

    def download_version(self):
        """Ouvre une fenêtre pour télécharger une nouvelle version."""
        # Récupérer les versions disponibles depuis GitHub
        releases = GitHubManager.get_releases()
        if not releases:
            messagebox.showerror("Error", "Failed to fetch releases from GitHub.")
            return

        # Créer une nouvelle fenêtre pour afficher les releases et les fichiers ZIP
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Install New Version")
        selection_window.geometry("450x400")
        selection_window.minsize(450, 400)

        # Conteneur principal pour les listes
        list_frame = tk.Frame(selection_window)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Section pour les releases
        tk.Label(list_frame, text="Select a Release:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        release_listbox = tk.Listbox(list_frame, height=15)
        release_listbox.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Section pour les fichiers ZIP
        tk.Label(list_frame, text="Select a File:").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        asset_listbox = tk.Listbox(list_frame, height=15)
        asset_listbox.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        # Configurer les colonnes pour qu'elles s'étendent
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_columnconfigure(1, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)

        # Ajouter les releases à la Listbox
        for release in releases:
            release_listbox.insert(tk.END, release["name"])

        # Conteneur pour le champ de saisie et la barre de progression
        progress_frame = tk.Frame(selection_window)
        progress_frame.pack(fill=tk.X, pady=10)

        # Champ de saisie pour le nom du fichier
        tk.Label(progress_frame, text="Custom Name:").pack(side=tk.LEFT, padx=5)
        version_name_entry = tk.Entry(progress_frame)
        version_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Barre de progression
        progress_label = tk.Label(progress_frame, text="Progress: 0%")
        progress_label.pack(side=tk.LEFT, padx=5)
        progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=300, mode="determinate")
        progress_bar.pack(fill=tk.X, expand=True, padx=5)

        # Bouton pour télécharger le fichier sélectionné (désactivé par défaut)
        download_button = tk.Button(selection_window, text="Download", state=tk.DISABLED)
        download_button.pack(pady=10)

        # Variable pour stocker la release sélectionnée
        selected_release = None

        def update_assets(event):
            """Met à jour la liste des fichiers ZIP en fonction de la release sélectionnée."""
            nonlocal selected_release
            selected_index = release_listbox.curselection()
            if not selected_index:
                return  # Ne rien faire si aucune release n'est sélectionnée

            # Récupérer les fichiers ZIP pour la release sélectionnée
            selected_release = releases[selected_index[0]]
            assets = selected_release.get("assets", [])

            # Effacer la liste actuelle et ajouter les nouveaux fichiers ZIP contenant "Windows"
            asset_listbox.delete(0, tk.END)
            filtered_assets = [asset for asset in assets if "windows" in asset["name"].lower()]
            for asset in filtered_assets:
                asset_listbox.insert(tk.END, asset["name"])

            # Désactiver le bouton Download tant qu'aucun fichier ZIP n'est sélectionné
            download_button.config(state=tk.DISABLED)

        def enable_download_button(event):
            """Active le bouton Download lorsqu'un fichier ZIP est sélectionné."""
            if asset_listbox.curselection():
                download_button.config(state=tk.NORMAL)
            else:
                download_button.config(state=tk.DISABLED)

        def download_selected_asset():
            """Télécharge et installe l'asset sélectionné."""
            selected_asset_index = asset_listbox.curselection()
            if not selected_release or not selected_asset_index:
                messagebox.showerror("Error", "Please select a release and a file to download.")
                return

            # Récupérer l'asset sélectionné dans la liste filtrée
            filtered_assets = [asset for asset in selected_release["assets"] if "windows" in asset["name"].lower()]
            selected_asset = filtered_assets[selected_asset_index[0]]
            download_url = selected_asset["browser_download_url"]
            file_name = selected_asset["name"]

            # Extraire la version du jeu et le renderer à partir du nom de l'asset
            game_version = "Unknown"
            renderer = "Unknown"
            if "_v" in file_name:
                try:
                    # Extraire la version
                    version_part = file_name.split("_v")[1]
                    game_version = version_part.split("_")[0]  # Prendre la partie avant le prochain "_"

                    # Extraire le renderer (par exemple, "OpenGL" ou "DirectX")
                    renderer = file_name.split("_")[-1].split(".")[0]  # Prendre la dernière partie avant l'extension
                except IndexError:
                    pass

            # Récupérer le nom personnalisé de la version
            custom_name = version_name_entry.get().strip()
            if not custom_name:
                custom_name = os.path.splitext(file_name)[0]  # Utiliser le nom par défaut si aucun nom n'est fourni

            # Assurez-vous que le dossier 'versions' existe
            versions_directory = "versions"
            if not os.path.exists(versions_directory):
                os.makedirs(versions_directory)

            # Chemin complet pour le fichier téléchargé
            file_path = os.path.join(versions_directory, file_name)
            extract_directory = os.path.join(versions_directory, custom_name)

            try:
                # Télécharger le fichier avec une barre de progression
                response = requests.get(download_url, stream=True)
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                downloaded_size = 0

                with open(file_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        progress = int((downloaded_size / total_size) * 100)
                        progress_bar["value"] = progress
                        progress_label.config(text=f"Progress: {progress}%")
                        selection_window.update_idletasks()

                # Décompresser le fichier ZIP
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(extract_directory)

                # Écrire les variables dans un fichier texte
                variables_file_path = os.path.join(extract_directory, "launcher_variables")
                with open(variables_file_path, "w") as variables_file:
                    variables_file.write(f"game_version={game_version}\n")
                    variables_file.write(f"renderer={renderer}\n")

                # Supprimer le fichier ZIP après extraction
                os.remove(file_path)

                messagebox.showinfo("Success", f"Version '{custom_name}' has been installed.")
                self.refresh_versions()  # Rafraîchir la liste des versions
                selection_window.destroy()  # Fermer la fenêtre de sélection
            except Exception as e:
                messagebox.showerror("Error", f"Failed to download or install the version.\n{e}")

        # Lier les événements
        release_listbox.bind("<<ListboxSelect>>", update_assets)
        asset_listbox.bind("<<ListboxSelect>>", enable_download_button)
        download_button.config(command=download_selected_asset)

    def delete_version(self):
        """Supprime la version sélectionnée."""
        selected_items = self.version_table.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select a valid version to delete.")
            return

        # Récupérer le nom du dossier de la version sélectionnée
        selected_version = self.version_table.item(selected_items[0], "values")[0]

        # Chemin du dossier de la version
        version_path = os.path.join("versions", selected_version)

        if os.path.exists(version_path):
            # Demander confirmation avant de supprimer
            if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete version '{selected_version}'?"):
                try:
                    # Supprimer le dossier et son contenu
                    import shutil
                    shutil.rmtree(version_path)
                    messagebox.showinfo("Success", f"Version '{selected_version}' has been deleted.")
                    # Rafraîchir la liste des versions
                    self.refresh_versions()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete version '{selected_version}'.\n{e}")
        else:
            messagebox.showerror("Error", f"Version '{selected_version}' not found.")

    def rename_version(self):
        """Renomme la version sélectionnée."""
        selected_items = self.version_table.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select a version to rename.")
            return

        # Récupérer le nom du dossier de la version sélectionnée
        selected_version = self.version_table.item(selected_items[0], "values")[0]

        # Fenêtre pour saisir le nouveau nom
        rename_window = tk.Toplevel(self.root)
        rename_window.title("Rename Version")
        rename_window.geometry("300x150")

        tk.Label(rename_window, text=f"Renaming: {selected_version}").pack(pady=10)
        tk.Label(rename_window, text="New Name:").pack(pady=5)

        new_name_entry = tk.Entry(rename_window, width=30)
        new_name_entry.pack(pady=5)

        def confirm_rename():
            new_name = new_name_entry.get().strip()
            if not new_name:
                messagebox.showerror("Error", "New name cannot be empty.")
                return

            # Chemin actuel et nouveau chemin
            current_path = os.path.join("versions", selected_version)
            new_path = os.path.join("versions", new_name)

            if os.path.exists(new_path):
                messagebox.showerror("Error", f"A version with the name '{new_name}' already exists.")
                return

            try:
                os.rename(current_path, new_path)
                messagebox.showinfo("Success", f"Version '{selected_version}' has been renamed to '{new_name}'.")
                self.refresh_versions()  # Rafraîchir la liste des versions
                rename_window.destroy()  # Fermer la fenêtre
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename version.\n{e}")

        tk.Button(rename_window, text="Rename", command=confirm_rename).pack(pady=10)

    def open_version_folder(self):
        """Ouvre le dossier de la version sélectionnée dans l'explorateur de fichiers."""
        selected_items = self.version_table.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select a version to open its folder.")
            return

        # Récupérer le nom du dossier de la version sélectionnée
        selected_version = self.version_table.item(selected_items[0], "values")[0]

        # Chemin du dossier de la version
        version_path = os.path.join("versions", selected_version)

        if os.path.exists(version_path):
            try:
                os.startfile(version_path)  # Ouvrir le dossier dans l'explorateur de fichiers
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open folder for version '{selected_version}'.\n{e}")
        else:
            messagebox.showerror("Error", f"Folder not found for version '{selected_version}'.")

    def run(self):
        self.root.mainloop()