import os
import sys
import subprocess
import shutil
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
import json
import zipfile
import py7zr
import rarfile
import tempfile 

# Persistent file paths
APPDATA_FOLDER = os.path.join(os.getenv("LOCALAPPDATA"), "MarvelRivalsModManager")
CONFIG_FILE = os.path.join(APPDATA_FOLDER, "config.json")
BACKUP_FOLDER = os.path.join(
    os.getenv("LOCALAPPDATA"), "MarvelRivalsModManager", "backup"
)

# Ensure AppData folder exists
os.makedirs(APPDATA_FOLDER, exist_ok=True)

def create_popup(parent, title, size="300x150", resizable=False, icon_path=None):
    """Create a generic popup window."""
    popup = tk.Toplevel(parent)
    popup.title(title)
    popup.geometry(size)
    if not resizable:
        popup.resizable(False, False)
    if icon_path and os.path.exists(icon_path):
        popup.iconbitmap(icon_path)
    return popup

# Helper Functions
def save_config(game_dir, dark_theme, current_profile):
    config = {
        "game_dir": game_dir,
        "dark_theme": dark_theme,
        "current_profile": current_profile,
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def load_config():
    """Load configuration from the config.json file."""
    config_path = os.path.join(
        os.getenv("LOCALAPPDATA"), "MarvelRivalsModManager", "config.json"
    )
    if not os.path.exists(config_path):
        return None, False, None  # Default values if config doesn't exist

    try:
        with open(config_path, "r") as config_file:
            config_data = json.load(config_file)

        # Validate current_profile against existing profiles
        profiles_folder = os.path.join(
            os.getenv("LOCALAPPDATA"), "MarvelRivalsModManager", "profiles"
        )
        current_profile = config_data.get("current_profile")
        if current_profile:
            profile_path = os.path.join(profiles_folder, current_profile)
            if not os.path.exists(profile_path):
                current_profile = None  # Reset if profile folder doesn't exist

        return (
            config_data.get("game_dir"),
            config_data.get("dark_theme", False),
            current_profile,
        )
    except Exception:
        return None, False, None  # Default values in case of error


def verify_game_folder(folder):
    return os.path.isfile(os.path.join(folder, "MarvelRivals_Launcher.exe"))

def list_paks(directory):
    mods_folder = os.path.join(directory, "MarvelGame", "Marvel", "Content", "Paks", "Mods")
    if os.path.exists(mods_folder):
        return [f for f in os.listdir(mods_folder) if f.endswith(".pak")]
    return []

def extract_archive(archive_path, extract_to):
    try:
        if archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as archive:
                app._extract_and_add_paks(archive, archive_path)
        elif archive_path.endswith(".7z"):
            with py7zr.SevenZipFile(archive_path, "r") as archive:
                app._extract_and_add_paks(archive, archive_path)
        elif archive_path.endswith(".rar"):
            with rarfile.RarFile(archive_path, "r") as archive:
                app._extract_and_add_paks(archive, archive_path)
        else:
            messagebox.showerror("Error", "Unsupported archive format.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to extract archive: {e}")
        
       
class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.title("Settings")
        self.app = app
        self.geometry("300x150")
        self.resizable(False, False)
        self.transient(parent)

        self.dark_theme_var = tk.BooleanVar(value=self.app.dark_theme)

        tk.Label(self, text="Game Directory:").pack(pady=(10, 0))
        tk.Label(self, text=self.app.selected_folder).pack()

        tk.Checkbutton(self, text="Dark Theme", variable=self.dark_theme_var, command=self.toggle_dark_theme).pack(pady=10)

        tk.Button(self, text="Change Game Directory", command=self.app.show_folder_selector).pack()
        
class ModManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Marvel Rivals Mod Manager")
        
        # Initialize application state
        self.active_profile = {}
        self.temp_dirs = []  # Temporary directories for extracted mods

        # Configuration and UI setup
        self.selected_folder, self.dark_theme, self.current_profile = load_config()
        self.show_mod_manager()
        self.apply_theme()
        self.update_active_profile_label()
        
        # Sync all profiles before showing the UI
        self.sync_profiles()       

        # Register the exit handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)        

        # Set initial size
        window_width = 800
        window_height = 600

        # Calculate position to center the window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = (screen_width // 2) - (window_width // 2)
        y_position = (screen_height // 2) - (window_height // 2)

        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.root.resizable(False, False)

        # Load configuration
        self.selected_folder, self.dark_theme, self.current_profile = load_config()

        # Ensure the current profile exists or create a default profile
        profiles_folder = os.path.join(
            os.getenv("LOCALAPPDATA"), "MarvelRivalsModManager", "profiles"
        )
        if not os.path.exists(profiles_folder) or not os.listdir(profiles_folder):
            # No profiles exist, reset current_profile and create default profile
            self.current_profile = None
            self.save_config()
            self.ensure_default_profile()  # Create and load the Default profile
            
        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), "app.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        # Show the appropriate initial UI
        if self.selected_folder and verify_game_folder(self.selected_folder):
            self.show_mod_manager()
        else:
            self.show_folder_selector()
            
    def ensure_default_profile(self):
        """Ensure a default profile is created only if no profiles exist and none is active."""
        profiles_folder = os.path.join(
            os.getenv("LOCALAPPDATA"), "MarvelRivalsModManager", "profiles"
        )
        default_profile_name = "Default"
        default_profile_path = os.path.join(profiles_folder, default_profile_name)

        # Check if profiles exist
        profiles_exist = os.path.exists(profiles_folder) and any(
            os.path.isdir(os.path.join(profiles_folder, d)) for d in os.listdir(profiles_folder)
        )

        # If profiles exist and current_profile is set, do nothing
        if profiles_exist and self.current_profile:
            print("DEBUG: Profiles exist and an active profile is set. No default profile needed.")
            return  # Exit early as no default profile is needed

        # Create profiles folder if it doesn't exist
        os.makedirs(profiles_folder, exist_ok=True)

        # Create default profile if no other profiles exist
        if not profiles_exist:
            os.makedirs(default_profile_path)
            self.current_profile = default_profile_name
            self.save_config()  # Update the config to set the default profile
            self.update_active_profile_label()
            messagebox.showinfo("Info", "A default profile has been created and loaded.")
        else:
            print("DEBUG: Profiles exist but no active profile. Setting default profile.")
            # Set default profile if no active profile is found
            if not self.current_profile:
                self.current_profile = default_profile_name
                self.save_config()
                self.update_active_profile_label()

        
    def _create_popup(self, title, size="300x150", resizable=False, icon_path=None):
        """Create a generic popup window."""
        popup = tk.Toplevel(self.root)
        popup.title(title)

        # Set size and center the popup
        popup.geometry(size)
        popup.update_idletasks()  # Ensure dimensions are accurate before positioning
        popup_width = popup.winfo_width()
        popup_height = popup.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = (screen_width // 2) - (popup_width // 2)
        y_position = (screen_height // 2) - (popup_height // 2)
        popup.geometry(f"{size}+{x_position}+{y_position}")

        if not resizable:
            popup.resizable(False, False)
        if icon_path and os.path.exists(icon_path):
            popup.iconbitmap(icon_path)
        return popup

        
    def add_mod(self):
        """Add a mod to the applied mods list."""
        if not self.current_profile:  # Only create Default if no profile is active
            self.ensure_default_profile()
            
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Supported Mod Files", "*.pak *.zip *.7z *.rar")  # Unified filter for supported files
            ]
        )
        if file_path:
            mod_name = os.path.basename(file_path)

            # Handle .pak files directly
            if file_path.endswith(".pak"):
                self.add_pak_to_list(file_path)
                return

            # Handle archive files
            if file_path.endswith((".zip", ".7z", ".rar")):
                try:
                    # Create a temporary directory for the archive
                    temp_dir = tempfile.mkdtemp()
                    self.temp_dirs.append(temp_dir)  # Store temp directory for cleanup later

                    if file_path.endswith(".zip"):
                        with zipfile.ZipFile(file_path, "r") as archive:
                            archive.extractall(temp_dir)
                    elif file_path.endswith(".7z"):
                        with py7zr.SevenZipFile(file_path, "r") as archive:
                            archive.extractall(temp_dir)
                    elif file_path.endswith(".rar"):
                        with rarfile.RarFile(file_path, "r") as archive:
                            archive.extractall(temp_dir)

                    # Add all .pak files in the extracted temp directory to the Applied Mods list
                    for root, _, files in os.walk(temp_dir):
                        for extracted_file in files:
                            if extracted_file.endswith(".pak"):
                                extracted_path = os.path.join(root, extracted_file)
                                self.add_pak_to_list(extracted_path)

                except Exception as e:
                    messagebox.showerror("Error", f"Failed to extract archive: {e}")

    def add_pak_to_list(self, file_path):
        """Add a .pak file to the Applied Mods list."""
        mod_name = os.path.basename(file_path)

        # Check if the mod already exists in the listbox
        existing_mods = self.applied_mods_listbox.get(0, tk.END)
        if mod_name in existing_mods:
            messagebox.showinfo("Info", f"Mod '{mod_name}' is already added.")
            return

        try:
            # Add the mod to the listbox without copying
            self.applied_mods_listbox.insert(tk.END, mod_name)
            # Optionally, store the original file path for later use
            self.active_profile[mod_name] = file_path
            self.update_pak_list()  # Refresh Paks in folder after adding
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add mod: {e}")
            
    def on_exit(self):
        """Sync .paks in the Mods folder with the currently loaded profile before exiting."""
        if self.current_profile:
            # Get the current profile path
            profiles_folder = os.path.join(
                os.getenv("LOCALAPPDATA"), "MarvelRivalsModManager", "profiles"
            )
            current_profile_path = os.path.join(profiles_folder, self.current_profile)
            os.makedirs(current_profile_path, exist_ok=True)

            # Get the Mods folder path
            mods_folder = os.path.join(
                self.selected_folder, "MarvelGame", "Marvel", "Content", "Paks", "Mods"
            )
            if not os.path.exists(mods_folder):
                print("DEBUG: No Mods folder found. Nothing to sync.")
                self.root.destroy()
                return

            try:
                # Get lists of .pak files in Mods and Profile folders
                mods_files = {file for file in os.listdir(mods_folder) if file.endswith(".pak")}
                profile_files = {file for file in os.listdir(current_profile_path) if file.endswith(".pak")}

                # Copy new .pak files from Mods to Profile
                for file in mods_files - profile_files:
                    source_path = os.path.join(mods_folder, file)
                    destination_path = os.path.join(current_profile_path, file)
                    shutil.copy2(source_path, destination_path)
                    print(f"DEBUG: Added {file} to {destination_path}")

                # Remove .pak files from Profile that are no longer in Mods
                for file in profile_files - mods_files:
                    file_path = os.path.join(current_profile_path, file)
                    os.remove(file_path)
                    print(f"DEBUG: Removed {file} from {file_path}")
            except Exception as e:
                print(f"ERROR: Failed to sync mods with profile: {e}")

        # Perform cleanup (temporary directories, etc.)
        self.cleanup_temp_dirs()

        # Exit the program
        self.root.destroy()

    def sync_profiles(self):
        """Ensure all profiles have an up-to-date profile.json file."""
        profiles_folder = os.path.join(
            os.getenv("LOCALAPPDATA"), "MarvelRivalsModManager", "profiles"
        )

        if not os.path.exists(profiles_folder):
            print("DEBUG: No profiles folder found to sync.")
            return

        try:
            for profile_name in os.listdir(profiles_folder):
                profile_path = os.path.join(profiles_folder, profile_name)
                if os.path.isdir(profile_path):  # Only process directories
                    json_path = os.path.join(profile_path, "profile.json")
                    pak_files = [
                        file for file in os.listdir(profile_path) if file.endswith(".pak")
                    ]

                    # Write the .pak files to profile.json
                    with open(json_path, "w") as json_file:
                        json.dump({"mods": pak_files}, json_file, indent=4)

                    print(f"DEBUG: Synced profile.json for profile '{profile_name}'.")
        except Exception as e:
            print(f"ERROR: Failed to sync profiles: {e}")           

    def cleanup_temp_dirs(self):
        """Delete any temporary directories created during the session."""
        try:
            for temp_dir in self.temp_dirs:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            self.temp_dirs = []  # Reset the list after cleanup
        except Exception as e:
            print(f"DEBUG: Failed to clean up temporary directories: {e}")

    def on_close(self):
        """Handle program exit."""
        self.cleanup_temp_dirs()  # Clean up temporary directories
        self.root.destroy()
        
    def save_config(self):
        """Save the current configuration to the config.json file."""
        config_path = os.path.join(
            os.getenv("LOCALAPPDATA"), "MarvelRivalsModManager", "config.json"
        )
        config_data = {
            "game_dir": self.selected_folder,
            "dark_theme": self.dark_theme,
            "current_profile": self.current_profile,
        }

        try:
            with open(config_path, "w") as config_file:
                json.dump(config_data, config_file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")



    def apply_theme(self):
        """Apply the selected theme to the application."""
        dark_bg = "#191918"
        light_bg = "white"
        light_fg = "black"
        dark_fg = "white"

        style = ttk.Style()
        if self.dark_theme:
            style.theme_use("clam")
            style.configure("TLabel", background=dark_bg, foreground=dark_fg)
            style.configure("TButton", background="#555", foreground=dark_fg)
            style.configure("TFrame", background=dark_bg)
            self.root.configure(bg=dark_bg)

            # Apply dark theme to specific widgets
            if hasattr(self, "pak_listbox"):
                self.pak_listbox.config(
                    bg=dark_bg, fg=dark_fg, highlightbackground="#555", selectbackground="#555", selectforeground=dark_fg
                )
            if hasattr(self, "applied_mods_listbox"):
                self.applied_mods_listbox.config(
                    bg=dark_bg, fg=dark_fg, highlightbackground="#555", selectbackground="#555", selectforeground=dark_fg
                )

            # Ensure all frames and containers are dark
            for frame_attr in ["main_frame", "left_frame", "right_frame", "actions_frame"]:
                if hasattr(self, frame_attr):
                    getattr(self, frame_attr).config(bg=dark_bg)

        else:
            style.theme_use("default")
            style.configure("TLabel", background=light_bg, foreground=light_fg)
            style.configure("TButton", background=light_bg, foreground=light_fg)
            style.configure("TFrame", background=light_bg)
            self.root.configure(bg="SystemButtonFace")

            # Reset to light theme for specific widgets
            if hasattr(self, "pak_listbox"):
                self.pak_listbox.config(
                    bg=light_bg, fg=light_fg, highlightbackground="SystemButtonFace", selectbackground="SystemHighlight", selectforeground=light_fg
                )
            if hasattr(self, "applied_mods_listbox"):
                self.applied_mods_listbox.config(
                    bg=light_bg, fg=light_fg, highlightbackground="SystemButtonFace", selectbackground="SystemHighlight", selectforeground=light_fg
                )

            # Reset frame backgrounds
            for frame_attr in ["main_frame", "left_frame", "right_frame", "actions_frame"]:
                if hasattr(self, frame_attr):
                    getattr(self, frame_attr).config(bg=light_bg)



    def toggle_theme(self, enabled):
        """Enable or disable the dark theme."""
        self.dark_theme = enabled
        self.apply_theme()
        self.save_config()  # Save the updated theme setting


    def show_folder_selector(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Select your Marvel's Avengers game folder:").pack(pady=20)
        tk.Button(self.root, text="Browse", command=self.browse_folder).pack()

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            if verify_game_folder(folder_selected):
                self.selected_folder = folder_selected
                self.save_config()
                self.show_mod_manager()
            else:
                messagebox.showerror("Error", "Invalid game folder selected.")

    def show_mod_manager(self):
        # Clear previous widgets, but ensure the menu remains attached
        for widget in self.root.winfo_children():
            if not isinstance(widget, tk.Menu):  # Do not destroy the menu
                widget.destroy()

        # Menu Bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)  # Attach menu to the root window

        # File Menu
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Launch Game", command=self.launch_game)  # Add Launch Game
        filemenu.add_separator()
        filemenu.add_command(label="Settings", command=self.open_settings)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="Menu", menu=filemenu)

        # About Menu Button
        about_menu = tk.Menu(menubar, tearoff=0)
        about_menu.add_command(label="Help", command=self.show_about)
        menubar.add_cascade(label="About", menu=about_menu)

        # Main Frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left Frame (Paks in Folder)
        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Display Current Profile
        active_profile_text = f"Active Profile: {self.current_profile or 'None'}"
        print(f"DEBUG: Setting current_profile_label with text: {active_profile_text}")  # Debug
        self.current_profile_label = tk.Label(self.left_frame, text=active_profile_text, font=("Arial", 10, "bold"))
        self.current_profile_label.pack(pady=5)

        tk.Label(self.left_frame, text="Paks in folder:").pack(pady=(0, 5))
        self.pak_listbox = tk.Listbox(self.left_frame)
        self.pak_listbox.pack(fill=tk.BOTH, expand=True)

        self.actions_frame = tk.Frame(self.left_frame)
        self.actions_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(self.actions_frame, text="Save Profile", command=self.save_profile, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(self.actions_frame, text="Load Profile", command=self.load_profile, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(self.actions_frame, text="Refresh", command=self.update_pak_list, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(self.actions_frame, text="Clear", command=self.clear_mods, width=15).pack(side=tk.LEFT, padx=5)

        # Right Frame (Applied Mods)
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        tk.Label(self.right_frame, text="Applied Mods:").pack(pady=(0, 5))
        self.applied_mods_listbox = tk.Listbox(self.right_frame)
        self.applied_mods_listbox.pack(fill=tk.BOTH, expand=True)
        self.applied_mods_listbox.bind('<<ListboxSelect>>', self.on_mod_select)

        button_frame = tk.Frame(self.right_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        tk.Button(button_frame, text="Add Mod", command=self.add_mod).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.remove_mod_button = tk.Button(button_frame, text="Remove Mod", command=self.remove_mod, state=tk.DISABLED)
        self.remove_mod_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        tk.Button(button_frame, text="Apply", command=self.apply_mods).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Refresh Paks in folder list
        self.update_pak_list()
        self.pak_listbox.bind("<Button-3>", self.show_context_menu)

        # Apply the selected theme
        self.apply_theme()


    def show_about(self):
        """Display the About message."""
        messagebox.showinfo("About", "ARMED AND DANGEROUS!")
        
    def clear_mods(self):
        """Clear all .paks from the Mods folder and the current profile folder, then update the profile JSON."""
        if not self.current_profile:
            messagebox.showerror("Error", "No active profile to clear.")
            return

        # Get the Mods folder path
        mods_folder = os.path.join(
            self.selected_folder, "MarvelGame", "Marvel", "Content", "Paks", "Mods"
        )
        # Get the current profile folder path
        profiles_folder = os.path.join(
            os.getenv("LOCALAPPDATA"), "MarvelRivalsModManager", "profiles"
        )
        current_profile_path = os.path.join(profiles_folder, self.current_profile)

        if not os.path.exists(mods_folder) and not os.path.exists(current_profile_path):
            messagebox.showinfo("Info", "No Mods folder or profile folder found to clear.")
            return

        # Confirm clearing the Mods folder and profile folder
        confirm = messagebox.askyesno(
            "Confirm Clear",
            f"Are you sure you want to clear all .pak files from the Mods folder and profile '{self.current_profile}'?",
        )
        if not confirm:
            return

        try:
            # Clear the Mods folder
            if os.path.exists(mods_folder):
                for file in os.listdir(mods_folder):
                    if file.endswith(".pak"):
                        os.remove(os.path.join(mods_folder, file))
                        print(f"DEBUG: Removed {file} from Mods folder.")

            # Clear the current profile folder
            if os.path.exists(current_profile_path):
                for file in os.listdir(current_profile_path):
                    if file.endswith(".pak"):
                        os.remove(os.path.join(current_profile_path, file))
                        print(f"DEBUG: Removed {file} from profile '{self.current_profile}'.")

            # Save an empty mods list to profile.json
            json_path = os.path.join(current_profile_path, "profile.json")
            with open(json_path, "w") as json_file:
                json.dump({"mods": []}, json_file, indent=4)
            print(f"DEBUG: Updated profile '{self.current_profile}' with no mods.")

            # Refresh the Paks in Folder list
            self.update_pak_list()

            # Sync all profiles
            self.sync_profiles()

            messagebox.showinfo("Success", "Mods and profile cleared successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear Mods or profile: {e}")


        
    def open_settings(self):
        """Open the settings popup."""
        popup = tk.Toplevel(self.root)
        popup.title("Settings")
        popup.geometry("800x600")  # Set default size

        # Center the popup on the screen
        popup.update_idletasks()
        popup_width = popup.winfo_width()
        popup_height = popup.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = (screen_width // 2) - (popup_width // 2)
        y_position = (screen_height // 2) - (popup_height // 2)
        popup.geometry(f"400x200+{x_position}+{y_position}")

        # Make it non-resizable
        popup.resizable(False, False)

        # Set the app icon
        icon_path = os.path.join(os.path.dirname(__file__), "app.ico")
        if os.path.exists(icon_path):
            popup.iconbitmap(icon_path)

        # Settings content
        tk.Label(popup, text="Settings", font=("Arial", 14, "bold")).pack(pady=10)

        # Current Game Directory
        tk.Label(popup, text="Game Directory:").pack(pady=5)
        tk.Label(popup, text=self.selected_folder or "Not Set").pack()

        # Change Game Directory Button
        tk.Button(popup, text="Change Game Directory", command=self.show_folder_selector).pack(pady=5)

        # Theme Toggle
        theme_var = tk.BooleanVar(value=self.dark_theme)
        tk.Checkbutton(
            popup,
            text="Enable Dark Theme",
            variable=theme_var,
            command=lambda: self.toggle_theme(theme_var.get()),
        ).pack(pady=5)

    def update_pak_list(self):
        """Refresh the displayed lists of Paks in Folder and Applied Mods."""
        self.sync_profiles()   
        self.pak_listbox.delete(0, tk.END)
        if self.selected_folder:
            mods_folder = os.path.join(self.selected_folder, "MarvelGame", "Marvel", "Content", "Paks", "Mods")
            if os.path.exists(mods_folder):
                for pak in sorted(os.listdir(mods_folder)):  # Alphabetically sort for UX
                    if pak.endswith(".pak"):
                        self.pak_listbox.insert(tk.END, pak)

                
    def show_context_menu(self, event):
        """Show the context menu and highlight the item under the cursor."""
        try:
            # Get the index of the item under the cursor
            index = self.pak_listbox.nearest(event.y)
            if index >= 0:
                # Highlight the item
                self.pak_listbox.selection_clear(0, tk.END)
                self.pak_listbox.selection_set(index)
                self.pak_listbox.activate(index)

                # Get the file name and path
                file_name = self.pak_listbox.get(index)
                file_path = os.path.join(self.selected_folder, "MarvelGame", "Marvel", "Content", "Paks", "Mods", file_name)

                # Create the context menu
                menu = tk.Menu(self.root, tearoff=0)
                menu.add_command(label="View File Location", command=lambda: self.view_file_location(file_path))
                menu.add_command(label="Remove from Folder", command=lambda: self.remove_from_folder(file_path))
                menu.post(event.x_root, event.y_root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show context menu: {e}")

    def remove_from_folder(self, file_path):
        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove {os.path.basename(file_path)}?"):
            os.remove(file_path)
            self.update_pak_list()
            

    def view_file_location(self, file_path):
        os.startfile(os.path.dirname(file_path))

    def _extract_and_add_paks(self, archive, archive_path):
        for member in archive.namelist():
            if member.endswith(".pak") and "Paks" in member:
                extraction_path = os.path.join(
                    self.selected_folder,
                    "MarvelGame",
                    "Marvel",
                    "Content",
                    "Paks",
                    "Mods",
                    os.path.basename(member),
                )
                with archive.open(member, "r") as source, open(extraction_path, "wb") as target:
                    shutil.copyfileobj(source, target)
                self.applied_mods_listbox.insert(tk.END, os.path.basename(member))
                
    def on_mod_select(self, event):
        """Enable the Remove Mod button when a mod is selected in Applied Mods."""
        selection = self.applied_mods_listbox.curselection()
        if selection:
            self.remove_mod_button.config(state=tk.NORMAL)  # Enable the button
        else:
            self.remove_mod_button.config(state=tk.DISABLED)  # Disable the button

                
    def remove_mod(self):
        selection = self.applied_mods_listbox.curselection()
        if selection:
            selected_mod = self.applied_mods_listbox.get(selection[0])
        mods_folder = os.path.join(self.selected_folder, "MarvelGame", "Marvel", "Content", "Paks", "Mods")
        mod_path = os.path.join(mods_folder, selected_mod)
        try:
            if os.path.exists(mod_path):
                os.remove(mod_path)
            self.applied_mods_listbox.delete(selection[0])
            messagebox.showinfo("Success", f"Removed mod '{selected_mod}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove mod: {e}")

    def apply_mods(self):
        if not self.current_profile:
            self.ensure_default_profile()
            
        if not self.selected_folder:
            messagebox.showerror("Error", "No game folder selected.")
            return

        mods_folder = os.path.join(self.selected_folder, "MarvelGame", "Marvel", "Content", "Paks", "Mods")
        os.makedirs(mods_folder, exist_ok=True)


        try:
            for i in range(self.applied_mods_listbox.size()):
                mod_name = self.applied_mods_listbox.get(i)
                source_path = self.active_profile.get(mod_name)  # Get the original file path
                if source_path:
                    destination_path = os.path.join(mods_folder, mod_name)
                    shutil.copy2(source_path, destination_path)

            self.applied_mods_listbox.delete(0, tk.END)  # Clear applied mods after applying
            self.update_pak_list()  # Refresh the Paks in folder
            messagebox.showinfo("Success", "Mods applied successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply mods: {e}")
            
    def update_active_profile_label(self):
        """Update the Active Profile label to show the current profile."""
        if hasattr(self, "current_profile_label"):
            active_profile_text = f"Active Profile: {self.current_profile or 'None'}"
            self.current_profile_label.config(text=active_profile_text)

    def center_popup(self, popup):
        """Centers a popup window on the screen."""
        popup.update_idletasks()  # Ensure geometry is available
        geometry = popup.geometry()  # Debug geometry string
        print(f"DEBUG: Popup geometry: {geometry}")  # Debugging

        try:
            screen_width = popup.winfo_screenwidth()
            screen_height = popup.winfo_screenheight()
            size = tuple(int(_) for _ in geometry.split('+')[0].split('x'))
            x = screen_width // 2 - size[0] // 2
            y = screen_height // 2 - size[1] // 2
            popup.geometry(f"{size[0]}x{size[1]}+{x}+{y}")
        except Exception as e:
            print(f"ERROR: Failed to center popup: {e}")

    def save_profile(self):
        """Save the current Mods folder as a new profile."""
        try:
            profiles_folder = os.path.join(
                os.getenv("LOCALAPPDATA"), "MarvelRivalsModManager", "profiles"
            )
            os.makedirs(profiles_folder, exist_ok=True)  # Ensure the profiles directory exists
            print(f"DEBUG: profiles_folder -> {profiles_folder}")

            # Create popup for saving profile
            popup = tk.Toplevel(self.root)
            print(f"DEBUG: self.root -> {self.root}")
            popup.title("Save Profile")
            popup.geometry("400x200")
            popup.resizable(False, False)

            # Set the icon for the popup
            if hasattr(sys, "_MEIPASS"):
                icon_path = os.path.join(sys._MEIPASS, "app.ico")
            else:
                icon_path = os.path.join(os.path.dirname(__file__), "app.ico")
            print(f"DEBUG: icon_path -> {icon_path}")

            if os.path.exists(icon_path):
                popup.iconbitmap(icon_path)
            else:
                print("DEBUG: app.ico not found for Save Profile popup.")

            # Add label and entry for profile name
            tk.Label(popup, text="Enter a name for the profile:").pack(pady=10)
            profile_name_var = tk.StringVar()
            profile_name_entry = tk.Entry(popup, textvariable=profile_name_var)
            profile_name_entry.pack(pady=5)
            print(f"DEBUG: profile_name_var -> {profile_name_var}")

            # Save Profile Logic
            def confirm_save():
                profile_name = profile_name_var.get().strip()
                print(f"DEBUG: profile_name -> {profile_name}")
                if not profile_name:
                    messagebox.showerror("Error", "Profile name cannot be empty.", parent=popup)
                    return

                # Validate profile name for illegal characters
                invalid_chars = r'<>:"/\\|?*'
                if any(char in profile_name for char in invalid_chars):
                    messagebox.showerror(
                        "Error",
                        f"Profile name cannot contain these characters: {invalid_chars}",
                        parent=popup,
                    )
                    return

                profile_path = os.path.join(profiles_folder, profile_name)
                if os.path.exists(profile_path):
                    messagebox.showerror(
                        "Error",
                        f"A profile with the name '{profile_name}' already exists.",
                        parent=popup,
                    )
                    return

                try:
                    # Create profile folder
                    os.makedirs(profile_path)

                    # Copy .pak files from Mods folder to profile
                    mods_folder = os.path.join(
                        self.selected_folder, "MarvelGame", "Marvel", "Content", "Paks", "Mods"
                    )
                    for file in os.listdir(mods_folder):
                        if file.endswith(".pak"):
                            shutil.copy(
                                os.path.join(mods_folder, file),
                                os.path.join(profile_path, file),
                            )

                    # Save profile metadata
                    profile_metadata = [
                        file for file in os.listdir(mods_folder) if file.endswith(".pak")
                    ]
                    with open(os.path.join(profile_path, "profile.json"), "w") as json_file:
                        json.dump(profile_metadata, json_file)

                    # Update active profile
                    self.current_profile = profile_name
                    self.update_active_profile_label()
                    self.save_config()

                    popup.destroy()
                    messagebox.showinfo("Success", f"Profile '{profile_name}' has been saved.")
                except Exception as error:
                    messagebox.showerror(
                        "Error", f"An error occurred while saving the profile: {error}", parent=popup
                    )

            # Add Save and Cancel buttons
            tk.Button(popup, text="Save", command=confirm_save).pack(pady=5)
            tk.Button(popup, text="Cancel", command=popup.destroy).pack(pady=5)

            # Center the popup manually
            popup.update_idletasks()
            screen_width = popup.winfo_screenwidth()
            screen_height = popup.winfo_screenheight()
            popup_width = 400
            popup_height = 200
            x = (screen_width - popup_width) // 2
            y = (screen_height - popup_height) // 2
            popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
            print(f"DEBUG: Popup centered at {x}, {y}")

        except Exception as error:
            print(f"DEBUG: Exception in save_profile -> {error}")
            messagebox.showerror("Error", f"An unexpected error occurred: {error}")


    def load_profile(self):
        """Load a selected profile from a dropdown menu with the option to delete profiles."""
        try:
            # Retrieve profiles folder
            profiles_folder = os.path.join(
                os.getenv("LOCALAPPDATA"), "MarvelRivalsModManager", "profiles"
            )
            if not os.path.exists(profiles_folder):
                messagebox.showerror("Error", "Profiles folder not found.")
                return

            # Retrieve list of profiles
            profiles = [
                name for name in os.listdir(profiles_folder)
                if os.path.isdir(os.path.join(profiles_folder, name))
            ]
            if not profiles:
                messagebox.showinfo("Info", "No profiles available to load.")
                return

            # Exclude the current profile
            profiles = [profile for profile in profiles if profile != self.current_profile]
            if not profiles:
                messagebox.showinfo("Info", "No other profiles available to load.")
                return

            # Create popup for profile selection
            popup = tk.Toplevel(self.root)
            popup.title("Load Profile")
            popup.geometry("400x200")
            popup.resizable(False, False)

            # Set popup icon
            if hasattr(sys, "_MEIPASS"):
                icon_path = os.path.join(sys._MEIPASS, "app.ico")
            else:
                icon_path = os.path.join(os.path.dirname(__file__), "app.ico")
            if os.path.exists(icon_path):
                popup.iconbitmap(icon_path)

            # Add label and dropdown
            tk.Label(popup, text="Select a Profile to Load:").pack(pady=10)
            profile_var = tk.StringVar(value=profiles[0])
            profile_dropdown = ttk.Combobox(
                popup, textvariable=profile_var, values=profiles, state="readonly"
            )
            profile_dropdown.pack(pady=5)

            # Confirm Load Profile Logic
            def confirm_load():
                selected_profile = profile_var.get()
                if not selected_profile:
                    messagebox.showerror("Error", "No profile selected.", parent=popup)
                    return

                try:
                    # Load the selected profile
                    profile_path = os.path.join(profiles_folder, selected_profile)
                    mods_folder = os.path.join(
                        self.selected_folder, "MarvelGame", "Marvel", "Content", "Paks", "Mods"
                    )

                    # Clear the Mods folder
                    if os.path.exists(mods_folder):
                        for file in os.listdir(mods_folder):
                            if file.endswith(".pak"):
                                os.remove(os.path.join(mods_folder, file))

                    # Copy profile .pak files to Mods
                    for file in os.listdir(profile_path):
                        if file.endswith(".pak"):
                            shutil.copy(os.path.join(profile_path, file), mods_folder)

                    # Update current profile
                    self.current_profile = selected_profile
                    self.update_active_profile_label()
                    self.update_pak_list()
                    self.save_config()

                    popup.destroy()
                    messagebox.showinfo("Success", f"Profile '{selected_profile}' loaded.")
                except Exception as error:
                    messagebox.showerror("Error", f"Failed to load profile: {error}")

            tk.Button(popup, text="Load", command=confirm_load).pack(pady=5)

            # Delete Profile Logic
            def delete_profile():
                selected_profile = profile_var.get()
                if not selected_profile:
                    messagebox.showerror("Error", "No profile selected.", parent=popup)
                    return

                confirm = messagebox.askyesno(
                    "Confirm Delete",
                    f"Are you sure you want to delete the profile '{selected_profile}'?",
                    parent=popup,
                )
                if confirm:
                    try:
                        shutil.rmtree(os.path.join(profiles_folder, selected_profile))
                        profiles.remove(selected_profile)
                        profile_dropdown["values"] = profiles
                        profile_var.set(profiles[0] if profiles else "")
                        messagebox.showinfo("Success", f"Profile '{selected_profile}' deleted.")
                    except Exception as error:
                        messagebox.showerror("Error", f"Failed to delete profile: {error}")

            tk.Button(popup, text="Delete Profile", command=delete_profile).pack(pady=5)
            tk.Button(popup, text="Cancel", command=popup.destroy).pack(pady=5)

            # Center the popup after geometry is set
            self.root.after(10, lambda: self.center_popup(popup))

        except Exception as error:
            messagebox.showerror("Error", f"An unexpected error occurred: {error}")

    def apply_profile(self, profile_name):
        """Apply the mods from the selected profile."""
        try:
            profiles_folder = os.path.join(BACKUP_FOLDER, "Profiles")
            profile_folder = os.path.join(profiles_folder, profile_name)
            profile_json_path = os.path.join(profile_folder, "profile.json")

            if not os.path.exists(profile_json_path):
                messagebox.showerror("Error", "Invalid profile: Missing profile.json file.")
                return

            with open(profile_json_path, "r") as f:
                profile_paks = json.load(f)

            # Get the current .pak files in the Mods folder
            mods_folder = os.path.join(self.selected_folder, "MarvelGame", "Marvel", "Content", "Paks", "Mods")
            os.makedirs(mods_folder, exist_ok=True)
            current_paks = {pak for pak in os.listdir(mods_folder) if pak.endswith(".pak")}

            # Remove .pak files not in the profile
            for current_pak in current_paks:
                if current_pak not in profile_paks:
                    os.remove(os.path.join(mods_folder, current_pak))

            # Add missing .pak files from the profile
            for pak in profile_paks:
                source_path = os.path.join(profile_folder, pak)
                destination_path = os.path.join(mods_folder, pak)
                if not os.path.exists(destination_path):
                    shutil.copy2(source_path, destination_path)

            # Update the current profile
            self.current_profile = profile_name
            self.save_config()  # Save the updated profile to config

            # Refresh the UI and reapply the theme
            self.show_mod_manager()
            self.apply_theme()

            messagebox.showinfo("Success", f"Profile '{profile_name}' loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply profile: {e}")

    def launch_game(self):
        """Confirm and launch the game via Steam."""
        confirm = messagebox.askyesno("Launch Game", "Are you sure you want to launch the game?")
        if confirm:
            try:
                # Run the command silently
                subprocess.run(["cmd", "/c", "start", "steam://rungameid/2767030"], shell=True)
                messagebox.showinfo("Success", "The game has been launched!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch the game: {e}")

                
    def cleanup_temp_dirs(self):
        """Clean up all temporary directories."""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        self.temp_dirs.clear()  # Clear the list after cleanup
        
    def on_close(self):
        """Handle program exit."""
        self.cleanup_temp_dirs()  # Clean up temporary directories
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ModManagerApp(root)
    root.mainloop()
