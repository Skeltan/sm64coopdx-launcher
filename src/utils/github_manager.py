import requests

class GitHubManager:
    REPO_URL = "https://api.github.com/repos/coop-deluxe/sm64coopdx/releases"

    @staticmethod
    def get_releases():
        """Fetch the list of releases from the GitHub repository."""
        try:
            response = requests.get(GitHubManager.REPO_URL)
            response.raise_for_status()  # Raise an error for HTTP issues
            releases = response.json()
            return [
                {
                    "name": release["name"],
                    "assets": [
                        {
                            "name": asset["name"],
                            "browser_download_url": asset["browser_download_url"]
                        }
                        for asset in release["assets"]
                    ]
                }
                for release in releases
            ]
        except requests.RequestException as e:
            print(f"Error fetching releases: {e}")
            return []