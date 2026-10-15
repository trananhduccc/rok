import os
import time
import random
import threading
from flask import Flask, render_template_string, jsonify, request
import pyautogui
import cv2
import numpy as np

pyautogui.PAUSE = 0.02
pyautogui.FAILSAFE = True

app = Flask(__name__)

# Trạng thái các tính năng trên Web
bot_state = {
    "master_running": False,
    "fog": True,        # Tự động dò sương (Bật/Tắt 0.1s)
    "cave": False,      # Tự động dò hang & nhận làng bộ lạc
    "farm": False,      # Tự động tìm mỏ & đi farm
    "barb": False,      # Tự động tìm & đánh man rợ
    "logs": ["[Hệ thống] Khởi động Web Server thành công. Sẵn sàng điều khiển!"]
}

IMG_DIR = "images"
CONFIDENCE = 0.82

def add_log(msg):
    timestamp = time.strftime("%H:%M:%S")
    bot_state["logs"].append(f"[{timestamp}] {msg}")
    if len(bot_state["logs"]) > 60:
        bot_state["logs"].pop(0)

def locate_img(filename, conf=CONFIDENCE):
    """Tìm tọa độ của hình ảnh mẫu trên màn hình"""
    path = os.path.join(IMG_DIR, filename)
    if not os.path.exists(path):
        return None
    screen = pyautogui.screenshot()
    screen_np = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
    template = cv2.imread(path, cv2.IMREAD_COLOR)
    if template is None:
        return None

    h, w, _ = template.shape
    res = cv2.matchTemplate(screen_np, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val >= conf:
        return (max_loc[0] + w // 2, max_loc[1] + h // 2)
    return None

def click_at(pos, delay_after=0.5):
    """Click ngẫu nhiên lệch tâm 1-3px như người thật"""
    x = pos[0] + random.randint(-3, 3)
    y = pos[1] + random.randint(-3, 3)
    pyautogui.click(x, y, _pause=False)
    if delay_after > 0:
        time.sleep(delay_after)

# ================= CÁC MODULE TỰ ĐỘNG =================

def run_fog_module():
    """Module 1: Dò sương bằng mẹo Bật -> chờ 0.1s -> Tắt"""
    idle_pos = locate_img("scout_idle.png")
    if idle_pos:
        toggle_pos = locate_img("auto_toggle.png")
        if not toggle_pos:
            click_at(idle_pos, 0.4)
            toggle_pos = locate_img("auto_toggle.png")
        if toggle_pos:
            # Nhấp Bật -> chờ đúng 0.1s -> Nhấp Tắt
            click_at(toggle_pos, 0.1)
            click_at(toggle_pos, 0.0)
            add_log("[Dò Sương] Đã kích hoạt Bật/Tắt 0.1s cho Trinh sát!")
            time.sleep(2.0)

def run_cave_module():
    """Module 2: Dò Hang động và Nhận quà Làng bộ lạc"""
    # Kiểm tra biểu tượng Hang động hoặc Làng trên bản đồ/báo cáo
    village_pos = locate_img("village_icon.png")
    if village_pos:
        click_at(village_pos, 1.0)
        add_log("[Làng Bộ Lạc] Đã bấm nhận quà Làng bộ lạc!")
        return

    cave_pos = locate_img("cave_icon.png")
    if cave_pos and locate_img("scout_idle.png"):
        click_at(cave_pos, 0.8)
        investigate_btn = locate_img("btn_investigate.png") # Nút "Điều tra" hang
        if investigate_btn:
            click_at(investigate_btn, 0.8)
            send_btn = locate_img("btn_send.png")
            if send_btn:
                click_at(send_btn, 1.0)
                add_log("[Dò Hang] Đã cử Trinh sát đi điều tra Hang động!")

def run_farm_module():
    """Module 3: Tự động tìm mỏ và cử quân đi Farm"""
    # Chỉ tìm mỏ khi phát hiện còn hàng đợi rảnh (hoặc nút Tìm kiếm hiển thị)
    search_icon = locate_img("btn_search_map.png") # Nút kính lúp góc trái dưới
    if search_icon:
        click_at(search_icon, 0.7)
        find_res_btn = locate_img("btn_find_resource.png") # Nút "Tìm kiếm" mỏ tài nguyên
        if find_res_btn:
            click_at(find_res_btn, 1.5)
            gather_btn = locate_img("btn_gather.png") # Nút "Thu thập"
            if gather_btn:
                click_at(gather_btn, 0.8)
                new_troop_btn = locate_img("btn_new_troop.png") # Nút "Đội quân mới"
                if new_troop_btn:
                    click_at(new_troop_btn, 0.8)
                    march_btn = locate_img("btn_march.png") # Nút "Hành quân"
                    if march_btn:
                        click_at(march_btn, 1.5)
                        add_log("[Đi Farm] Đã cử 1 đạo quân đi thu thập tài nguyên!")

def run_barb_module():
    """Module 4: Tự động đánh / kéo Man rợ"""
    # Ưu tiên 1: Nếu đang kéo man trên bản đồ, tìm man rợ gần đạo quân đang đứng
    barb_on_map = locate_img("barb_target.png")
    if barb_on_map:
        click_at(barb_on_map, 0.6)
        atk_btn = locate_img("btn_attack.png")
        if atk_btn:
            click_at(atk_btn, 0.7)
            march_btn = locate_img("btn_march.png")
            if march_btn:
                click_at(march_btn, 1.5)
                add_log("[Man Rợ] Đã tấn công mục tiêu Man rợ tiếp theo!")
                return

    # Ưu tiên 2: Dùng kính lúp tìm Man rợ mới
    search_icon = locate_img("btn_search_map.png")
    if search_icon:
        click_at(search_icon, 0.7)
        find_barb_btn = locate_img("btn_find_barb.png")
        if find_barb_btn:
            click_at(find_barb_btn, 1.5)
            atk_btn = locate_img("btn_attack.png")
            if atk_btn:
                click_at(atk_btn, 0.8)
                new_troop_btn = locate_img("btn_new_troop.png")
                if new_troop_btn:
                    click_at(new_troop_btn, 0.8)
                march_btn = locate_img("btn_march.png")
                if march_btn:
                    click_at(march_btn, 1.5)
                    add_log("[Man Rợ] Đã xuất quân đánh Man rợ!")

def master_bot_loop():
    """Vòng lặp chính chạy ngầm quản lý toàn bộ tác vụ"""
    while True:
        if bot_state["master_running"]:
            try:
                # 0. Kiểm tra Captcha bảo vệ tài khoản
                if locate_img("captcha.png", conf=0.80):
                    bot_state["master_running"] = False
                    add_log("⚠️ CẢNH BÁO: Phát hiện bảng Xác minh Captcha! Đã tự động tạm dừng.")
                    continue

                # Thực thi lần lượt các module được bật trên Web
                if bot_state["fog"]:
                    run_fog_module()
                if bot_state["cave"]:
                    run_cave_module()
                if bot_state["farm"]:
                    run_farm_module()
                if bot_state["barb"]:
                    run_barb_module()

            except Exception as e:
                add_log(f"[Lỗi] {e}")

        time.sleep(random.uniform(1.2, 2.0))

# ================= GIAO DIỆN WEB (HTML/CSS/JS) =================

HTML_PAGE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RoK Web Auto Center</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #12181b; color: #f5f6fa; margin: 0; padding: 15px; }
        .container { max-width: 480px; margin: auto; background: #1e272e; padding: 18px; border-radius: 14px; box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
        h2 { text-align: center; color: #ffd32a; margin-top: 0; font-size: 20px; }
        .master-btn { width: 100%; padding: 14px; font-size: 16px; font-weight: bold; border: none; border-radius: 10px; cursor: pointer; margin-bottom: 15px; transition: 0.2s; }
        .btn-on { background: #05c46b; color: white; }
        .btn-off { background: #ff3f34; color: white; }
        .card { display: flex; justify-content: space-between; align-items: center; background: #2f3640; padding: 12px 15px; border-radius: 10px; margin-bottom: 10px; }
        .card-title { font-weight: 600; font-size: 15px; }
        .card-sub { font-size: 12px; color: #a4b0be; margin-top: 2px; }
        input[type="checkbox"] { width: 22px; height: 22px; accent-color: #ffd32a; cursor: pointer; }
        .log-box { background: #0f1417; color: #0be881; font-family: Consolas, monospace; font-size: 12px; height: 190px; overflow-y: auto; padding: 10px; border-radius: 8px; margin-top: 12px; border: 1px solid #353b48; }
    </style>
</head>
<body>
    <div class="container">
        <h2>⚡ ROK WEB AUTO DASHBOARD</h2>
        <button id="masterBtn" class="master-btn btn-on" onclick="toggleMaster()">▶ BẮT ĐẦU CHẠY AUTO</button>

        <div class="card">
            <div>
                <div class="card-title">🌫️ Tự động Dò Sương (0.1s)</div>
                <div class="card-sub">Canh do thám về tự Bật -> 0.1s -> Tắt</div>
            </div>
            <input type="checkbox" id="fog" checked onchange="updateConfig()">
        </div>

        <div class="card">
            <div>
                <div class="card-title">⛰️ Tự động Dò Hang & Làng</div>
                <div class="card-sub">Thăm dò hang động & nhận quà làng bộ lạc</div>
            </div>
            <input type="checkbox" id="cave" onchange="updateConfig()">
        </div>

        <div class="card">
            <div>
                <div class="card-title">🌾 Tự động Đi Farm Mỏ</div>
                <div class="card-sub">Tìm mỏ tài nguyên và cử đạo quân rảnh</div>
            </div>
            <input type="checkbox" id="farm" onchange="updateConfig()">
        </div>

        <div class="card">
            <div>
                <div class="card-title">⚔️ Tự động Đánh / Kéo Man</div>
                <div class="card-sub">Tìm kiếm và tấn công Man rợ liên hoàn</div>
            </div>
            <input type="checkbox" id="barb" onchange="updateConfig()">
        </div>

        <div class="log-box" id="logBox">Đang tải nhật ký...</div>
    </div>

    <script>
        let isRunning = false;

        async function fetchStatus() {
            const res = await fetch('/api/status');
            const data = await res.json();
            isRunning = data.master_running;
            const btn = document.getElementById('masterBtn');
            if (isRunning) {
                btn.innerText = "⏹ DỪNG TOÀN BỘ AUTO";
                btn.className = "master-btn btn-off";
            } else {
                btn.innerText = "▶ BẮT ĐẦU CHẠY AUTO";
                btn.className = "master-btn btn-on";
            }
            document.getElementById('fog').checked = data.fog;
            document.getElementById('cave').checked = data.cave;
            document.getElementById('farm').checked = data.farm;
            document.getElementById('barb').checked = data.barb;

            const logBox = document.getElementById('logBox');
            logBox.innerHTML = data.logs.join('<br>');
            logBox.scrollTop = logBox.scrollHeight;
        }

        async function toggleMaster() {
            await fetch('/api/toggle_master', { method: 'POST' });
            fetchStatus();
        }

        async function updateConfig() {
            const payload = {
                fog: document.getElementById('fog').checked,
                cave: document.getElementById('cave').checked,
                farm: document.getElementById('farm').checked,
                barb: document.getElementById('barb').checked
            };
            await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        setInterval(fetchStatus, 1200);
        fetchStatus();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/api/status")
def status():
    return jsonify(bot_state)

@app.route("/api/toggle_master", methods=["POST"])
def toggle_master():
    bot_state["master_running"] = not bot_state["master_running"]
    state_str = "ĐÃ BẬT" if bot_state["master_running"] else "ĐÃ TẠM DỪNG"
    add_log(f"[Hệ thống] Trạng thái Auto: {state_str}")
    return jsonify({"ok": True})

@app.route("/api/config", methods=["POST"])
def config():
    data = request.json
    for key in ["fog", "cave", "farm", "barb"]:
        if key in data:
            bot_state[key] = bool(data[key])
    add_log("[Cấu hình] Đã cập nhật danh sách tính năng từ Web!")
    return jsonify({"ok": True})

if __name__ == "__main__":
    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR)
    threading.Thread(target=master_bot_loop, daemon=True).start()
    print("=== MỞ TRÌNH DUYỆT VÀO ĐỊA CHỈ: http://127.0.0.1:5000 ===")
    app.run(host="0.0.0.0", port=5000, debug=False)

