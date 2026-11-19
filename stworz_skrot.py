# -*- coding: utf-8 -*-
import os
import subprocess

shortcut_path = os.path.expanduser(r"~\Desktop\Agent Forum FW Drucik (Antigravity AI).lnk")
target_bat = r"D:\strona www fwdrucik\URUCHOM_AGENTA_FORUM_ANTIGRAVITY.bat"
work_dir = r"D:\strona www fwdrucik"

ps_script = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{shortcut_path}')
$s.TargetPath = '{target_bat}'
$s.WorkingDirectory = '{work_dir}'
$s.Description = 'Uruchamia Agenta Administratora Forum FW Drucik pod MCP Antigravity'
$s.IconLocation = 'shell32.dll,221'
$s.Save()
Write-Output "SHORTCUT_CREATED"
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
print("STDOUT:", res.stdout.strip())
print("STDERR:", res.stderr.strip())
print("ISTNIEJE:", os.path.exists(shortcut_path))
