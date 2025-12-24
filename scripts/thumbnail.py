#!/usr/bin/env python3
"""
Media Thumbnail Generator for Waybar
Tạo thumbnail album art với bo góc tròn và fallback
"""

import subprocess
import os
import sys
from pathlib import Path
from typing import Optional, Tuple
import requests
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    print("", file=sys.stderr)  # Empty output nếu không có PIL
    sys.exit(1)

class ThumbnailGenerator:
    def __init__(self):
        # Cấu hình
        self.bg_color = (0, 0, 0, 0)  # Trong suốt
        self.corner_radius = 15       # Bo góc
        self.frame_size = (128, 128)  # Kích thước cố định
        self.cache_dir = Path.home() / ".cache" / "waybar-media"
        self.output_path = "/tmp/waybar_thumbnail.png"
        
        # Tạo thư mục cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Danh sách fallback paths
        self.fallback_paths = [
            Path.home() / ".cache" / "hyde" / "wall.set",
            Path.home() / ".config" / "hypr" / "wallpaper.jpg",  
            Path.home() / ".config" / "hypr" / "wallpaper.png",
            Path("/usr/share/pixmaps/music.png"),
            Path("/usr/share/icons/hicolor/128x128/apps/multimedia-player.png")
        ]

    def run_command(self, cmd: list) -> Optional[str]:
        """Chạy lệnh shell an toàn"""
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

    def get_art_url(self) -> Optional[str]:
        """Lấy URL album art từ playerctl"""
        return self.run_command(["playerctl", "metadata", "mpris:artUrl"])

    def download_image(self, url: str) -> Optional[Image.Image]:
        """Download ảnh từ URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10, stream=True)
            response.raise_for_status()
            
            # Giới hạn kích thước file (5MB)
            if int(response.headers.get('content-length', 0)) > 5 * 1024 * 1024:
                return None
                
            return Image.open(BytesIO(response.content)).convert("RGBA")
        except (requests.RequestException, OSError, ValueError):
            return None

    def load_local_image(self, path: str) -> Optional[Image.Image]:
        """Load ảnh từ file local"""
        try:
            if path.startswith("file://"):
                path = path[7:]
            
            file_path = Path(path)
            if file_path.exists() and file_path.stat().st_size > 0:
                return Image.open(file_path).convert("RGBA")
            return None
        except (OSError, ValueError):
            return None

    def get_fallback_image(self) -> Optional[Image.Image]:
        """Lấy ảnh fallback"""
        for path in self.fallback_paths:
            if path.exists():
                try:
                    return Image.open(path).convert("RGBA")
                except (OSError, ValueError):
                    continue
        return None

    def create_default_thumbnail(self) -> Image.Image:
        """Tạo thumbnail mặc định với icon âm nhạc"""
        img = Image.new("RGBA", self.frame_size, (50, 50, 50, 255))
        
        # Vẽ icon âm nhạc đơn giản
        draw = ImageDraw.Draw(img)
        center_x, center_y = self.frame_size[0] // 2, self.frame_size[1] // 2
        
        # Vẽ note âm nhạc
        draw.ellipse([center_x-20, center_y+5, center_x-10, center_y+15], fill=(200, 200, 200, 255))
        draw.rectangle([center_x-12, center_y-15, center_x-10, center_y+10], fill=(200, 200, 200, 255))
        draw.ellipse([center_x+5, center_y, center_x+15, center_y+10], fill=(200, 200, 200, 255))
        draw.rectangle([center_x+13, center_y-20, center_x+15, center_y+5], fill=(200, 200, 200, 255))
        
        return img

    def resize_and_crop(self, img: Image.Image) -> Image.Image:
        """Resize và crop ảnh về kích thước vuông"""
        original_width, original_height = img.size
        target_width, target_height = self.frame_size
        
        # Tính tỷ lệ để fill toàn bộ khung
        ratio = max(target_width / original_width, target_height / original_height)
        
        # Resize ảnh
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop về kích thước target
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        return img.crop((left, top, right, bottom))

    def add_rounded_corners(self, img: Image.Image) -> Image.Image:
        """Thêm bo góc tròn"""
        # Tạo mask bo góc
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle(
            (0, 0, img.size[0], img.size[1]), 
            self.corner_radius, 
            fill=255
        )
        
        # Apply mask
        output = Image.new("RGBA", img.size, self.bg_color)
        output.paste(img, (0, 0))
        output.putalpha(mask)
        
        return output

    def add_subtle_effects(self, img: Image.Image) -> Image.Image:
        """Thêm hiệu ứng nhẹ cho thumbnail"""
        # Thêm shadow nhẹ
        shadow = Image.new("RGBA", (img.size[0] + 4, img.size[1] + 4), self.bg_color)
        shadow_mask = Image.new("L", shadow.size, 0)
        draw = ImageDraw.Draw(shadow_mask)
        draw.rounded_rectangle(
            (2, 2, shadow.size[0] - 2, shadow.size[1] - 2),
            self.corner_radius,
            fill=100
        )
        shadow.putalpha(shadow_mask)
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=2))
        
        # Composite shadow + image
        final = Image.new("RGBA", shadow.size, self.bg_color)
        final.paste(shadow, (0, 0), shadow)
        final.paste(img, (2, 2), img)
        
        return final

    def save_thumbnail(self, img: Image.Image) -> bool:
        """Lưu thumbnail ra file"""
        try:
            # Process ảnh
            img = self.resize_and_crop(img)
            img = self.add_rounded_corners(img)
            img = self.add_subtle_effects(img)
            
            # Lưu file
            img.save(self.output_path, "PNG", optimize=True)
            return True
        except (OSError, ValueError):
            return False

    def generate_thumbnail(self) -> str:
        """Generate thumbnail chính"""
        # Lấy URL album art
        art_url = self.get_art_url()
        img = None
        
        if art_url:
            if art_url.startswith(("http://", "https://")):
                # Download từ URL
                img = self.download_image(art_url)
            elif art_url.startswith("file://"):
                # Load từ file local
                img = self.load_local_image(art_url)
        
        # Nếu không có album art, dùng fallback
        if not img:
            img = self.get_fallback_image()
        
        # Nếu vẫn không có, tạo default
        if not img:
            img = self.create_default_thumbnail()
        
        # Lưu thumbnail
        if self.save_thumbnail(img):
            return self.output_path
        else:
            return ""

def main():
    """Main function"""
    try:
        generator = ThumbnailGenerator()
        result = generator.generate_thumbnail()
        print(result)
    except Exception:
        # Silent fail - return empty string
        print("")

if __name__ == "__main__":
    main()