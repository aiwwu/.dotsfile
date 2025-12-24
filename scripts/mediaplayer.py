#!/usr/bin/env python3
"""
Waybar Media Player Module
Hiển thị thông tin trình phát nhạc hiện tại với hỗ trợ nhiều player
"""

import json
import subprocess
import sys
import os
from typing import Optional, Dict, List

class MediaPlayer:
    def __init__(self):
        self.player_icons = {
            "spotify": "",
            "chromium": "",
            "firefox": "",
            "vlc": "",
            "mpv": "🎞",
            "rhythmbox": "",
            "clementine": "",
            "amarok": "",
            "audacious": "",
            "deadbeef": "",
            "cmus": "",
            "moc": "",
            "brave": "",
            "opera": "",
            "discord": "󰙯",
            "telegram": "",
            "default": "󰽴"
        }
        
        self.status_icons = {
            "playing": "",
            "paused": "",
            "stopped": ""
        }
        
        self.source_icons = {
            "youtube.com": "YouTube",
            "youtu.be": "YouTube", 
            "soundcloud.com": "SoundCloud",
            "zingmp3.vn": "Zing MP3",
            "nhaccuatui.com": "NCT",
            "open.spotify.com": "Spotify Web",
            "music.apple.com": "Apple Music",
            "tidal.com": "Tidal",
            "deezer.com": "Deezer"
        }

    def run_command(self, cmd: List[str]) -> Optional[str]:
        """Chạy lệnh shell và trả về kết quả"""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            return None

    def get_all_players(self) -> List[str]:
        """Lấy danh sách tất cả trình phát"""
        players_output = self.run_command(["playerctl", "--list-all"])
        if players_output:
            return [p.strip() for p in players_output.split('\n') if p.strip()]
        return []

    def get_active_player(self) -> Optional[str]:
        """Tìm trình phát đang hoạt động (ưu tiên playing, sau đó paused)"""
        players = self.get_all_players()
        if not players:
            return None

        # Ưu tiên trình phát đang playing
        for player in players:
            status = self.run_command(["playerctl", "--player", player, "status"])
            if status and status.lower() == "playing":
                return player
        
        # Nếu không có playing, lấy paused
        for player in players:
            status = self.run_command(["playerctl", "--player", player, "status"])
            if status and status.lower() == "paused":
                return player
                
        # Trả về player đầu tiên nếu có
        return players[0] if players else None

    def get_metadata(self, player: Optional[str] = None) -> Dict[str, Optional[str]]:
        """Lấy metadata từ trình phát"""
        base_cmd = ["playerctl"]
        if player:
            base_cmd.extend(["--player", player])

        metadata = {
            "artist": self.run_command(base_cmd + ["metadata", "xesam:artist"]),
            "title": self.run_command(base_cmd + ["metadata", "xesam:title"]),
            "album": self.run_command(base_cmd + ["metadata", "xesam:album"]),
            "status": self.run_command(base_cmd + ["status"]),
            "url": self.run_command(base_cmd + ["metadata", "xesam:url"]),
            "identity": self.run_command(base_cmd + ["metadata", "mpris:identity"]) or player or "Unknown"
        }
        
        return metadata

    def get_source_from_url(self, url: Optional[str]) -> Optional[str]:
        """Xác định nguồn phát từ URL"""
        if not url:
            return None
            
        for domain, icon in self.source_icons.items():
            if domain in url:
                return icon
        return None

    def get_player_icon(self, identity: str, url: Optional[str] = None) -> str:
        """Lấy icon cho trình phát"""
        # Kiểm tra nguồn từ URL trước
        source_icon = self.get_source_from_url(url)
        if source_icon and any(browser in identity.lower() for browser in ["firefox", "chromium", "brave", "opera"]):
            return source_icon
            
        # Tìm icon dựa trên tên trình phát
        identity_lower = identity.lower()
        for key, icon in self.player_icons.items():
            if key in identity_lower:
                return icon
                
        return self.player_icons["default"]

    def format_text(self, metadata: Dict[str, Optional[str]]) -> tuple[str, str]:
        """Format text hiển thị và tooltip"""
        artist = metadata.get("artist")
        title = metadata.get("title")
        album = metadata.get("album")
        identity = metadata.get("identity", "Unknown")
        status = metadata.get("status", "stopped")
        url = metadata.get("url")

        # Icon trạng thái và trình phát
        status_icon = self.status_icons.get(status.lower() if status else "stopped", "")
        player_icon = self.get_player_icon(identity, url)

        # Tạo text hiển thị
        if artist and title:
            text = f"{status_icon} {player_icon} {artist} - {title}"
            tooltip_parts = [f"{identity}"]
            if album:
                tooltip_parts.append(f"Album: {album}")
            tooltip_parts.append(f"{artist} - {title}")
            tooltip = "\n".join(tooltip_parts)
        elif title:
            text = f"{status_icon} {player_icon} {title}"
            tooltip = f"{identity}\n{title}"
        else:
            text = "󰝛 No media"
            tooltip = "No media playing"

        return text, tooltip

    def get_waybar_output(self) -> Dict:
        """Tạo output JSON cho Waybar"""
        active_player = self.get_active_player()
        
        if not active_player:
            # Thử lấy metadata từ player mặc định
            metadata = self.get_metadata()
            if not any(metadata.values()):
                return {
                    "text": "󰝛 No media",
                    "class": "stopped",
                    "alt": "none",
                    "tooltip": "No media playing"
                }
        else:
            metadata = self.get_metadata(active_player)

        text, tooltip = self.format_text(metadata)
        status = metadata.get("status", "stopped").lower()

        return {
            "text": text,
            "class": status,
            "alt": metadata.get("identity", "none"),
            "tooltip": tooltip
        }

def main():
    """Main function"""
    try:
        # Kiểm tra playerctl có tồn tại không
        if not subprocess.run(["which", "playerctl"], capture_output=True).returncode == 0:
            print(json.dumps({
                "text": "󰝛 playerctl not found",
                "class": "error",
                "alt": "error",
                "tooltip": "playerctl is not installed"
            }))
            return
            
        player = MediaPlayer()
        output = player.get_waybar_output()
        print(json.dumps(output, ensure_ascii=False))
        
    except Exception as e:
        # Fallback output nếu có lỗi
        print(json.dumps({
            "text": "󰝛 Error",
            "class": "error", 
            "alt": "error",
            "tooltip": f"Error: {str(e)}"
        }))

if __name__ == "__main__":
    main()