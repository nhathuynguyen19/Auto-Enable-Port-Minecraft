from flask import Flask, Response, stream_with_context, request
import subprocess
import time
import psutil
import os
import pygetwindow as gw
import pyautogui
import threading
import keyboard
import mouse
import ctypes
import datetime
from pystray import Icon, MenuItem, Menu
from PIL import Image

LOG_FILE = "enable_port.log"

app = Flask(__name__)

request_lock = threading.Lock()
process_running = True

def check_minecraft_connections(port=12345):
    try:
        # Chạy lệnh netstat để lấy danh sách các kết nối đến cổng Minecraft
        result = subprocess.run(["netstat", "-an"], capture_output=True, text=True)
        
        # Kiểm tra xem có kết nối nào đến cổng không
        connections = [line for line in result.stdout.split("\n") if f":{port}" in line and "ESTABLISHED" in line]
        
        if connections:
            print("Người chơi đang kết nối:")
            for conn in connections:
                print(conn)
            return True
        else:
            print("Không có ai đang kết nối vào server Minecraft LAN.")
            return False
    except Exception as e:
        print(f"Lỗi: {e}")
        return False

def on_exit(icon, item):
    global process_running
    process_running = False
    icon.stop()
    os._exit(0)

def write_log(message):
    """Ghi log vào file với timestamp"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")

def run_system_tray():
    if process_running:
        image = Image.open("icon.png")  # Đổi "icon.png" thành đường dẫn ảnh của bạn
        menu = Menu(MenuItem("Thoát", on_exit))
        icon = Icon("enablePort", image, menu=menu)
        icon.title = "Auto Enable Port Minecraft"
        icon.run()

def is_process_running(process_name):
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if process_name.lower() in proc.info['name'].lower():
            return proc
    return None

def wait_for_stable_process(process_name, timeout=30, cpu_threshold=5, stable_duration=5):
    start_time = time.time()
    stable_start = None

    while time.time() - start_time < timeout:
        proc = is_process_running(process_name)
        if proc:
            try:
                cpu_usage = proc.cpu_percent(interval=1)
                name = "Minecraft" if process_name == "javaw.exe" else "Legacy" if process_name == "java.exe" else process_name
                yield f"CPU {name}: {cpu_usage}%\n"

                if cpu_usage < cpu_threshold:
                    if stable_start is None:
                        stable_start = time.time()
                    elif time.time() - stable_start >= stable_duration:
                        yield f"{process_name} đã ổn định!\n"
                        return
                else:
                    stable_start = None

            except psutil.NoSuchProcess:
                # yield f"{process_name} không còn tồn tại.\n"
                continue
        time.sleep(1)

    yield f"Lỗi: {process_name} không ổn định sau {timeout} giây.\n"

def kill_process(process_name):
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if process_name.lower() in proc.info['name'].lower():
            yield f"Đang tắt tiến trình: {proc.info['name']} (PID: {proc.info['pid']})\n"
            os.kill(proc.info['pid'], 9)

def start_process_hidden(command):
    """Chạy tiến trình ngầm, không hiện cửa sổ."""
    subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW, shell=True)

def handle():
    yield "Đang mở Legacy Launcher...\n"
    start_process_hidden(r"C:\Users\huyth\AppData\Roaming\.tlauncher\legacy\Minecraft\TL.exe")

    for message in wait_for_stable_process("java.exe"):
        yield message

    yield "Legacy đã mở và ổn định! Tiếp tục vào game...\n"

    if not is_process_running("javaw.exe"):
        yield "Đang mở Minecraft...\n"
        start_process_hidden(r"C:\Users\huyth\OneDrive\Documents\Code\My projects\Open minecraft\when_nothing.ahk")

        for message in wait_for_stable_process("javaw.exe", 240, 50, 10):
            yield message

        yield "Minecraft đã mở và ổn định! Tiếp tục mở port...\n"
        start_process_hidden(r"C:\Users\huyth\OneDrive\Documents\Code\My projects\Open minecraft\in_game.ahk")

# Danh sách các phím trên bàn phím 60%
keys_60_layout = [
    "esc", "tab", "caps lock", "shift", "ctrl", "alt", "space", "enter", "backspace", "delete",
    *"abcdefghijklmnopqrstuvwxyz",  # Các chữ cái từ a-z
    *"0123456789",  # Các số từ 0-9
    "`", "~", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "_", "=", "+",
    "[", "]", "{", "}", "\\", "|", ";", ":", "'", '"', ",", "<", ".", ">", "/", "?",
]

# Kiểm tra nếu có bất kỳ phím nào được bấm
def any_key_pressed():
    return any(keyboard.is_pressed(k) for k in keys_60_layout)

def bring_minecraft_to_front():
    """Đưa cửa sổ Minecraft lên màn hình nếu đang chạy."""
    messages = ["Minecraft đang hoạt động..."]
    for window in gw.getWindowsWithTitle(""):
        if "Minecraft" in window.title:
            # messages.append(f"Đã tìm thấy cửa sổ: {window.title}")
            try:
                window.restore()
                # messages.append("Đã khôi phục cửa sổ.")
                window.activate()
                # messages.append("Đã đưa Minecraft lên foreground.")
                return True, messages
            except Exception as e:
                messages.append(f"Lỗi khi xử lý cửa sổ: {e}")
                return False, messages
    messages.append("Không tìm thấy cửa sổ Minecraft.")
    return False, messages

def is_minecraft_active():
    """Kiểm tra xem cửa sổ Minecraft có đang active không."""
    import pygetwindow as gw
    active_window = gw.getActiveWindow()
    return active_window and "Minecraft" in active_window.title

def wait_for_confirmation(timeout=60):
    """Chờ xác nhận của người dùng trong cửa sổ Minecraft trong thời gian timeout giây."""
    messages = ["Bắt đầu chờ xác nhận từ người dùng..."]
    start_time = time.time()
    prev_mouse_pos = pyautogui.position()

    while time.time() - start_time < timeout:
        if is_minecraft_active():
            detected = False  # Cờ kiểm tra nếu có bất kỳ sự kiện nào xảy ra
            
            # Kiểm tra nếu có phím được bấm
            try:
                if any_key_pressed():
                    messages.append("Phát hiện bấm phím!")
                    detected = True  
            except:
                messages.append("Không thể kiểm tra bàn phím. Kiểm tra quyền chạy script!")
            
            # Kiểm tra nếu có nhấp chuột
            try:
                if mouse.is_pressed("left") or mouse.is_pressed("right"):
                    messages.append("Phát hiện nhấp chuột!")
                    detected = True  
            except:
                messages.append("Không thể kiểm tra chuột. Hãy cài đặt thư viện `mouse` đúng cách!")
            
            # Nếu bất kỳ sự kiện nào xảy ra, thoát vòng lặp
            if detected:
                return True, messages

        time.sleep(0.1)  # Kiểm tra nhanh hơn

    messages.append("Hết thời gian chờ, không có hoạt động.")
    return False, messages

def show_noti_request():
    if process_running:
        ctypes.windll.user32.MessageBoxW(
            0,  
            "Có request mở port!",  # Nội dung
            "Thông báo",  # Tiêu đề
            0x40 | 0x40000  # MB_ICONINFORMATION | MB_TOPMOST
        )

def check_and_handle_minecraft():
    """Xử lý logic khi Minecraft đang chạy."""
    if check_minecraft_connections():
        yield "\nĐang có người chơi, port đang được mở :))"
        return
        
    if is_process_running("javaw.exe"):
        result, logs = bring_minecraft_to_front()
        for log in logs:
            yield log + "\n"
        if result:  # Nếu có cửa sổ Minecraft, đưa lên trước
            yield f"Nếu không có người chơi tiến hành tự động tắt Minecraft và khởi động lại Legacy sau 60s..."
            result, logs = wait_for_confirmation()
            if result:
                yield "\nĐang có người chơi, port đang được mở hoặc chưa :))"
                threading.Thread(target=show_noti_request, daemon=True).start()
                return

        # Nếu không có xác nhận trong 60 giây, tắt Minecraft
        for message in kill_process("javaw.exe"):
            yield message

        # Chạy lại Minecraft
        for message in handle():
            yield message

        yield "Đã mở port!\n"

def get_client_ip():
    """Lấy địa chỉ IP thực sự của client"""
    if "X-Forwarded-For" in request.headers:
        return request.headers.get("X-Forwarded-For").split(",")[0]  # Lấy IP đầu tiên trong danh sách
    return request.remote_addr  # Nếu không có proxy, lấy IP trực tiếp

@app.route('/enablePort', methods=['GET'])
def enablePort():
    def event_stream():
        client_ip = get_client_ip()
        write_log(f"Request mở port từ IP: {client_ip}")

        global request_lock
        if not request_lock.acquire(blocking=False):
            yield "Có một người khác đang request"
            return Response(stream_with_context(event_stream()), content_type='text/event-stream; charset=utf-8', headers={'Transfer-Encoding': 'chunked'})
        try:
            while True:
                if is_process_running("javaw.exe"):
                    for message in check_and_handle_minecraft():
                        yield message
                    break

                if is_process_running("java.exe"):
                    for message in kill_process("java.exe"):
                        yield message

                for message in handle():
                    yield message
                yield "Đang mở map"
                time.sleep(10)
                yield "Đang mở port..."
                time.sleep(15)
                yield "Đã mở port!\n"
                break
        except GeneratorExit:
            print("⚠️ Client đã đóng tab hoặc hủy request!")
            return
        finally:
            request_lock.release()  # Mở khóa khi xong

    return Response(stream_with_context(event_stream()), content_type='text/event-stream; charset=utf-8', headers={'Transfer-Encoding': 'chunked'})

if __name__ == '__main__':
    threading.Thread(target=run_system_tray, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
