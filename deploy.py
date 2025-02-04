# deploy.py

import os
import subprocess
import sys
import logging
from typing import Optional
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
        logging.info(f"Command executed successfully")
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        logging.error(f"STDOUT: {e.stdout}")
        logging.error(f"STDERR: {e.stderr}")
        raise

def check_dependency(command: str, install_command: list, package_name: str) -> None:
    """
    Check if a dependency is installed, and install it if not.
    
    Args:
        command (str): Command to check if the dependency is installed
        install_command (list): Command to install the dependency
        package_name (str): Name of the dependency for logging purposes
    """
    try:
        logging.info(f"Checking if {package_name} is installed...")
        subprocess.run(command, check=True)
        logging.info(f"{package_name} is already installed.")
    except subprocess.CalledProcessError:
        logging.info(f"{package_name} is not installed. Installing {package_name}...")
        run_command(install_command)
        logging.info(f"{package_name} installed successfully.")

def install_nodejs(version: str) -> None:
    """Install specific Node.js version using nodesource."""
    try:
        logging.info(f"Installing Node.js version {version}...")
        run_command(["curl", "-fsSL", f"https://deb.nodesource.com/setup_{version}.x", "-o", "nodesource_setup.sh"])
        run_command(["sudo", "bash", "nodesource_setup.sh"])
        run_command(["sudo", "apt-get", "install", "-y", "nodejs"])
        logging.info("Node.js installed successfully")
    except Exception as e:
        logging.error(f"Node.js installation failed: {e}")
        raise

def clone_repository(repo_url: str, project_dir: str) -> None:
    """Clone git repository with error handling."""
    try:
        logging.info(f"Cloning repository from {repo_url} to {project_dir}...")
        run_command(["git", "clone", repo_url, project_dir])
        logging.info("Repository cloned successfully")
    except Exception as e:
        logging.error(f"Repository cloning failed: {e}")
        raise

def setup_project(project_dir: str) -> None:
    """Setup project dependencies and build."""
    try:
        logging.info(f"Setting up project in {project_dir}...")
        run_command(["npm", "ci"], cwd=project_dir)  # Use npm ci for more reliable dependency installation
        run_command([config.NEXT_BUILD_COMMAND], cwd=project_dir)
        logging.info("Project setup completed successfully")
    except Exception as e:
        logging.error(f"Project setup failed: {e}")
        raise

def start_application_with_pm2(project_dir: str, app_name: str) -> None:
    """Start NextJS application using PM2."""
    try:
        logging.info(f"Starting application in {project_dir} using PM2...")
        run_command(["pm2", "start", config.NEXT_START_COMMAND, "--name", app_name], cwd=project_dir)
        logging.info("Application started successfully with PM2")
    except Exception as e:
        logging.error(f"Application startup failed: {e}")
        raise

def configure_pm2_startup(username: str) -> None:
    """Configure PM2 to start on system boot."""
    try:
        run_command(["pm2", "startup"])
        run_command([
            "sudo", "env", f"PATH={os.environ['PATH']}", 
            "pm2", "startup", "systemd", 
            "-u", username, 
            "--hp", os.path.expanduser("~")
        ])
        run_command(["pm2", "save"])
        logging.info("PM2 startup configuration completed")
    except Exception as e:
        logging.error(f"PM2 startup configuration failed: {e}")
        raise

def cleanup() -> None:
    """Perform cleanup tasks after deployment."""
    try:
        # Remove temporary setup files if needed
        if os.path.exists("nodesource_setup.sh"):
            os.remove("nodesource_setup.sh")
        logging.info("Cleanup completed")
    except Exception as e:
        logging.error(f"Cleanup failed: {e}")

def main():
    try:
        # Check and install dependencies
        check_dependency(["npm", "-v"], ["sudo", "apt-get", "install", "-y", "npm"], "npm")
        check_dependency(["git", "--version"], ["sudo", "apt-get", "install", "-y", "git"], "git")
        check_dependency(["pm2", "-v"], ["npm", "install", "-g", "pm2"], "pm2")

        install_nodejs(config.NODE_VERSION)
        clone_repository(config.GITHUB_REPO_URL, config.PROJECT_DIR)
        setup_project(config.PROJECT_DIR)
        start_application_with_pm2(config.PROJECT_DIR, config.PM2_APP_NAME)
        configure_pm2_startup(os.getlogin())
        cleanup()
        logging.info("Deployment completed successfully!")
    except Exception as e:
        logging.error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
