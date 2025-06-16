import os
import requests
import shutil
import subprocess
import sys
import json
import time
from tkinter import messagebox

# Configuration
GITHUB_REPO_API = "https://api.github.com/repos/pahilabs/simple-test-app/releases/latest"
GITHUB_RELEASES_URL = "https://github.com/pahilabs/simple-test-app/releases"
CURRENT_VERSION = "1.0.0"  # This should match main.py

# Backup paths
USER_HOME = os.path.expanduser("~")
BACKUP_DIR = os.path.join(USER_HOME, ".simple-test-app", "backup")
DB_BACKUP_PATH = os.path.join(BACKUP_DIR, "users.db")

def get_db_path():
    """Get the current database path"""
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(app_dir, 'data', 'users.db')

def backup_user_data():
    """Create a backup of user data"""
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        db_path = get_db_path()
        if os.path.exists(db_path):
            shutil.copy2(db_path, DB_BACKUP_PATH)
            print(f"Database backed up to {DB_BACKUP_PATH}")
            return True
        else:
            print("No database found to backup")
            return True
            
    except Exception as e:
        print(f"Backup failed: {e}")
        return False

def restore_user_data():
    """Restore user data from backup"""
    try:
        if os.path.exists(DB_BACKUP_PATH):
            db_path = get_db_path()
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            shutil.copy2(DB_BACKUP_PATH, db_path)
            print("Database restored from backup")
            return True
        else:
            print("No backup found to restore")
            return True
            
    except Exception as e:
        print(f"Restore failed: {e}")
        return False

def check_for_new_version():
    """Check GitHub for the latest release"""
    try:
        response = requests.get(GITHUB_REPO_API, timeout=5)
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get("tag_name", "").lstrip('v')
            
            if latest_version and latest_version != CURRENT_VERSION:
                print(f"New version available: {latest_version}")
                
                if messagebox.askyesno(
                    "Update Available",
                    f"A new version ({latest_version}) is available.\n"
                    f"Current version: {CURRENT_VERSION}\n\n"
                    f"Do you want to update now?"
                ):
                    update_application(latest_version, data)
            else:
                print("You are running the latest version")
        else:
            print(f"Could not check for updates: {response.status_code}")
            
    except Exception as e:
        print(f"Update check failed: {e}")

def update_application(latest_version, release_data):
    """Update the application"""
    try:
        # Backup user data
        if not backup_user_data():
            messagebox.showerror("Update Error", "Failed to backup user data")
            return
        
        # Find download URL
        assets = release_data.get("assets", [])
        download_url = None
        
        for asset in assets:
            if asset["name"].endswith(".tar.gz"):
                download_url = asset["browser_download_url"]
                break
        
        if not download_url:
            messagebox.showerror("Update Error", "No update package found")
            return
        
        # Download update
        download_path = os.path.join("/tmp", f"simple-test-app-{latest_version}.tar.gz")
        messagebox.showinfo("Update", "Downloading update...")
        
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(download_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        # Extract update
        extract_dir = "/tmp/simple-test-app-update"
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)
        
        subprocess.run(["tar", "-xzf", download_path, "-C", extract_dir], check=True)
        
        # Find and run installer
        install_script = None
        for root, dirs, files in os.walk(extract_dir):
            if "install.sh" in files:
                install_script = os.path.join(root, "install.sh")
                break
        
        if install_script:
            messagebox.showinfo("Update", "Installing update...")
            subprocess.run(["sudo", "bash", install_script], check=True)
        
        # Restore user data
        time.sleep(1)
        restore_user_data()
        
        messagebox.showinfo("Update Complete", 
                          "Update completed successfully!\n"
                          "Please restart the application.")
        sys.exit(0)
        
    except Exception as e:
        messagebox.showerror("Update Error", f"Update failed: {e}")
        print(f"Update failed: {e}")
