#!/usr/bin/env python3
"""
Trading System Log Colorizer
Makes JSON logs more readable with colors and formatting
"""

import json
import sys
import re
from datetime import datetime
from typing import Dict, Any

# ANSI Color Codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'

class LogColorizer:
    def __init__(self):
        self.level_colors = {
            'INFO': Colors.GREEN,
            'WARNING': Colors.YELLOW,
            'ERROR': Colors.RED,
            'DEBUG': Colors.CYAN,
            'CRITICAL': Colors.BG_RED + Colors.WHITE
        }
        
        self.service_colors = {
            'OllamaService': Colors.MAGENTA,
            'trading_system': Colors.BLUE,
            'enhanced_logging': Colors.CYAN
        }
        
        self.symbol_colors = {
            'AAPL': Colors.GREEN,
            'MSFT': Colors.BLUE,
            'GOOGL': Colors.YELLOW,
            'TSLA': Colors.RED,
            'AMZN': Colors.MAGENTA
        }

    def colorize_level(self, level: str) -> str:
        """Colorize log levels"""
        color = self.level_colors.get(level, Colors.WHITE)
        return f"{color}{level}{Colors.RESET}"

    def colorize_service(self, service: str) -> str:
        """Colorize service names"""
        color = self.service_colors.get(service, Colors.WHITE)
        return f"{color}{service}{Colors.RESET}"

    def colorize_symbol(self, text: str) -> str:
        """Colorize stock symbols in text"""
        for symbol, color in self.symbol_colors.items():
            text = re.sub(rf'\b{symbol}\b', f"{color}{symbol}{Colors.RESET}", text)
        return text

    def colorize_message(self, message: str) -> str:
        """Colorize specific patterns in messages"""
        # Colorize trade signals
        message = re.sub(r'(BUY|SELL)', f"{Colors.BOLD}{Colors.GREEN}\\1{Colors.RESET}", message)
        message = re.sub(r'(Approved: True)', f"{Colors.GREEN}\\1{Colors.RESET}", message)
        message = re.sub(r'(Approved: False)', f"{Colors.RED}\\1{Colors.RESET}", message)
        message = re.sub(r'(Confidence: \d+\.\d+)', f"{Colors.YELLOW}\\1{Colors.RESET}", message)
        
        # Colorize symbols
        message = self.colorize_symbol(message)
        
        # Colorize URLs
        message = re.sub(r'(http[s]?://[^\s]+)', f"{Colors.CYAN}\\1{Colors.RESET}", message)
        
        return message

    def format_timestamp(self, timestamp: str) -> str:
        """Format timestamp with color"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return f"{Colors.BLUE}{dt.strftime('%H:%M:%S')}{Colors.RESET}"
        except:
            return timestamp

    def process_line(self, line: str) -> str:
        """Process a single log line"""
        try:
            # Try to parse as JSON
            data = json.loads(line.strip())
            
            # Extract fields
            timestamp = data.get('timestamp', '')
            level = data.get('level', 'INFO')
            message = data.get('message', '')
            logger = data.get('logger', '')
            
            # Format the output
            formatted = (
                f"{self.format_timestamp(timestamp)} "
                f"[{self.colorize_level(level)}] "
                f"[{self.colorize_service(logger)}] "
                f"{self.colorize_message(message)}"
            )
            
            return formatted
            
        except json.JSONDecodeError:
            # Not JSON, return as-is with basic colorization
            return f"{Colors.WHITE}{line.strip()}{Colors.RESET}"
        except Exception as e:
            return f"{Colors.RED}Error processing line: {e}{Colors.RESET}\n{line}"

    def run(self):
        """Main processing loop"""
        for line in sys.stdin:
            formatted = self.process_line(line)
            print(formatted)

def main():
    colorizer = LogColorizer()
    colorizer.run()

if __name__ == "__main__":
    main() 