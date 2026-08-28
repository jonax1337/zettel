; NSIS pre-install hook: force-clean stale bundled resources before copying.
;
; Root cause (Tauri NSIS bug, see tauri-apps/tauri#15134): the bundled
; `sidecar/`, `jre/`, and `kosit-validator/` resource directories contain
; unversioned files (PyInstaller-frozen exe + DLLs, raw JRE/validator assets).
; NSIS's default SetOverwrite logic sometimes skips re-copying files it
; considers "unchanged" for directories like these, so across several
; releases only zettel.exe got updated while sidecar/jre/kosit-validator
; silently stayed on whatever version was first installed — for months.
;
; Fix: unconditionally kill any running sidecar process and wipe these
; three resource directories before the installer copies the fresh ones.
; This makes every install/update byte-for-byte reproducible regardless of
; what NSIS's heuristics decide to skip.

!macro NSIS_HOOK_PREINSTALL
  ; Sidecar may still be running if the app wasn't fully closed.
  nsExec::Exec 'taskkill /F /IM zettel-sidecar.exe'
  Sleep 500

  ; Wipe stale bundled resources so the fresh copies always win.
  RMDir /r "$INSTDIR\sidecar"
  RMDir /r "$INSTDIR\jre"
  RMDir /r "$INSTDIR\kosit-validator"
!macroend
