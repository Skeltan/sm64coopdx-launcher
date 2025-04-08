import requests
import os

class FileManager:
    @staticmethod
    def list_versions(directory="versions"):  # Définit "versions" comme répertoire par défaut
        """List all versions in the given directory."""
        if not os.path.exists(directory):
            return []
        return [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]

    @staticmethod
    def delete_version(directory="versions", version_name=""):
        """Delete a specific version."""
        version_path = os.path.join(directory, version_name)
        if os.path.exists(version_path):
            os.rmdir(version_path)
            return True
        return False

    @staticmethod
    def download_version(download_url, version_name, directory="versions"):
        """Download a version from the given URL and save it in the directory."""
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)

            response = requests.get(download_url, stream=True)
            response.raise_for_status()  # Raise an error for HTTP issues

            version_path = os.path.join(directory, version_name)
            with open(version_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            return True
        except requests.RequestException as e:
            print(f"Error downloading version: {e}")
            return False