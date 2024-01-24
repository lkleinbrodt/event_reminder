import requests
from config import Config
from datetime import datetime, timedelta

class RateLimitError(Exception):
    def __init__(self, ip, message="Rate limit exceeded"):
        self.ip = ip
        self.message = message
        super().__init__(self.message)


class TelegramBot:
    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.message_counts = {}
        
        self.window_duration = timedelta(minutes=5)
        
    def send_message(self, message, ip = None):
        
        # Check if the IP is in the dictionary
        if ip is not None:
            if ip in self.message_counts:
                if self.message_counts[ip]["count"] >= 3:
                    block_until = (self.message_counts[ip]["timestamp"] + self.window_duration)
                    current_time = datetime.utcnow()
                    if current_time >= block_until:
                        # Reset attempts after block expires
                        self.message_counts[ip] = {"count": 1, "timestamp": datetime.now()}
                    else:
                        # Rate limit exceeded, don't send the message
                        raise RateLimitError(ip)
                else:
                    self.message_counts[ip]["count"] += 1
                    self.message_counts[ip]["timestamp"] = datetime.utcnow()
            else:
                self.message_counts[ip] = {"count": 1, "timestamp": datetime.now()}
            
        
        
        api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message
        }

        response = requests.post(api_url, data=payload)
        if response.status_code == 200:
            print("Message sent successfully.")
        else:
            print(f"Failed to send message. Status code: {response.status_code}")
            
        

    def send_termination_message(self):
        self.send_message("Site terminated")