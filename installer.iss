#define AppName       "Shuraksha"
#define AppVersion    "1.0.0"
#define AppPublisher  "Shuraksha Security"
#define AppExeName    "Shuraksha.exe"
#define AppRegName    "Shuraksha"
#define AppURL        "https://github.com/theusualprogrammer/shuraksha"
#define SourceDir     "dist\Shuraksha"
#define OutputDir     "dist\installer"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir={#OutputDir}
OutputBaseFilename=Shuraksha_Setup_v{#AppVersion}
SetupIconFile=assets\icons\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} Security Vault
CreateUninstallRegKey=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel1=Welcome to Shuraksha Security Vault
WelcomeLabel2=This will install Shuraksha version {#AppVersion} on your computer.%n%nShuraksha is a personal encrypted security vault.%n%nAll your data stays only on this machine. Nothing is ever sent to any cloud or external server.%n%nClick Next to continue.
FinishedLabel=Shuraksha has been installed successfully.%n%nRemember your three keys:%n  1. Master password opens the application.%n  2. Dark mode toggle reveals the hidden vault.%n  3. Date of birth on the BODMAS screen opens the real vault.

[Tasks]
Name: "desktopicon";   Description: "Create a desktop shortcut";  GroupDescription: "Shortcuts:"
Name: "startmenuicon"; Description: "Create a Start Menu entry";   GroupDescription: "Shortcuts:"

[Files]
Source: "{#SourceDir}\*";            DestDir: "{app}";              Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\icons\icon.ico";     DestDir: "{app}\assets\icons"; Flags: ignoreversion
Source: "assets\icons\icon_256.png"; DestDir: "{app}\assets\icons"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\{#AppName}";     Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\icons\icon.ico"; Comment: "Open Shuraksha Security Vault"
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\icons\icon.ico"; Comment: "Open Shuraksha Security Vault"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

[Registry]
Root: HKCU; Subkey: "Software\{#AppRegName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}";        Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#AppRegName}"; ValueType: string; ValueName: "Version";     ValueData: "{#AppVersion}"
Root: HKCU; Subkey: "Software\{#AppRegName}"; ValueType: string; ValueName: "Publisher";   ValueData: "{#AppPublisher}"
Root: HKCU; Subkey: "Software\{#AppRegName}"; ValueType: string; ValueName: "URL";         ValueData: "{#AppURL}"

[Run]
Filename: "{app}\{#AppExeName}"; Parameters: "--register"; Description: "Set up your Shuraksha vault (required)"; Flags: postinstall nowait skipifsilent; StatusMsg: "Running vault registration setup..."

[UninstallRun]
Filename: "{app}\{#AppExeName}"; Parameters: "--wipe"; Flags: skipifdoesntexist; RunOnceId: "WipeVaultData"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]

function InitializeSetup(): Boolean;
var
  OldVersion: String;
  Msg: String;
begin
  Result := True;
  if RegQueryStringValue(HKCU, 'Software\Shuraksha', 'Version', OldVersion) then begin
    Msg := 'Shuraksha version ' + OldVersion + ' is already installed. Your existing vault data will NOT be affected. Do you want to continue?';
    if MsgBox(Msg, mbConfirmation, MB_YESNO) = IDNO then begin
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
  end;
end;

function InitializeUninstall(): Boolean;
var
  Msg: String;
begin
  Result := True;
  Msg := 'Do you want to permanently delete your encrypted vault data? Click YES to delete everything. Click NO to keep your vault data.';
  if MsgBox(Msg, mbConfirmation, MB_YESNO) = IDYES then begin
    DelTree(ExpandConstant('{userappdata}\Shuraksha'), True, True, True);
  end;
end;