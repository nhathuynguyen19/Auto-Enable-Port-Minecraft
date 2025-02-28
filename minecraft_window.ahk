F1::
WinGet, javaWindows, List, ahk_exe javaw.exe
Loop, %javaWindows% {
    winID := javaWindows%A_Index%
    WinGetTitle, winTitle, ahk_id %winID%
    MsgBox, Cửa sổ thuộc javaw.exe: %winTitle% (ID: %winID%)
}
return