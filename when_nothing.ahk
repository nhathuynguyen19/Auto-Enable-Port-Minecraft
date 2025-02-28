#Persistent
SetTitleMatchMode, 2

; Chờ cửa sổ của tiến trình java.exe xuất hiện
WinWait, ahk_exe java.exe
WinGet, idList, List, ahk_exe java.exe

; Duyệt qua từng cửa sổ con để tìm Legacy Launcher
Loop, %idList% {
    winID := idList%A_Index%
    WinGetTitle, winTitle, ahk_id %winID%

    ; Kiểm tra nếu cửa sổ có chữ "Legacy Launcher" trong tiêu đề
    If (InStr(winTitle, "Legacy Launcher")) {
        Break  ; Dừng vòng lặp khi tìm thấy cửa sổ đúng
    }
}

; Nếu không tìm thấy cửa sổ nào phù hợp, thoát script
if (!winID) {
    ExitApp
}

; Đưa cửa sổ xuống dưới cùng (z-order thấp nhất)
DllCall("SetWindowPos", "UInt", winID, "UInt", 1, "Int", 0, "Int", 0, "Int", 0, "Int", 0, "UInt", 3)

ControlFocus,, ahk_id %winID%  ; Đảm bảo cửa sổ nhận phím
Sleep, 100

; Gửi phím đến cửa sổ vừa tìm được
ControlSend,, {Tab 4}, ahk_id %winID%
Sleep, 500
ControlSend,, {Enter}, ahk_id %winID%

ExitApp
