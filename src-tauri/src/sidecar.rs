// Copyright (C) 2026 VoiceGameControl Contributors
// Licensed under MIT

use std::process::{Child, Command, Stdio};
use tauri::AppHandle;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

pub fn spawn_sidecar(_handle: &AppHandle, port: u16) -> Result<Child, String> {
    #[cfg(debug_assertions)]
    {
        let current_dir = std::env::current_dir()
            .map_err(|e| format!("Failed to get current dir: {}", e))?;
        
        let project_root = if current_dir.ends_with("src-tauri") {
            current_dir.parent().unwrap().to_path_buf()
        } else {
            current_dir
        };
        
        let mut cmd = Command::new("python");
        cmd.args(["-m", "voice_game_control.main", "--port", &port.to_string(), "--tauri"])
            .current_dir(&project_root)
            .stdout(Stdio::inherit())
            .stderr(Stdio::inherit());
        
        #[cfg(target_os = "windows")]
        {
            const CREATE_NO_WINDOW: u32 = 0x08000000;
            cmd.creation_flags(CREATE_NO_WINDOW);
        }
        
        eprintln!("[TAURI] Attempting to spawn Python: python -m voice_game_control.main --port {} --tauri", port);
        eprintln!("[TAURI] Working directory: {:?}", project_root);
        
        let child = cmd.spawn()
            .map_err(|e| {
                let err_msg = format!("Failed to spawn Python: {}", e);
                eprintln!("[TAURI] ✗ {}", err_msg);
                err_msg
            })?;
        
        eprintln!("[TAURI] ✓ Python backend spawned with PID: {}", child.id());
        
        return Ok(child);
    }
    
    #[cfg(not(debug_assertions))]
    {
        Err("Production mode not implemented yet".to_string())
    }
}
