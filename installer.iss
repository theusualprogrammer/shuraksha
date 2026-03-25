; -----------------------------------------------
; Shuraksha - Inno Setup Installer Script
; File: installer.iss
; -----------------------------------------------

#define AppName        "Shuraksha"
#define AppVersion     "1.0.0"
#define AppPublisher   "Shuraksha Security"
#define AppDescription "Personal Security Vault"
#define AppExeName     "Shuraksha.exe"
#define AppRegName     "Shuraksha"
#define AppURL         "https://github.com/theusualprogrammer/shuraksha"
#define SourceDir      "dist\Shuraksha"
#define OutputDir      "dist\installer"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
AppComments={#AppDescription}

DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}

DirExistsWarning=yes
DisableDirPage=no

OutputDir={#OutputDir}
OutputBaseFilename=Shuraksha_Setup_v{#AppVersion}

SetupIconFile=assets\icons\icon.ico

Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

MinVersion=10.0

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

WizardStyle=modern
WizardResizable=no

PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} Security Vault
CreateUninstallRegKey=yes

ShowTasksTreeLines=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel1=Welcome to Shuraksha Security Vault
WelcomeLabel2=This will install Shuraksha version {#AppVersion} on your computer.%n%nShuraksha is a personal encrypted security vault.%n%nAll your data stays only on this machine. Nothing is ever sent to any cloud or external server.%n%nClick Next to continue.
FinishedLabel=Shuraksha Security Vault has been installed successfully.%n%nYour account has been registered. Launch Shuraksha from the desktop shortcut.%n%nRemember your three keys:%n  1. Master password opens the application.%n  2. Dark mode toggle reveals the hidden vault.%n  3. Date of birth on the BODMAS screen opens the real vault.

[Tasks]
Name: "desktopicon";   Description: "Create a &desktop shortcut";     GroupDescription: "Shortcuts:"; Flags: checked
Name: "startmenuicon"; Description: "Create a &Start Menu entry";      GroupDescription: "Shortcuts:"; Flags: checked
Name: "quicklaunch";   Description: "Create a &Quick Launch shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*";            DestDir: "{app}";              Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\icons\icon.ico";     DestDir: "{app}\assets\icons"; Flags: ignoreversion
Source: "assets\icons\icon_256.png"; DestDir: "{app}\assets\icons"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\{#AppName}";     Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\icons\icon.ico"; Tasks: desktopicon;   Comment: "Open Shuraksha Security Vault"
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\icons\icon.ico"; Tasks: startmenuicon; Comment: "Open Shuraksha Security Vault"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}";                                                   Tasks: startmenuicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunch

[Registry]
Root: HKCU; Subkey: "Software\{#AppRegName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}";           Flags: uninsdeletekey
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
begin
  Result := True;

  if RegQueryStringValue(
    HKCU,
    'Software\Shuraksha',
    'Version',
    OldVersion
  ) then begin
    if MsgBox(
      'Shuraksha version ' + OldVersion + ' is already installed.' +
      #13#10#13#10 +
      'Installing again will update the application files.' +
      #13#10 +
      'Your existing vault data will NOT be affected.' +
      #13#10#13#10 +
      'Do you want to continue?',
      mbConfirmation,
      MB_YESNO
    ) = IDNO then begin
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
  Response: Integer;
begin
  Result := True;

  Response := MsgBox(
    'Do you want to delete your encrypted vault data?' +
    #13#10#13#10 +
    'Click YES to permanently delete all vault files, passwords, and notes.' +
    #13#10 +
    'Click NO to keep your vault data on this computer.',
    mbConfirmation,
    MB_YESNO
  );

  if Response = IDYES then begin
    DelTree(
      ExpandConstant('{userappdata}\Shuraksha'),
      True, True, True
    );
  end;
end;