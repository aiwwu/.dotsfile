#!/bin/bash

# Script để chạy thumbnail generator một cách tự động

# Đường dẫn tới script Python
THUMBNAIL_SCRIPT="/home/khoi/.config/Scripts/thumbnail.py"
PYTHON_EXEC="python3" # Hoặc python

# Kiểm tra xem script có tồn tại không
if [ ! -f "$THUMBNAIL_SCRIPT" ]; then
    echo "Lỗi: Không tìm thấy script $THUMBNAIL_SCRIPT"
    exit 1
fi

# Hàm để chạy generator
run_generator() {
    $PYTHON_EXEC "$THUMBNAIL_SCRIPT" > /dev/null 2>&1
}

# Chạy lần đầu để có thumbnail ngay lập tức
run_generator

# Theo dõi sự thay đổi và chạy lại script
# playerctl --follow sẽ chờ sự kiện. Khi có sự kiện, nó sẽ chạy lại.
playerctl --follow metadata --format '{{ mpris:artUrl }}' | while read -r; do
    run_generator
done
