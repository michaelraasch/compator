#!/bin/bash

# Detect the OS
OS=$(uname -s)

# Determine the correct rc file
if [[ -n "$ZSH_VERSION" ]]; then
  RC_FILE=".zshrc"
else
  RC_FILE=".bashrc"
fi

# Explicitly source the rc file
source ~/$RC_FILE

# Install nvm
if [[ "$OS" == "Darwin" ]]; then
  brew install nvm
elif [[ "$OS" == "Linux" ]]; then
  sudo apt -y update
  sudo apt -y install zip iptables-persistent
  # Check if nvm is already installed
  if [[ ! -d "NVM_DIR" ]]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
  else
    echo "nvm is already installed."
    source $NVM_DIR/nvm.sh
  fi  
fi

# Source the rc file to apply changes
source ~/$RC_FILE

# Install Node.js
nvm install v20.18.1

# Step 4: Install yarn
npm install -g yarn

# Install SDKMAN!
# Check if SDKMAN! is already installed 
if [[ ! -d "$SDKMAN_DIR" ]]; then
  curl -s "https://get.sdkman.io" | bash
else
  echo "SDKMAN! is already installed."
  source $SDKMAN_DIR/bin/sdkman-init.sh
fi

# Source the rc file to apply changes
source ~/$RC_FILE

# Install Java
sdk install java 21.0.5-tem

# Source the rc file to apply changes
source ~/$RC_FILE

# Install Gradle
sdk install gradle

echo "Installation complete!"
