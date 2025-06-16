#!/usr/bin/env python3
"""
Simple Test Application for Update Mechanism
A basic desktop app with user registration and update functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys
import hashlib
import threading
import traceback
from pathlib import Path

# Version information
APP_VERSION = "1.0.1"
APP_NAME = "SimpleTestApp"

class Database:
    def __init__(self):
        self.db_path = self.get_db_path()
        self.init_database()
    
    def get_db_path(self):
        """Get the database path"""
        # Use user's home directory for database storage
        home_dir = os.path.expanduser("~")
        db_dir = os.path.join(home_dir, '.simple-test-app')
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, 'users.db')
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create app_settings table for version tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    key VARCHAR(50) PRIMARY KEY,
                    value VARCHAR(255)
                )
            ''')
            
            # Insert or update version
            cursor.execute('''
                INSERT OR REPLACE INTO app_settings (key, value) 
                VALUES ('app_version', ?)
            ''', (APP_VERSION,))
            
            conn.commit()
            print(f"Database initialized at: {self.db_path}")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, password, email=""):
        """Register a new user"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, email) 
                VALUES (?, ?, ?)
            ''', (username, password_hash, email))
            
            conn.commit()
            return True, "User registered successfully!"
            
        except sqlite3.IntegrityError:
            return False, "Username already exists!"
        except sqlite3.Error as e:
            return False, f"Database error: {e}"
        finally:
            if conn:
                conn.close()
    
    def get_users(self):
        """Get all users"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # This enables column access by name
            cursor = conn.cursor()
        
            cursor.execute('SELECT username, email, created_at FROM users ORDER BY created_at DESC')
            users = cursor.fetchall()
        
            # Convert Row objects to tuples for the treeview
            result = []
            for user in users:
                result.append((user['username'], user['email'] or '', user['created_at']))
        
            print(f"Retrieved {len(result)} users from database")  # Debug print
            return result
        
        except sqlite3.Error as e:
            print(f"Database error in get_users: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_version(self):
        """Get app version from database"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT value FROM app_settings WHERE key = ?', ('app_version',))
            result = cursor.fetchone()
            return result[0] if result else APP_VERSION
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return APP_VERSION
        finally:
            if conn:
                conn.close()

class SimpleTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Initialize database
        self.db = Database()
        
        # Create GUI
        self.create_widgets()
        
        # Check for updates in background
        self.check_updates_thread()
    
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        # Add version info display
        version_info = ttk.Label(main_frame, text=f"🎉 Updated to version {APP_VERSION}!", 
                                font=('Arial', 10), foreground='green')
        version_info.grid(row=0, column=1, pady=(0, 20))
        
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text=f"{APP_NAME} v{APP_VERSION}", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Registration section
        reg_frame = ttk.LabelFrame(main_frame, text="User Registration", padding="10")
        reg_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Username
        ttk.Label(reg_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(reg_frame, textvariable=self.username_var, width=30)
        username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        
        # Password
        ttk.Label(reg_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(reg_frame, textvariable=self.password_var, 
                                 show="*", width=30)
        password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        
        # Email (optional)
        ttk.Label(reg_frame, text="Email (optional):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(reg_frame, textvariable=self.email_var, width=30)
        email_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        
        # Register button
        register_btn = ttk.Button(reg_frame, text="Register User", 
                                command=self.register_user)
        register_btn.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Users list section
        list_frame = ttk.LabelFrame(main_frame, text="Registered Users", padding="10")
        list_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Create frame for treeview and scrollbar
        tree_frame = ttk.Frame(list_frame)
        tree_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Treeview for users
        columns = ('Username', 'Email', 'Created At')
        self.users_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=8)
        
        # Configure columns
        self.users_tree.heading('Username', text='Username')
        self.users_tree.heading('Email', text='Email')
        self.users_tree.heading('Created At', text='Created At')
        
        self.users_tree.column('Username', width=120, minwidth=100)
        self.users_tree.column('Email', width=150, minwidth=120)
        self.users_tree.column('Created At', width=150, minwidth=120)
        
        self.users_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        
        # Buttons frame
        buttons_frame = ttk.Frame(list_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Refresh button
        refresh_btn = ttk.Button(buttons_frame, text="Refresh List", 
                               command=self.refresh_users)
        refresh_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Test button for debugging
        test_btn = ttk.Button(buttons_frame, text="Test Add Item", 
                            command=self.test_add_item)
        test_btn.grid(row=0, column=1, padx=(0, 10))
        
        # Clear button
        clear_btn = ttk.Button(buttons_frame, text="Clear List", 
                             command=self.clear_list)
        clear_btn.grid(row=0, column=2)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set(f"Ready - Database: {self.db.db_path}")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                             relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(2, weight=1)
        reg_frame.columnconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Load initial data
        self.refresh_users()
    
    def test_add_item(self):
        """Test function to add a dummy item to the treeview"""
        try:
            print("Testing treeview by adding dummy item...")
            item_id = self.users_tree.insert('', 'end', values=('test_user', 'test@email.com', '2025-01-01 12:00:00'))
            print(f"Added test item with ID: {item_id}")
            
            # Force GUI update
            self.root.update_idletasks()
            
            # Check if item was added
            children = self.users_tree.get_children()
            print(f"Treeview now has {len(children)} items")
            
            self.status_var.set(f"Test item added - Total items: {len(children)}")
            
        except Exception as e:
            print(f"Error in test_add_item: {e}")
            traceback.print_exc()
    
    def clear_list(self):
        """Clear all items from the treeview"""
        try:
            print("Clearing treeview...")
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            
            children = self.users_tree.get_children()
            print(f"Treeview cleared - Items remaining: {len(children)}")
            self.status_var.set("List cleared")
            
        except Exception as e:
            print(f"Error clearing list: {e}")
            traceback.print_exc()
    
    def register_user(self):
        """Register a new user"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        email = self.email_var.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required!")
            return
        
        success, message = self.db.register_user(username, password, email)
        
        if success:
            messagebox.showinfo("Success", message)
            print(f"User {username} registered successfully")  # Debug print
            # Clear form
            self.username_var.set("")
            self.password_var.set("")
            self.email_var.set("")
            # Refresh users list
            self.refresh_users()
        else:
            messagebox.showerror("Error", message)
    
    def refresh_users(self):
        """Refresh the users list"""
        try:
            print("=== Starting refresh_users ===")
            
            # Clear existing items
            print("Clearing existing items...")
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            
            print(f"Items after clearing: {len(self.users_tree.get_children())}")
        
            # Load users from database
            print("Loading users from database...")
            users = self.db.get_users()
            print(f"Retrieved {len(users)} users from database")
        
            # Add each user to the treeview
            for i, user in enumerate(users):
                print(f"Adding user {i+1}: {user}")
                try:
                    item_id = self.users_tree.insert('', 'end', values=user)
                    print(f"  -> Added with item_id: {item_id}")
                except Exception as e:
                    print(f"  -> Error adding user: {e}")
            
            # Force GUI update
            print("Forcing GUI update...")
            self.root.update_idletasks()
            self.users_tree.update_idletasks()
            
            # Verify items were added
            final_count = len(self.users_tree.get_children())
            print(f"Final treeview item count: {final_count}")
        
            self.status_var.set(f"Ready - {len(users)} users registered (showing {final_count})")
            print("=== Finished refresh_users ===")
        
        except Exception as e:
            print(f"Error refreshing users: {e}")
            traceback.print_exc()
            self.status_var.set(f"Error refreshing users: {e}")
    
    def check_updates_thread(self):
        """Check for updates in a separate thread"""
        def check_updates():
            try:
                from update_utils import check_for_new_version
                check_for_new_version()
            except ImportError:
                print("Update utils not available")
            except Exception as e:
                print(f"Update check failed: {e}")
        
        # Start update check in background after 2 seconds
        self.root.after(2000, lambda: threading.Thread(target=check_updates, daemon=True).start())

def main():
    """Main function"""
    root = tk.Tk()
    app = SimpleTestApp(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application interrupted")
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Error", f"Application error: {e}")

if __name__ == "__main__":
    main()
