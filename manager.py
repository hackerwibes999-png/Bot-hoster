import os
import subprocess
import shutil
import zipfile
import json
import time
import re
from pathlib import Path
from typing import Tuple, Optional
import uuid

from config import BOTS_DIR, LOGS_DIR

class BotManager:
    def __init__(self):
        self.bots_dir = BOTS_DIR
        self.logs_dir = LOGS_DIR
        
    def extract_and_prepare(self, file_path: str, bot_id: str) -> Tuple[bool, str, str]:
        """
        Extract uploaded file and prepare bot environment
        Returns: (success, bot_type, main_file_path)
        """
        bot_folder = os.path.join(self.bots_dir, bot_id)
        os.makedirs(bot_folder, exist_ok=True)
        
        # Copy file to bot folder
        file_name = os.path.basename(file_path)
        dest_file = os.path.join(bot_folder, file_name)
        shutil.copy2(file_path, dest_file)
        
        # Detect file type and extract
        if file_name.endswith('.zip'):
            try:
                with zipfile.ZipFile(dest_file, 'r') as zip_ref:
                    zip_ref.extractall(bot_folder)
                os.remove(dest_file)
            except Exception as e:
                return False, "", f"Failed to extract zip: {str(e)}"
        
        # Detect main file
        main_file = self._detect_main_file(bot_folder)
        if not main_file:
            return False, "", "No main file found (bot.py, main.py, bot.js, index.js)"
        
        # Detect bot type
        bot_type = 'python' if main_file.endswith('.py') else 'nodejs'
        
        # Install dependencies
        success, error = self._install_dependencies(bot_folder, bot_type)
        if not success:
            return False, "", f"Failed to install dependencies: {error}"
        
        return True, bot_type, main_file
    
    def _detect_main_file(self, folder: str) -> Optional[str]:
        """Detect main bot file"""
        possible_files = ['bot.py', 'main.py', 'bot.js', 'index.js', 'app.js']
        
        for file in possible_files:
            file_path = os.path.join(folder, file)
            if os.path.isfile(file_path):
                return file_path
        
        # Check for any .py or .js file in root
        for file in os.listdir(folder):
            if file.endswith('.py') or file.endswith('.js'):
                return os.path.join(folder, file)
        
        return None
    
    def _install_dependencies(self, folder: str, bot_type: str) -> Tuple[bool, str]:
        """Install dependencies for the bot"""
        try:
            if bot_type == 'python':
                req_file = os.path.join(folder, 'requirements.txt')
                if os.path.isfile(req_file):
                    result = subprocess.run(
                        ['pip', 'install', '-r', req_file],
                        cwd=folder,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if result.returncode != 0:
                        return False, result.stderr
                    
                # Check if python-telegram-bot is installed
                try:
                    subprocess.run(['pip', 'show', 'python-telegram-bot'], 
                                 capture_output=True, check=True)
                except subprocess.CalledProcessError:
                    # Install python-telegram-bot if not present
                    subprocess.run(['pip', 'install', 'python-telegram-bot'], 
                                 cwd=folder, capture_output=True, timeout=60)
                
            elif bot_type == 'nodejs':
                package_file = os.path.join(folder, 'package.json')
                if not os.path.isfile(package_file):
                    # Create minimal package.json
                    package_data = {
                        "name": "telegram-bot",
                        "version": "1.0.0",
                        "dependencies": {
                            "node-telegram-bot-api": "^0.61.0"
                        }
                    }
                    with open(package_file, 'w') as f:
                        json.dump(package_data, f, indent=2)
                
                # Install npm dependencies
                result = subprocess.run(
                    ['npm', 'install', '--production'],
                    cwd=folder,
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                if result.returncode != 0:
                    return False, result.stderr
            
            return True, ""
            
        except subprocess.TimeoutExpired:
            return False, "Dependency installation timed out"
        except Exception as e:
            return False, str(e)
    
    def start_bot(self, bot_id: str, bot_type: str, main_file: str, bot_token: str) -> Tuple[bool, str, str]:
        """
        Start the bot using pm2
        Returns: (success, process_id, error_message)
        """
        bot_folder = os.path.join(self.bots_dir, bot_id)
        log_file = os.path.join(self.logs_dir, f"{bot_id}.log")
        
        # Set environment variable for bot token
        env = os.environ.copy()
        env['BOT_TOKEN'] = bot_token
        
        # Build pm2 start command
        if bot_type == 'python':
            cmd = ['pm2', 'start', main_file, '--name', bot_id, '--interpreter', 'python3']
        else:  # nodejs
            cmd = ['pm2', 'start', main_file, '--name', bot_id]
        
        try:
            # Start with pm2
            result = subprocess.run(
                cmd,
                cwd=bot_folder,
                env=env,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return False, "", result.stderr
            
            # Get process ID
            process_id = self._get_pm2_process_id(bot_id)
            if not process_id:
                return False, "", "Failed to get process ID"
            
            return True, process_id, ""
            
        except subprocess.TimeoutExpired:
            return False, "", "Startup timed out"
        except Exception as e:
            return False, "", str(e)
    
    def _get_pm2_process_id(self, bot_id: str) -> Optional[str]:
        """Get pm2 process ID for bot"""
        try:
            result = subprocess.run(
                ['pm2', 'jlist'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                processes = json.loads(result.stdout)
                for proc in processes:
                    if proc.get('name') == bot_id:
                        return str(proc.get('pm_id'))
            return None
        except:
            return None
    
    def stop_bot(self, bot_id: str) -> Tuple[bool, str]:
        """Stop the bot"""
        try:
            result = subprocess.run(
                ['pm2', 'stop', bot_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                return False, result.stderr
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def restart_bot(self, bot_id: str) -> Tuple[bool, str]:
        """Restart the bot"""
        try:
            result = subprocess.run(
                ['pm2', 'restart', bot_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                return False, result.stderr
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def delete_bot(self, bot_id: str) -> Tuple[bool, str]:
        """Delete bot from pm2 and filesystem"""
        try:
            # Stop and delete from pm2
            subprocess.run(['pm2', 'delete', bot_id], capture_output=True, timeout=10)
            
            # Delete bot folder
            bot_folder = os.path.join(self.bots_dir, bot_id)
            if os.path.exists(bot_folder):
                shutil.rmtree(bot_folder)
            
            # Delete log file
            log_file = os.path.join(self.logs_dir, f"{bot_id}.log")
            if os.path.exists(log_file):
                os.remove(log_file)
            
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def get_logs(self, bot_id: str, lines: int = 50) -> str:
        """Get bot logs"""
        log_file = os.path.join(self.logs_dir, f"{bot_id}.log")
        if not os.path.exists(log_file):
            return "No logs found"
        
        try:
            result = subprocess.run(
                ['tail', '-n', str(lines), log_file],
                capture_output=True,
                text=True
            )
            return result.stdout or "No logs available"
        except:
            return "Error reading logs"
    
    def get_bot_status(self, bot_id: str) -> str:
        """Get bot status from pm2"""
        try:
            result = subprocess.run(
                ['pm2', 'jlist'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                processes = json.loads(result.stdout)
                for proc in processes:
                    if proc.get('name') == bot_id:
                        return proc.get('pm2_env', {}).get('status', 'unknown')
            return 'stopped'
        except:
            return 'unknown'
    
    def verify_bot_token(self, bot_token: str) -> Tuple[bool, str]:
        """
        Verify if a bot token is valid by making a test request
        Returns: (is_valid, bot_username)
        """
        import requests
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return True, data.get('result', {}).get('username', 'Unknown')
            return False, ""
        except:
            return False, ""
