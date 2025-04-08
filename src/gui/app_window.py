import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk
import requests
import os
import zipfile
import subprocess
from utils.file_manager import FileManager
from utils.github_manager import GitHubManager
from config import LAUNCHER_VERSION

class AppWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("sm64coopdx Launcher")
        self.root.geometry("400x400")

        # Label principal
        self.label = tk.Label(self.root, text="Welcome to sm64coopdx Launcher!")
        self.label.pack(pady=10)

        # Drop-down list pour les versions installées
        self.version_combobox = ttk.Combobox(self.root, state="readonly")
        self.version_combobox.pack(pady=10, padx=10, fill=tk.X)

        # Bouton pour lancer une version (désactivé par défaut)
        self.launch_button = tk.Button(self.root, text="Launch Version", state=tk.DISABLED, command=self.launch_version)
        self.launch_button.pack(pady=5)

        # Bouton pour télécharger une version
        self.download_button = tk.Button(self.root, text="Download Version", command=self.download_version)
        self.download_button.pack(pady=5)

        # Bouton pour supprimer une version (désactivé par défaut)
        self.delete_button = tk.Button(self.root, text="Delete Version", state=tk.DISABLED, command=self.delete_version)
        self.delete_button.pack(pady=5)

        # Bouton pour rafraîchir la liste des versions
        self.refresh_button = tk.Button(self.root, text="Refresh Versions", command=self.refresh_versions)
        self.refresh_button.pack(pady=5)

        # Afficher la version du launcher
        self.version_label = tk.Label(self.root, text=f"Launcher Version: {LAUNCHER_VERSION}")
        self.version_label.pack(pady=5)

        # Charger les versions installées au démarrage
        self.refresh_versions()

        # Lier la sélection dans la Combobox à l'activation des boutons "Launch" et "Delete"
        self.version_combobox.bind("<<ComboboxSelected>>", self.on_version_select)

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

        # Mettre à jour la Combobox avec les versions trouvées
        if versions:
            self.version_combobox["values"] = versions
            self.version_combobox.current(0)  # Sélectionner la première version par défaut
            self.launch_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
        else:
            # Afficher un message par défaut si aucune version n'est installée
            self.version_combobox["values"] = ["No versions of sm64coopdx installed"]
            self.version_combobox.set("No versions of sm64coopdx installed")
            self.launch_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)

    def on_version_select(self, event):
        """Active les boutons 'Launch Version' et 'Delete Version' lorsqu'une version est sélectionnée."""
        if self.version_combobox.get():
            self.launch_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
        else:
            self.launch_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)

    def launch_version(self):
        """Lance la version sélectionnée en exécutant son fichier .exe."""
        selected_version = self.version_combobox.get()
        if not selected_version:
            messagebox.showerror("Error", "Please select a version to launch.")
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
        releases = GitHubManager.get_releases()
        if not releases:
            messagebox.showerror("Error", "Failed to fetch releases from GitHub.")
            return

        # Créer une nouvelle fenêtre pour afficher les releases et les fichiers ZIP
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Select a Release and File")
        selection_window.geometry("600x600")
        selection_window.minsize(600, 600)

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

        # Conteneur pour la barre de progression
        progress_frame = tk.Frame(selection_window)
        progress_frame.pack(fill=tk.X, pady=10)

        # Barre de progression (initialement cachée)
        progress_label = tk.Label(progress_frame, text="Progress: 0%")
        progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=500, mode="determinate")

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

        def download_selected_file():
            """Télécharge le fichier ZIP sélectionné avec une barre de progression."""
            if not selected_release:
                messagebox.showerror("Error", "Please select a release.")
                return

            selected_asset_index = asset_listbox.curselection()
            if not selected_asset_index:
                messagebox.showerror("Error", "Please select a file.")
                return

            # Récupérer les informations du fichier ZIP sélectionné
            selected_asset = selected_release["assets"][selected_asset_index[0]]
            download_url = selected_asset["browser_download_url"]
            file_name = selected_asset["name"]

            # Afficher la barre de progression
            progress_label.pack(pady=5)
            progress_bar.pack(pady=5)

            # Télécharger le fichier avec une barre de progression
            def perform_download():
                # Assurez-vous que le dossier 'versions' existe
                download_directory = "versions"
                if not os.path.exists(download_directory):
                    os.makedirs(download_directory)

                # Chemin complet pour le fichier téléchargé
                file_path = os.path.join(download_directory, file_name)

                response = requests.get(download_url, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0

                with open(file_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            downloaded_size += len(chunk)
                            progress = int((downloaded_size / total_size) * 100)
                            progress_bar["value"] = progress
                            progress_label.config(text=f"Progress: {progress}%")
                            selection_window.update_idletasks()

                if downloaded_size == total_size:
                    # Décompresser le fichier ZIP dans un dossier portant le même nom
                    extract_directory = os.path.join(download_directory, os.path.splitext(file_name)[0])
                    if not os.path.exists(extract_directory):
                        os.makedirs(extract_directory)

                    try:
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_directory)
                        # Supprimer le fichier ZIP après décompression
                        os.remove(file_path)
                        messagebox.showinfo("Success", f"File '{file_name}' downloaded, extracted to '{extract_directory}', and deleted!")
                    except zipfile.BadZipFile:
                        messagebox.showerror("Error", f"Failed to extract '{file_name}'. The file is not a valid ZIP archive.")
                else:
                    messagebox.showerror("Error", f"Failed to download file '{file_name}'.")

                # Fermer la fenêtre de téléchargement
                selection_window.destroy()

                # Rafraîchir la liste des versions
                self.refresh_versions()

            perform_download()

        # Lier l'événement de sélection à la mise à jour des fichiers ZIP
        release_listbox.bind("<<ListboxSelect>>", update_assets)

        # Lier l'événement de sélection des fichiers ZIP à l'activation du bouton Download
        asset_listbox.bind("<<ListboxSelect>>", enable_download_button)

        # Associer la fonction de téléchargement au bouton Download
        download_button.config(command=download_selected_file)

    def delete_version(self):
        """Supprime la version sélectionnée."""
        selected_version = self.version_combobox.get()
        if not selected_version:
            messagebox.showerror("Error", "Please select a version to delete.")
            return

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

    def run(self):
        self.root.mainloop()