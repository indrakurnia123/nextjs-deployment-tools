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

def run_command(command: list, cwd: Optional[str] = None, check: bool = True) -> subprocess.CompletedProcess:
    """
    Wrapper function to run shell commands with improved error handling and logging.
    
    Args:
        command (list): Command to execute
        cwd (Optional[str]): Working directory for the command
        check (bool): Whether to raise an exception on command failure
    
    Returns:
        subprocess.CompletedProcess: Result of the command execution
    """
    try:
        logging.info(f"Executing command: {' '.join(command)}")
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            cwd=cwd, 
            check=check
        )
        logging.info("Command executed successfully")
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        logging.error(f"STDOUT: {e.stdout}")
        logging.error(f"STDERR: {e.stderr}")
        raise

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

def clone_repository(repo_url: str, project_dir: str) -> None:
    """
    Clone git repository with error handling.
    
    Args:
        repo_url (str): URL of the git repository
        project_dir (str): Directory to clone the repository into
    """
    # Ensure project directory exists
    os.makedirs(project_dir, exist_ok=True)

    logging.info(f"Cloning repository from {repo_url} to {project_dir}...")
    try:
        # Check if directory is empty or new
        if not os.listdir(project_dir):
            run_command(["git", "clone", repo_url, project_dir])
            logging.info("Repository cloned successfully")
        else:
            # If directory is not empty, perform a git pull
            run_command(["git", "pull"], cwd=project_dir)
            logging.info("Repository updated successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"Repository operation failed: {e}")
        raise

def setup_project(project_dir: str) -> None:
    """
    Setup project dependencies and build.
    
    Args:
        project_dir (str): Directory of the project
    """
    logging.info(f"Setting up project in {project_dir}...")
    
    # Check for package-lock.json to determine installation method
    if os.path.exists(os.path.join(project_dir, 'package-lock.json')):
        run_command(["npm", "ci"], cwd=project_dir)
    else:
        run_command(["npm", "install"], cwd=project_dir)
    
    # Build the project
    run_command([config.NEXT_BUILD_COMMAND], cwd=project_dir)
    logging.info("Project setup completed successfully")

def start_application_with_pm2(project_dir: str, app_name: str) -> None:
    """
    Start NextJS application using PM2.
    
    Args:
        project_dir (str): Directory of the project
        app_name (str): Name to give the PM2 process
    """
    logging.info(f"Starting application in {project_dir} using PM2...")
    
    # Stop existing PM2 process if it exists
    try:
        run_command(["pm2", "delete", app_name], check=False)
    except subprocess.CalledProcessError:
        # Ignore error if process doesn't exist
        pass

    # Start new PM2 process
    run_command([
        "pm2", "start", 
        config.NEXT_START_COMMAND, 
        "--name", app_name
    ], cwd=project_dir)
    
    logging.info("Application started successfully with PM2")

def configure_pm2_startup(username: str) -> None:
    """
    Configure PM2 to start on system boot.
    
    Args:
        username (str): Username to configure startup for
    """
    try:
        # Generate startup script
        run_command(["pm2", "startup"])
        
        # Configure startup for specific user
        run_command([
            "sudo", "env", f"PATH={os.environ['PATH']}", 
            "pm2", "startup", "systemd", 
            "-u", username, 
            "--hp", os.path.expanduser("~")
        ])
        
        # Save current PM2 process list
        run_command(["pm2", "save"])
        
        logging.info("PM2 startup configuration completed")
    except subprocess.CalledProcessError as e:
        logging.error(f"PM2 startup configuration failed: {e}")
        raise

def cleanup() -> None:
    """Perform cleanup tasks after deployment."""
    try:
        # Remove any temporary files
        temp_files = ["nodesource_setup.sh"]
        for file in temp_files:
            if os.path.exists(file):
                os.remove(file)
        
        logging.info("Cleanup completed")
    except Exception as e:
        logging.error(f"Cleanup failed: {e}")

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

        # Clone or update repository
        clone_repository(config.GITHUB_REPO_URL, config.PROJECT_DIR)

        # Setup project dependencies and build
        setup_project(config.PROJECT_DIR)

        # Start application with PM2
        start_application_with_pm2(config.PROJECT_DIR, config.PM2_APP_NAME)

        # Configure PM2 startup
        configure_pm2_startup(os.getlogin())

        # Final cleanup
        cleanup()

        logging.info("Deployment completed successfully!")
    except Exception as e:
        logging.error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()