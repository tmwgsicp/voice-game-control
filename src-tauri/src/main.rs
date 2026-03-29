// Copyright (C) 2026 VoiceGameControl Contributors
// Licensed under MIT

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Child;
use std::sync::Mutex;
use std::net::TcpListener;
use tauri::Manager;

mod sidecar;

struct AppState {
    port: Mutex<u16>,
    sidecar_child: Mutex<Option<Child>>,
}

#[tauri::command]
fn get_port(state: tauri::State<AppState>) -> u16 {
    *state.port.lock().unwrap()
}

fn main() {
    let _lock_listener = match TcpListener::bind("127.0.0.1:38766") {
        Ok(listener) => Some(listener),
        Err(_) => {
            eprintln!("VoiceGameControl is already running!");
            std::process::exit(1);
        }
    };

    let port = portpicker::pick_unused_port().expect("No available port");

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_process::init())
        .manage(AppState {
            port: Mutex::new(port),
            sidecar_child: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![get_port])
        .setup(move |app| {
            let handle = app.handle().clone();
            let state = handle.state::<AppState>();
            
            match sidecar::spawn_sidecar(&handle, port) {
                Ok(child) => {
                    eprintln!("[TAURI] ✓ Python sidecar spawned, PID: {}", child.id());
                    *state.sidecar_child.lock().unwrap() = Some(child);
                }
                Err(e) => {
                    eprintln!("[TAURI] ✗ FAILED to spawn Python: {}", e);
                }
            }

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let tauri::RunEvent::ExitRequested { .. } = &event {
                let state = app_handle.state::<AppState>();
                let mut guard = state.sidecar_child.lock().unwrap();
                if let Some(mut child) = guard.take() {
                    let _ = child.kill();
                }
            }
        });
}
