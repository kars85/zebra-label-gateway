; NSIS installer for Zebra Label Gateway (Windows).
; Build:  makensis packaging\installer.nsi
; Packages the PyInstaller onedir output in packaging\dist\ZebraLabelGateway.

Unicode true
!include "MUI2.nsh"
!include "x64.nsh"

!define APPNAME "Zebra Label Gateway"
!define APPVER "1.0.0"
!define PUBLISHER "Zebra Label Gateway"
!define UNINSTKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\ZebraLabelGateway"

Name "${APPNAME}"
OutFile "ZebraLabelGateway-Setup.exe"
InstallDir "$PROGRAMFILES64\${APPNAME}"
InstallDirRegKey HKLM "Software\ZebraLabelGateway" "InstallDir"
RequestExecutionLevel admin

!define MUI_ICON "app.ico"
!define MUI_UNICON "app.ico"
!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\ZebraLabelGateway.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APPNAME}"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  ; PyInstaller onedir output (exe + _internal with all deps + bundled frontend).
  File /r "dist\ZebraLabelGateway\*.*"

  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\ZebraLabelGateway.exe" "" "$INSTDIR\ZebraLabelGateway.exe"
  CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\ZebraLabelGateway.exe" "" "$INSTDIR\ZebraLabelGateway.exe"

  WriteRegStr HKLM "Software\ZebraLabelGateway" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "${UNINSTKEY}" "DisplayName" "${APPNAME}"
  WriteRegStr HKLM "${UNINSTKEY}" "DisplayVersion" "${APPVER}"
  WriteRegStr HKLM "${UNINSTKEY}" "Publisher" "${PUBLISHER}"
  WriteRegStr HKLM "${UNINSTKEY}" "DisplayIcon" "$INSTDIR\ZebraLabelGateway.exe"
  WriteRegStr HKLM "${UNINSTKEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegDWORD HKLM "${UNINSTKEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINSTKEY}" "NoRepair" 1
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
  RMDir "$SMPROGRAMS\${APPNAME}"
  Delete "$DESKTOP\${APPNAME}.lnk"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKLM "${UNINSTKEY}"
  DeleteRegKey HKLM "Software\ZebraLabelGateway"
  ; Note: per-user data (%LOCALAPPDATA%\ZebraLabelGateway) is left in place on
  ; purpose so saved-label history/profiles survive a reinstall.
SectionEnd
