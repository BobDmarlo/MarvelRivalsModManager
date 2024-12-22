

# Marvel Rivals Mod Manager


Marvel Rivals Mod Manager is an easy tool designed to simplify managing modded .paks for **Marvel Rivals**. It allows you to organize, apply, and create mod profiles with ease.

# features
[(Back to top)](#table-of-contents)


✨ Features

General Features

Game Folder Verification: Ensures the correct game folder is selected by checking for MarvelRivals_Launcher.exe.

Intuitive Mod Management:
Drag-and-drop support for .pak, .zip, .7z, and .rar files.

Automatically extracts archives and adds .pak files to the mods list.

Profiles
Save mod configurations as profiles for quick switching.

Automatically sync profile contents when the program launches or profiles are loaded.

Dark Mode (Optional)
Supports a customizable dark theme for a comfortable UI experience.

Integrated Launcher
Launch the game directly from the application with one click.






# Table of Contents
- [Table of Contents](#table-of-contents)
- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)


# Installation
[(Back to top)](#table-of-contents)

### Option 1: Running the Python Script
To run the project directly from Python:

1. **Install Python**:
   - Download and install Python 3.8 or higher from [python.org](https://www.python.org).
   - Ensure `pip` is included in the installation.

2. **Clone the Repository**:
   ```bash
   git clone https://github.com/BobDmarlo/marvel-mod-manager.git
   cd marvel-mod-manager

3. **Install Dependencies: Install the required libraries**:

pip install py7zr rarfile Pillow

4. **Run the Application: Execute the script**: Either open the file or type in cmd
python MarvelRivalsModManager.py

Option 2: Using the Pre-Compiled Executable
If you prefer not to install Python:

Download the .exe File from:

Navigate to the Releases section of this repository and download the latest version of marvel-mod-manager.exe.
https://github.com/BobDmarlo/MarvelRivalsModManager/releases

Run the Application:

Double-click the .exe file to start the program.
No installation or additional setup is required.

Option 3: Compiling the Script into an Executable

🔧 Troubleshooting
Common Issues:

1. Missing DLL Errors:
Install the Microsoft Visual C++ Redistributable.
2. Black Window or UI Issues:
Ensure your graphics drivers are up to date.
3. Dependencies Not Found:
Run the following command to ensure all required dependencies are installed:
pip install py7zr rarfile Pillow


# Usage
[(Back to top)](#table-of-contents)

🛠️ How to Use the Program:

**Step 1**: Select Your Game Directory
Launch the program.
On the first screen, select the MarvelRivals game folder.

The program verifies the folder by checking for MarvelRivals_Launcher.exe.


**Step 2**: Managing Mods
The left panel displays the .pak files currently in the Mods folder.

The right panel shows applied mods for the active profile.

**Adding Mods**:
Click Add Mod to import .pak, .zip, .7z, or .rar files.

The program extracts the contents (if necessary) and displays them in the Applied Mods section.

**Applying Mods**:

Check the mods you'd like to apply.
Click Apply to move the selected mods into the game’s Mods folder.

Clearing Mods:
Use the Clear Mods button to remove all .pak files from the Mods folder and the current profile.

**Step 3**: Using Profiles

Save a Profile: Store the current set of applied mods for quick switching.

Load a Profile: Switch between different mod configurations.

