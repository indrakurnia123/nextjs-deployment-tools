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

## Prerequisites

Before running the script, ensure you have the following:

- An Ubuntu server (or any compatible Linux distribution).
- Python 3 installed on your server.
- Access to the terminal with sudo privileges.

## Getting Started

Follow these steps to deploy your Next.js application:

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:indrakurnia123/nextjs-deployment-tools.git
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

### Explanation of the README Structure

1. **Title and Logo**: The title clearly states the purpose of the repository, and the logo adds a visual element.
  
2. **Overview**: A brief introduction that explains what the script does and who it is for.

3. **Features**: A bullet-point list of the main features of the script, making it easy for users to understand its capabilities.

4. **Prerequisites**: A clear list of what users need before they can use the script.

5. **Getting Started**: Step-by-step instructions on how to clone the repository, configure settings, run the script, and access the application.

6. **Contributing**: Encouragement for others to contribute to the project, fostering community involvement.

7. **License**: Information about the project's license, which is important for open-source projects.

8. **Acknowledgments**: Acknowledging the technologies used in the project.

### Final Touches

- Make sure to replace `yourusername` and `username/repository.git` with your actual GitHub username and repository name.
- You can also add any additional sections that you think might be helpful, such as FAQs or troubleshooting tips
