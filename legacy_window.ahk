F1::
WinGet, javaWindows, List, ahk_exe java.exe
Loop, %javaWindows% {
    winID := javaWindows%A_Index%
    WinGetTitle, winTitle, ahk_id %winID%
    MsgBox, Cửa sổ thuộc java.exe: %winTitle% (ID: %winID%)
}
return