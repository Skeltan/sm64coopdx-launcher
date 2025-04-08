import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import zipfile
import requests
from utils.github_manager import GitHubManager
from config import LAUNCHER_VERSION
from PIL import Image, ImageTk

class AppWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("sm64coopdx Launcher")
        self.root.geometry("800x600")
        self.root.minsize(450, 400)

        # Création du Notebook pour les onglets
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Onglet "Launch Game"
        self.launch_tab = tk.Frame(notebook)
        notebook.add(self.launch_tab, text="Launch Game")

        # Onglet "Manage Versions"
        self.manage_tab = tk.Frame(notebook)
        notebook.add(self.manage_tab, text="Manage Versions")

        # Contenu de l'onglet "Launch Game"
        self.setup_launch_tab()

        # Contenu de l'onglet "Manage Versions"
        self.setup_manage_tab()

        # Charger les versions installées au démarrage
        self.refresh_versions()

    def setup_launch_tab(self):
        """Configure l'onglet pour lancer le jeu."""
        # Label principal
        label = tk.Label(self.launch_tab, text="Welcome to sm64coopdx Launcher!", font=("Arial", 16))
        label.pack(pady=20)

        # Charger et redimensionner le logo avec Pillow
        logo_path = os.path.join("res", "img", "logo.png")
        if os.path.exists(logo_path):
            try:
                pil_image = Image.open(logo_path)  # Charger l'image avec Pillow
                resized_image = pil_image.resize((512, 256), Image.Resampling.LANCZOS)  # Redimensionner l'image (150x150 pixels)
                self.logo_image = ImageTk.PhotoImage(resized_image)  # Convertir pour Tkinter
                logo_label = tk.Label(self.launch_tab, image=self.logo_image)
                logo_label.pack(pady=10)  # Placer le logo sous le texte "Welcome"
            except Exception as e:
                print(f"Error loading logo: {e}")
                messagebox.showerror("Error", f"Failed to load the logo image.\nDetails: {e}")
        else:
            messagebox.showerror("Error", f"Logo file not found: {logo_path}")

        # Conteneur pour les widgets en bas
        bottom_frame = tk.Frame(self.launch_tab)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # Label pour indiquer "Version:" au-dessus de la combobox
        version_label_text = tk.Label(bottom_frame, text="Version:", font=("Arial", 10))
        version_label_text.pack(side=tk.LEFT, padx=10)

        # Drop-down list pour les versions installées (en bas à gauche)
        self.version_combobox = ttk.Combobox(bottom_frame, state="readonly", width=30)
        self.version_combobox.pack(side=tk.LEFT, padx=10)

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
        # Liste des versions installées
        self.version_listbox = tk.Listbox(self.manage_tab, height=10, width=50)
        self.version_listbox.pack(pady=10, padx=10)

        # Bouton pour installer une nouvelle version
        self.install_button = tk.Button(self.manage_tab, text="Install New Version", command=self.download_version)
        self.install_button.pack(pady=5)

        # Bouton pour supprimer une version (désactivé par défaut)
        self.delete_button = tk.Button(self.manage_tab, text="Delete Version", state=tk.DISABLED, command=self.delete_version)
        self.delete_button.pack(pady=5)

        # Bouton pour renommer une version (désactivé par défaut)
        self.rename_button = tk.Button(self.manage_tab, text="Rename Version", state=tk.DISABLED, command=self.rename_version)
        self.rename_button.pack(pady=5)

        # Bouton pour rafraîchir la liste des versions
        self.refresh_button = tk.Button(self.manage_tab, text="Refresh Versions", command=self.refresh_versions)
        self.refresh_button.pack(pady=5)

        # Lier la sélection dans la Listbox à l'activation des boutons "Delete" et "Rename"
        self.version_listbox.bind("<<ListboxSelect>>", self.on_version_list_select)

    def refresh_versions(self):
        """Met à jour la liste des versions installées."""
        versions_directory = "versions"

        if not os.path.exists(versions_directory):
            os.makedirs(versions_directory)

        # Parcourir les sous-dossiers dans "versions"
        versions = []
        for version in os.listdir(versions_directory):
            version_path = os.path.join(versions_directory, version)
            if os.path.isdir(version_path):
                exe_file = os.path.join(version_path, "sm64coopdx.exe")  # Nom fixe du fichier .exe
                if os.path.exists(exe_file):  # Vérifier si le fichier .exe existe
                    versions.append(version)

        # Mettre à jour la Listbox avec les versions trouvées
        self.version_listbox.delete(0, tk.END)  # Effacer la liste actuelle
        if versions:
            for version in versions:
                self.version_listbox.insert(tk.END, version)
            self.delete_button.config(state=tk.NORMAL)
        else:
            self.version_listbox.insert(tk.END, "No versions installed")
            self.delete_button.config(state=tk.DISABLED)

        # Mettre à jour la Combobox dans l'onglet "Launch Game"
        self.version_combobox["values"] = versions if versions else ["No versions installed"]
        if versions:
            self.version_combobox.current(0)
            self.launch_button.config(state=tk.NORMAL)
        else:
            self.version_combobox.set("No versions installed")
            self.launch_button.config(state=tk.DISABLED)

    def on_version_select(self, event):
        """Active les boutons 'Launch Version' et 'Delete Version' lorsqu'une version est sélectionnée."""
        if self.version_combobox.get() and self.version_combobox.get() != "No versions of sm64coopdx installed":
            self.launch_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
        else:
            self.launch_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)

    def on_version_list_select(self, event):
        """Active les boutons 'Delete Version' et 'Rename Version' lorsqu'une version est sélectionnée dans la Listbox."""
        selected_indices = self.version_listbox.curselection()
        if selected_indices:
            self.delete_button.config(state=tk.NORMAL)
            self.rename_button.config(state=tk.NORMAL)
        else:
            self.delete_button.config(state=tk.DISABLED)
            self.rename_button.config(state=tk.DISABLED)

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

            # Effacer la liste actuelle et ajouter les nouveaux fichiers ZIP
            asset_listbox.delete(0, tk.END)
            for asset in assets:
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

            selected_asset = selected_release["assets"][selected_asset_index[0]]
            download_url = selected_asset["browser_download_url"]
            file_name = selected_asset["name"]

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
        selected_indices = self.version_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select a valid version to delete.")
            return

        selected_version = self.version_listbox.get(selected_indices[0])

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
        selected_indices = self.version_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select a version to rename.")
            return

        selected_version = self.version_listbox.get(selected_indices[0])

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

    def run(self):
        self.root.mainloop()