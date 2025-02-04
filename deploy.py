import os
import subprocess
import sys
import logging
import shutil
from typing import Optional, List

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def find_executable(executable: str) -> Optional[str]:
    """
    Find the full path of an executable using shutil.which.
    
    Args:
        executable (str): Name of the executable to find
    
    Returns:
        Optional[str]: Full path of the executable or None if not found
    """
    return shutil.which(executable)

def install_system_dependencies(dependencies: List[str]) -> None:
    """
    Install system-level dependencies using apt-get.
    
    Args:
        dependencies (List[str]): List of dependencies to install
    """
    missing_deps = [dep for dep in dependencies if not find_executable(dep)]
    
    if missing_deps:
        logging.info(f"Installing missing system dependencies: {missing_deps}")
        update_cmd = ["sudo", "apt-get", "update"]
        install_cmd = ["sudo", "apt-get", "install", "-y"] + missing_deps
        
        try:
            subprocess.run(update_cmd, check=True)
            subprocess.run(install_cmd, check=True)
            logging.info("System dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install system dependencies: {e}")
            raise

def install_nodejs(version: str) -> None:
    """
    Install Node.js using nodesource repository.
    
    Args:
        version (str): Node.js version to install
    """
    # Check if Node.js is already installed
    if find_executable("node"):
        logging.info("Node.js is already installed")
        return

    logging.info(f"Installing Node.js version {version}...")
    try:
        # Download nodesource setup script
        subprocess.run([
            "curl", "-fsSL", 
            f"https://deb.nodesource.com/setup_{version}.x", 
            "-o", "nodesource_setup.sh"
        ], check=True)

        # Run setup script
        subprocess.run(["sudo", "bash", "nodesource_setup.sh"], check=True)

        # Install Node.js and npm
        subprocess.run(["sudo", "apt-get", "install", "-y", "nodejs"], check=True)

        logging.info("Node.js and npm installed successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"Node.js installation failed: {e}")
        raise
    finally:
        # Clean up setup script
        if os.path.exists("nodesource_setup.sh"):
            os.remove("nodesource_setup.sh")

def install_npm_global_packages(packages: List[str]) -> None:
    """
    Install global npm packages.
    
    Args:
        packages (List[str]): List of global npm packages to install
    """
    if not find_executable("npm"):
        logging.error("npm is not installed. Cannot install global packages.")
        return

    for package in packages:
        if not find_executable(package):
            try:
                logging.info(f"Installing global npm package: {package}")
                subprocess.run(["npm", "install", "-g", package], check=True)
                logging.info(f"{package} installed successfully")
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to install {package}: {e}")

def main():
    try:
        # Install system dependencies
        install_system_dependencies([
            "git", "curl", "software-properties-common"
        ])

        # Install Node.js
        install_nodejs(config.NODE_VERSION)

        # Install global npm packages
        install_npm_global_packages(["pm2"])

        # Clone repository
        clone_repository(config.GITHUB_REPO_URL, config.PROJECT_DIR)

        # Setup project
        setup_project(config.PROJECT_DIR)

        # Start application with PM2
        start_application_with_pm2(config.PROJECT_DIR, config.PM2_APP_NAME)

        # Configure PM2 startup
        configure_pm2_startup(os.getlogin())

        logging.info("Deployment completed successfully!")
    except Exception as e:
        logging.error(f"Deployment failed: {e}")
        sys.exit(1)

# Rest of the script remains the same as in the previous version
# (functions like clone_repository, setup_project, etc.)

if __name__ == "__main__":
    main()