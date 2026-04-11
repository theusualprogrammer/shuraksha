; -----------------------------------------------
; Shuraksha - Registration Only Tool
; File: installer_register_only.iss
; -----------------------------------------------
; This is a SEPARATE lightweight tool.
; It does NOT install or uninstall the application.
; Use it ONLY to re-run the registration wizard
; if you want to reset your vault credentials
; without reinstalling the full application.
; -----------------------------------------------

#define AppName     "Shuraksha"
#define AppExeName  "Shuraksha.exe"
#define AppURL      "https://github.com/theusualprogrammer/shuraksha"
#define SourceDir   "dist\Shuraksha"
#define OutputDir   "dist\installer"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567891}
AppName=Shuraksha Registration Tool
AppVersion=1.0.0
AppPublisher=Shuraksha Security
AppPublisherURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
OutputDir={#OutputDir}
OutputBaseFilename=Shuraksha_Register_Tool
SetupIconFile=assets\icons\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
PrivilegesRequired=lowest
CreateUninstallRegKey=no
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel1=Shuraksha Registration Tool
WelcomeLabel2=This tool will re-run the Shuraksha vault registration wizard.%n%nUse this if you want to reset your master password and vault credentials without reinstalling the full application.%n%nClick Next to continue.
FinishedLabel=Registration tool has finished. The Shuraksha registration wizard will now open.

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\icons\icon.ico";     DestDir: "{app}\assets\icons"; Flags: ignoreversion
Source: "assets\icons\icon_256.png"; DestDir: "{app}\assets\icons"; Flags: ignoreversion

[Run]
Filename: "{app}\{#AppExeName}"; Parameters: "--register"; Description: "Open Shuraksha Registration Wizard"; Flags: postinstall nowait skipifsilent; StatusMsg: "Launching registration wizard..."

[Code]

function InitializeSetup(): Boolean;
var
  Msg: String;
begin
  Result := True;
  Msg := 'This tool re-runs the Shuraksha registration wizard. Your existing vault data will be overwritten if you complete the registration. Do you want to continue?';
  if MsgBox(Msg, mbConfirmation, MB_YESNO) = IDNO then begin
    Result := False;
  end;
end;