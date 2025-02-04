Tentu, saya akan melakukan optimasi pada `deploy.py` untuk menambahkan pengecekan dependency sebelum melakukan instalasi. Kode ini akan memeriksa apakah `npm`, `git`, dan `pm2` sudah terinstal, dan jika belum, akan menginstalnya. Selain itu, semua proses akan dilogkan dengan rapi.

Berikut adalah versi diperbarui dari `deploy.py`:

### deploy.py

```python
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
```

### Penjelasan Perubahan

1. **Fungsi `check_dependency`**:
   - Fungsi ini memeriksa apakah suatu dependensi (misalnya `npm`, `git`, atau `pm2`) sudah terinstal. Jika belum, fungsi ini akan menginstalnya.
   - Fungsi ini digunakan untuk memeriksa dan menginstal `npm`, `git`, dan `pm2`.

2. **Pengecekan Dependency**:
   - Sebelum menjalankan proses deployment, skrip akan memeriksa apakah `npm`, `git`, dan `pm2` sudah terinstal. Jika belum, skrip akan menginstalnya.

3. **Logging**:
   - Semua proses pengecekan dan instalasi dependensi akan dilogkan dengan rapi, sehingga Anda dapat melacak apa yang telah dilakukan oleh skrip.

### Deskripsi Singkat untuk GitHub

**"Automate Next.js deployment on Ubuntu with Node.js and PM2, including dependency checks and installation."**

### README.md

Berikut adalah versi diperbarui dari `README.md` dengan penjelasan tentang pengecekan dan instalasi dependensi:

```markdown
# Next.js Deployment Script

![Next.js Logo](https://nextjs.org/static/favicon/favicon.ico)

## Overview

The **Next.js Deployment Script** is a simple and efficient way to deploy your Next.js applications on Ubuntu servers. This script automates the entire deployment process, from installing Node.js and cloning your GitHub repository to setting up your application with PM2 for process management. Whether you're a beginner or an experienced developer, this script will help you get your Next.js application up and running in no time!

## Features

- **Automated Installation**: Installs the specified version of Node.js and PM2 automatically.
- **Repository Cloning**: Clones your Next.js project from GitHub to your server.
- **Dependency Management**: Installs all necessary dependencies using `npm ci` for reliable installations.
- **Build and Start**: Builds your Next.js application and starts it using PM2, ensuring it runs in the background.
- **Startup Configuration**: Configures PM2 to automatically start your application on system boot.
- **Logging**: Provides detailed logs of the deployment process for easy troubleshooting.
- **Dependency Checks**: Checks for and installs necessary dependencies (`npm`, `git`, `pm2`) if they are not already installed.

## Prerequisites

Before running the script, ensure you have the following:

- An Ubuntu server (or any compatible Linux distribution).
- Python 3 installed on your server.
- Access to the terminal with sudo privileges.

## Getting Started

Follow these steps to deploy your Next.js application:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/nextjs-deployment-script.git
   cd nextjs-deployment-script
   ```

2. **Configure Your Settings**:
   Open the `config.py` file and update the following parameters:
   ```python
   NODE_VERSION = "16.14.0"  # Specify the Node.js version
   GITHUB_REPO_URL = "https://github.com/username/repository.git"  # Your GitHub repository URL
   PROJECT_DIR = "/path/to/your/project"  # Directory where the project will be cloned
   NEXT_BUILD_COMMAND = "npm run build"  # Command to build your Next.js app
   NEXT_START_COMMAND = "npm run start"  # Command to start your Next.js app
   PM2_APP_NAME = "nextjs-app"  # Name for your PM2 application
   ```

3. **Run the Deployment Script**:
   Execute the following command to start the deployment process:
   ```bash
   python deploy.py
   ```

4. **Access Your Application**:
   Once the deployment is complete, your Next.js application will be running in the background. You can access it via your server's IP address or domain name.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Next.js](https://nextjs.org/) - The React framework for production.
- [PM2](https://pm2.keymetrics.io/) - Advanced, production process manager for Node.js.

---

Happy coding! If you have any questions or need assistance, feel free to reach out.