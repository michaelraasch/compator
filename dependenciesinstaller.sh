#!/usr/bin/env bash

# Function to parse a file and execute lines containing a specific string
# For some reason sourcing the rc file does not work, so we parse it and execute the correct lines manually
execute_matching_lines() {
  local file="$1"
  local search_string="$2"

  if [[ ! -f "$file" ]]; then
    echo "Error: File '$file' not found."
    return 1
  fi

  while IFS= read -r line; do
    if [[ "$line" == *"$search_string"* ]]; then
      eval "$line"
    fi
  done < "$file"
}

# Detect the OS
OS=$(uname -s)

# Determine the correct rc file
if [[ -n "$ZSH_VERSION" ]] || [[ "$SHELL" == "/bin/zsh" ]]; then
  RC_FILE=".zshrc"
else
  RC_FILE=".bashrc"
fi

if [[ "$OS" == "Linux" ]]; then
  sudo apt -y update
  sudo apt -y install zip iptables-persistent
fi
# Install nvm

# Check if nvm is already installed
if [[ ! -d "$NVM_DIR" ]]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
else
  echo "nvm is already installed."
fi

# we scan the rc fike for "nvm". Do not change this to ".nvm" or so because it will not work
execute_matching_lines "$HOME/$RC_FILE" "nvm"

# Install Node.js
nvm install v20.18.1

# Install yarn
npm install -g yarn

# Install SDKMAN!
# Check if SDKMAN! is already installed 
if [[ ! -d "$SDKMAN_DIR" ]]; then
  curl -s "https://get.sdkman.io" | bash
else
  echo "SDKMAN! is already installed."
fi

execute_matching_lines "$HOME/$RC_FILE" "sdkman"

# Install Java
sdk install java 21.0.5-tem

# Set JAVA_HOME and add it to RC_FILE
echo "export JAVA_HOME=\"$SDKMAN_DIR/candidates/java/current\"" >> ~/$RC_FILE

# Install Gradle
sdk install gradle

echo -e "Installation complete!\n"
echo -e "run the the following command\n"
echo "source ~/$RC_FILE"
echo -e "\nto finish the proess"
