**File:** `~/my-hypr-dots/install.sh`

```bash
#!/bin/bash

# --- COLORS ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- HEADER ---
echo -e "${GREEN}"
echo "=========================================="
echo "   MY HYPRLAND DOTFILES INSTALLER"
echo "=========================================="
echo -e "${NC}"


if [ -f /etc/arch-release ]; then
    echo -e "${GREEN}[+] Đã phát hiện Arch Linux.${NC}"
else
    echo -e "${RED}[!] Script này tối ưu cho Arch Linux. Hãy cẩn thận!${NC}"
    read -p "Bạn có muốn tiếp tục không? (y/n): " confirm
    if [[ $confirm != "y" ]]; then exit; fi
fi

# 2. Backup hàm
backup_config() {
    DIR=$1
    if [ -d "$HOME/.config/$DIR" ]; then
        echo -e "${YELLOW}[*] Đang backup $DIR cũ sang $DIR.bak...${NC}"
        mv "$HOME/.config/$DIR" "$HOME/.config/$DIR.bak"
    fi
}

# 3. Thực hiện Backup
echo -e "${GREEN}[+] Đang sao lưu cấu hình cũ...${NC}"
backup_config "hypr"
backup_config "waybar"
backup_config "kitty"
backup_config "rofi"

# 4. Copy Config mới
echo -e "${GREEN}[+] Đang cài đặt config mới...${NC}"
cp -r .config/* "$HOME/.config/"

# 5. Cấp quyền thực thi cho scripts
echo -e "${GREEN}[+] Cấp quyền cho các script...${NC}"
chmod +x scripts/*.sh 2>/dev/null

# 6. Optional: Cài gói (Cần sửa list gói cho phù hợp máy bạn)
# echo -e "${YELLOW}[*] Đang cài đặt các gói cần thiết...${NC}"
# yay -S hyprland waybar rofi-wayland kitty --noconfirm

echo -e "${GREEN}"
echo "=========================================="
echo "   CÀI ĐẶT HOÀN TẤT! HÃY REBOOT MÁY."
echo "=========================================="
echo -e "${NC}"