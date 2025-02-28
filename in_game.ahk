#Persistent
SetTitleMatchMode, 2

; Chờ cửa sổ Minecraft mở và lấy danh sách ID
WinWait, ahk_exe javaw.exe
WinGet, idList, List, ahk_exe javaw.exe

winID := ""  ; Đảm bảo winID không rỗng

; Duyệt qua từng cửa sổ con để tìm cửa sổ chính của Minecraft
Loop, %idList% {
    this_id := idList%A_Index%
    WinGetTitle, winTitle, ahk_id %this_id%

    ; Kiểm tra nếu cửa sổ có chữ "Minecraft" trong tiêu đề
    If (InStr(winTitle, "Minecraft")) {
        winID := this_id  ; Gán giá trị cho winID
        Break  ; Dừng vòng lặp khi tìm thấy cửa sổ đúng
    }
}

; Nếu không tìm thấy cửa sổ nào phù hợp, báo lỗi và thoát
if (!winID) {
    MsgBox, Không tìm thấy cửa sổ Minecraft! Script sẽ thoát.
    ExitApp
}

; Đưa cửa sổ xuống dưới cùng (z-order thấp nhất)
DllCall("SetWindowPos", "UInt", winID, "UInt", 1, "Int", 0, "Int", 0, "Int", 0, "Int", 0, "UInt", 3)

; Đảm bảo control nhận lệnh trước khi gửi phím
ControlFocus,, ahk_id %winID%  ; Đảm bảo cửa sổ nhận phím
Sleep, 100

; Gửi phím trực tiếp đến Minecraft mà không làm gián đoạn người dùng
ControlSend,, {Tab}{Enter}, ahk_id %winID%  ; Chọn Singleplayer
Sleep, 1000
ControlSend,, {Tab}{Enter}, ahk_id %winID%  ; Chọn map đầu tiên
Sleep, 15000
ControlSend,, {Esc}, ahk_id %winID%  ; Mở menu
Sleep, 1000
ControlSend,, {Tab 7}{Enter}, ahk_id %winID%  ; Chọn "Open to LAN"
Sleep, 1000
ControlSend,, {Tab 2}, ahk_id %winID%  ; Vào đặt port
Sleep, 1000
ControlSend,, 12345, ahk_id %winID%  ; Đặt port 12345
Sleep, 1000
ControlSend,, {Tab}{Enter}, ahk_id %winID%  ; Mở Port
Sleep, 1000

ExitApp
