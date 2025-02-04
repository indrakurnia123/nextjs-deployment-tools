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
        logging.info("Command executed successfully")
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        logging.error(f"STDOUT: {e.stdout}")
        logging.error(f"STDERR: {e.stderr}")
        raise

def check_dependency(command: list, name: str) -> bool:
    """Check if a command is available on the system."""
    try:
        run_command(command)
        logging.info(f"{name} is already installed.")
        return True
    except subprocess.CalledProcessError:
        logging.error(f"{name} is not installed.")
        return False

def install_git() -> None:
    """Install Git if it is not already installed."""
    if not check_dependency(["git", "--version"], "Git"):
        logging.info("Installing Git...")
        run_command(["sudo", "apt-get", "install", "-y", "git"])
        logging.info("Git installed successfully.")

def install_nodejs(version: str) -> None:
    """Install specific Node.js version using nodesource."""
    logging.info(f"Installing Node.js version {version}...")
    run_command(["curl", "-fsSL", f"https://deb.nodesource.com/setup_{version}.x", "-o", "nodesource_setup.sh"])
    run_command(["sudo", "bash", "nodesource_setup.sh"])
    run_command(["sudo", "apt-get", "install", "-y", "nodejs"])
    logging.info("Node.js installed successfully.")

def install_pm2() -> None:
    """Install PM2 process manager globally."""
    if not check_dependency(["npm", "-v"], "NPM"):
        logging.error("NPM is required to install PM2. Please install NPM and try again.")
        sys.exit(1)

    if not check_dependency(["pm2", "-v"], "PM2"):
        logging.info("Installing PM2...")
        run_command(["npm", "install", "-g", "pm2"])
        logging.info("PM2 installed successfully.")

def clone_repository(repo_url: str, project_dir: str) -> None:
    """Clone git repository with error handling."""
    logging.info(f"Cloning repository from {repo_url} to {project_dir}...")
    run_command(["git", "clone", repo_url, project_dir])
    logging.info("Repository cloned successfully")

def setup_project(project_dir: str) -> None:
    """Setup project dependencies and build."""
    logging.info(f"Setting up project in {project_dir}...")
    if os.path.exists(os.path.join(project_dir, 'package-lock.json')):
        run_command(["npm", "ci"], cwd=project_dir)  # Use npm ci for more reliable dependency installation
    else:
        run_command(["npm", "install"], cwd=project_dir)  # Fallback to npm install if no lock file
    run_command([config.NEXT_BUILD_COMMAND], cwd=project_dir)
    logging.info("Project setup completed successfully")

def configure_pm2_startup(username: str) -> None:
    """Configure PM2 to start on system boot."""
    run_command(["pm2", "startup"])
    run_command([
        "sudo", "env", f"PATH={os.environ['PATH']}", 
        "pm2", "startup", "systemd", 
        "-u", username, 
        "--hp", os.path.expanduser("~")
    ])
    run_command(["pm2", "save"])
    logging.info("PM2 startup configuration completed")

def start_application_with_pm2(project_dir: str, app_name: str) -> None:
    """Start NextJS application using PM2."""
    logging.info(f"Starting application in {project_dir} using PM2...")
    run_command(["pm2", "start", config.NEXT_START_COMMAND, "--name", app_name], cwd=project_dir)
    logging.info("Application started successfully with PM2")

def cleanup() -> None:
    """Perform cleanup tasks after deployment."""
    try:
        if os.path.exists("nodesource_setup.sh"):
            os.remove("nodesource_setup.sh")
        logging.info("Cleanup completed")
    except Exception as e:
        logging.error(f"Cleanup failed: {e}")

def main():
    try:
        install_git()
        install_nodejs(config.NODE_VERSION)
        install_pm2()
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
