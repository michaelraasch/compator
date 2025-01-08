#!/usr/bin/env python3

# you can either exexute it as
# ./xtcinstaller.py [args]
# python3 xtcinstaller.py [args]

import inspect
import json
import os
import shutil
import subprocess
import sys
from enum import Enum

class OperatingSystem(Enum):
  MacOS = 1
  Linux = 2
  Windows = 3

# Checks if the given applications are installed on the system.
def check_required_applications(): 

  required_apps = {}
  for app in applications:
    is_installed = shutil.which(app) is not None
    installed_apps[app] = is_installed
    print(f"{app}: {'Installed' if is_installed else 'Not installed'}")
  return installed_apps

def print_usage(script_name) -> bool:
  """Prints the usage instructions for the script."""
  print(f"Usage: {script_name} <repo>")
  print("  repo: xvm|platform|examples")

# executes an array of commands
def execute_commmands(commands):
  for command in commands:
    success = execute_commmand(command)
    if not success:
      return False
  return True 

# executes one system command 
def execute_commmand(command) -> bool:
  try:
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for line in process.stdout:
      print(line, end="")  # Print each line of output as it comes
    return_code = process.wait()  # Wait for the process to finish
    if return_code == 0:
      print(f"Successfully executed {' '.join(command)}")
      return True
    else:
      print(f"Error exexuting {' '.join(command)}")
      return False

  except (OSError, subprocess.SubprocessError) as e:
    print(f"An error occurred while executing {e}")
    return False

  return True

def process_repo(repo_name) -> bool:

  cwd = os.getcwd()

  repo_url = f"https://github.com/xtclang/{repo_name}.git"
  commands = None

  # Either clones or updates the specified repository from GitHub.
  # 1. check if the folder already exists. If so then is it a git repo? then ask whether to update or not.
  # 2. if it does not exist then close 
  if os.path.exists(repo_name) and os.path.isdir(repo_name):

    git_folder_path = os.path.join(repo_name, ".git")

    if os.path.exists(git_folder_path) and os.path.isdir(git_folder_path):

      # the repo already exists so offer the user some choices what to do
      print(f"'{repo_name}' is already repo. What do you want to do?")

      choice = None
      while True:
        choice = input("(U)pdate from remote and continue, (I)gnore remote and continue, (A)bort the whole process: U/I/A? ").upper()  # Convert input to uppercase for case-insensitivity
        if choice in ("U", "I", "A"):
          break
        else:
          print("Invalid choice. Please enter U, I, or A.")

      if choice == "A":
        print("Aborting")
        return False

      if choice == "I":
        print("Ignoring any repo operations.")
        return True

      if choice == "U":
        commands = [
          ["git", "fetch"],
          ["git", "pull"]
        ]

        # chdir into the repo to execute the commands
        os.chdir(repo_name)

    else:
      print(f"Folder '{repo_name}' exists, but is not a repo. Aborting...")
      return False

  else:
    # the folder does not exist so clone it
    commands = [
      ["git", "clone", repo_url]
    ]

  success = execute_commmands(commands)

  os.chdir(cwd)

  return success

def install_xvm(install_dir : str, operating_system : OperatingSystem) -> bool:

  repo = "xvm"

  success = process_repo(repo)
  if not success:
    return success

  try:
    # Change directory to the repository path
    os.chdir(repo)

    # Execute the gradlew command with real-time output
    process = subprocess.Popen(["./gradlew", "installDist"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for line in process.stdout:  # Process and print output line by line
      print(line, end="")   
    return_code = process.wait()

    if return_code != 0:
      print("Error running gradlew installDist.")
      return False

  except (OSError, subprocess.SubprocessError) as e:
    print(f"An error occurred while running gradlew installDist: {e}")
    return False

  cwd = os.getcwd()

  # amend the shell rcs. There is no 100% correct way to figure out what shell the user is running, so we do the following:
  # amend any rc file we find: ~/.zshrc and ~/.bashrc
  xdk_home = f"{cwd}/xdk/build/install/xdk"

  home_dir = os.path.expanduser("~") 
  for shell in [".zshrc", ".bashrc"]:
    filename = os.path.join(home_dir, shell)
    if os.path.exists(filename):

      print(f"Amending shell rc {filename}")
      with open(filename, "r") as file:
        lines = file.readlines()  # Read all lines into a list

      # we will remove any pre-existing XDK_HOME so we don't duplicate anything from a previous run
      with open(filename, "w") as file:
        for line in lines:
          if "XDK_HOME" not in line:  # Check if the line contains the string XDK_HOME
            file.write(line)  # Write the line back if it doesn't contain the string

        # append the new XDK_HOME lines
        file.write(f"export XDK_HOME='{xdk_home}'\n")  # Write the line with a newline character
        file.write(f"export PATH=$XDK_HOME/bin:$PATH\n")

  # we need xcc and xec. The correct way it to run shell script based on the OS
  os.chdir(f"{xdk_home}/bin")

  try:

    script_names = {
      OperatingSystem.Linux : "./cfg_linux.sh",
      OperatingSystem.MacOS : "./cfg_macos.sh",
      OperatingSystem.Windows : "./cfg_windows.cmd",
    }

    script_name = script_names[operating_system]

    process = subprocess.Popen([script_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for line in process.stdout:
      print(line, end="")
    return_code = process.wait()

    if return_code == 0:
      print(f"{os.getcwd()}/{script_name} executed successfully.")
    else:
      print(f"Error executing {script_name}.")
      return False

  except (OSError, subprocess.SubprocessError) as e:
    print(f"An error occurred while executing the script: {e}")
    return False

  return True

# amend the firewall rules
def amend_firewall_rules(platform_folder_path : str, operating_system : OperatingSystem, enable : bool) -> bool:

  current_function_name = inspect.currentframe().f_code.co_name

  success = True
  print("Amending the Firewall rules requires root access, Please enter your password.")

  match operating_system:
    case OperatingSystem.MacOS:

      filename = os.path.join(platform_folder_path, "port-forwarding.conf")
      try:
        os.remove(filename)
      except FileNotFoundError:
        nop = None

      # create file containing the port forwarding details
      try:
        with open(filename, "w") as file:
          file.write("\n")  # Write an empty line first

          # only if we want to enable the rules we will write them into the file
          # an empty file will remove previously added rules
          if enable:
            file.write("rdr pass on lo0 inet proto tcp from any to self port 80 -> 127.0.0.1 port 8080\n")
            file.write("rdr pass on lo0 inet proto tcp from any to self port 443 -> 127.0.0.1 port 8090\n")

        print(f"File '{filename}' created successfully.")

      except OSError as e:
        print(f"Error creating file: {e}")
        return False

      command = ["sudo", "pfctl", "-f", filename]
      success = execute_commmand(command)
      if not success:
        print("You can ignore the above error because the rules either already already exist or have been deleted. Nothing to see here.")
        success = True

      if not enable:
        try:
          os.remove(filename)
        except FileNotFoundError:
          nop = None

    case OperatingSystem.Linux:
      """
      commands = [
        ['sudo', 'nft', 'add', 'chain', 'nat', 'prerouting'],
        ['sudo', 'nft', 'add', 'rule', 'nat', 'prerouting', 'tcp', 'dport', '80', 'redirect', 'to', ':8080'],
        ['sudo', 'nft', 'add', 'rule', 'nat', 'prerouting', 'tcp', 'dport', '443', 'redirect', 'to', ':8090']
      ]

      if not enable:

        # if we want to disable them, then we remove them in reverse order
        commands.reverse()

        for command in commands:
          for i, cmd in enumerate(command):
            if cmd == 'add':
              command[i] = 'delete'


      success = execute_commmands(commands)
      if not success:
        print("You can ignore the above error because the rules either already already exist or have been deleted. Nothing to see here.")
        success = True
      """
    case OperatingSystem.Windows:
      print(f"{current_function_name}(): to do")

  return success

def add_firewall_rules(platform_folder_path : str, operating_system : OperatingSystem) -> bool:
  return amend_firewall_rules(platform_folder_path, operating_system, True)

def remove_firewall_rules(platform_folder_path : str, operating_system : OperatingSystem) -> bool:
  return amend_firewall_rules(platform_folder_path, operating_system, False)

def install_platform(install_dir : str, operating_system : OperatingSystem) -> bool:

  repo = "platform"

  success = process_repo(repo)
  if not success:
    return success

  try:

    home_dir = os.path.expanduser("~")
    xqizit_folder_path = os.path.join(home_dir, "xqiz.it")
    platform_folder_path = os.path.join(xqizit_folder_path, "platform")
    users_folder_path = os.path.join(xqizit_folder_path, "users")

    # create some required folders
    folders = [xqizit_folder_path, platform_folder_path, users_folder_path]
    for folder in folders:
      os.makedirs(folder, exist_ok=True)  # Create the folder
      print(f"Folder '{folder}' created successfully.")

  except OSError as e:
    print(f"Error creating folder: {e}")
    return False

  success = add_firewall_rules(platform_folder_path, operating_system)

  if not success:
    return success

  # Change directory to ./platform/platformUI/gui
  os.chdir(f"./{repo}/platformUI/gui")

  # update the content of package.json and fix the quasar version
  filename = "package.json"
  print(f"patching {filename}")
  
  try:
    with open(filename, "r") as f:
      data = json.load(f)  # Load the JSON data from the file

    data["dependencies"]["quasar"] = "2.15.4"  # Update the quasar version

    with open(filename, "w") as f:
      json.dump(data, f, indent=2)  # Write the updated JSON data back to the file with indentation

    print(f"Successfully updated quasar version in {filename}")

  except (OSError, json.JSONDecodeError) as e:
    print(f"Error updating package.json: {e}")
    return False

  # exeute some npm commands
  commands = [
    ["sudo", "npm", "install"],
    ["sudo", "npm", "install", "-g", "@quasar/cli"]
  ]

  success = execute_commmands(commands)
  if not success:
    return success

  # go back to the repo folder
  os.chdir(os.path.join(install_dir, repo))

  # kick off the build
  # This step will take up to a minute to compile for the first time but will be far quicker in subsequent builds 
  command = ["./gradlew", "build"] 
  success = execute_commmand(command)

  return success

def install_examples(install_dir : str, operating_system : OperatingSystem) -> bool:

  repo = "examples"

  success = process_repo(repo)
  if not success:
    return success

  # Change directory to the repository path
  os.chdir(repo)

  examples = [
    "banking",
#    "counter",
#    "welcome"
  ]

  for example in examples:
    os.chdir(example)

    command = ["gradle", "build"]
    success = execute_commmand(command)

    if not success:
      return success

    os.chdir("..")

  return success

def main(repo : str, operating_system : OperatingSystem):
  """
  This script performs several tasks based on the provided repository.

  Args:
    repo: The repository to operate on. Must be one of "xvm", "platform", or "examples".

  Unfortunately we cannot install multiple at the same time because some of installations require
  environment variables. Those cannot be set from within Python; they have to be set by either reloading
  the current shell rc or by starting a new terminal.
  """

  valid_repos = ["xvm", "platform", "examples"]

  if repo not in valid_repos:
    print("Invalid repository specified.")
    print_usage(sys.argv[0])
    sys.exit(1)

  install_dir = os.getcwd()

  success = None

  if repo == "xvm":
    success = install_xvm(install_dir, operating_system)
    if success:
      print("\nNOTE: To install another repo we need the added environment variables. Either open a new terminal source the rc file\n")

  if repo == "platform":
    success = install_platform(install_dir, operating_system)

  if repo == "examples":
    success = install_examples(install_dir, operating_system)

  # go back to the directory we have started in
  os.chdir(install_dir)

  return success

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("Missing repository argument.")
    print_usage(sys.argv[0])
    sys.exit(1)

  # check what operating system we are running on
  # for now we only support Mac and Linux
  operating_system = OperatingSystem.Linux if os.name == "posix" and sys.platform == "linux" else None
  operating_system = OperatingSystem.MacOS if os.name == "posix" and sys.platform == "darwin" else operating_system

  if operating_system is not None:
    repo = sys.argv[1]
    success = main(repo, operating_system)
  else:
    print("fUnsupported operating system {sys.platform}")
    success = False

  if success:
    print(f"Installing the repo {repo} succeeded")
    sys.exit(0)
  else:
    print(f"Installing the repo {repo} failed")
    sys.exit(1)

