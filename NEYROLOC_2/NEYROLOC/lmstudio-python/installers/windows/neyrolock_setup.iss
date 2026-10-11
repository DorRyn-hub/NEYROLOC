; NEYROLOCK Windows Installer Script
; Created with Inno Setup
; Улучшенная версия с детальным прогрессом установки

#define MyAppName "NEYROLOCK"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "NEYROLOCK Team"
#define MyAppURL "https://github.com/neyrolock/neyrolock"
#define MyAppExeName "NEYROLOCK.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
OutputDir=..\output
OutputBaseFilename=NEYROLOCK-{#MyAppVersion}-Windows-Setup
SetupIconFile=..\..\assets\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes
; Улучшенный интерфейс установки
WizardImageFile=compiler:WizModernImage-IS.bmp
WizardSmallImageFile=compiler:WizModernSmallImage-IS.bmp
; Показывать детальный прогресс
ShowTasksTreeLines=yes
AlwaysShowDirOnReadyPage=yes
AlwaysShowGroupOnReadyPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main application files from PyInstaller output
Source: "..\..\dist\NEYROLOCK\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Documentation
Source: "..\..\PROJECT_DOCUMENTATION.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Documentation"; Filename: "{app}\PROJECT_DOCUMENTATION.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\NEYROLOCK"

[Code]
var
  ProgressPage: TOutputProgressWizardPage;

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  PythonPath: String;
begin
  Result := True;

  // Check if Python is installed (optional - PyInstaller bundles Python)
  // This is just informational
  if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonPath) or
     RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonPath) or
     RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', PythonPath) then
  begin
    Log('Python found at: ' + PythonPath);
  end
  else
  begin
    Log('Python not found in registry (not required - app is standalone)');
  end;
end;

procedure InitializeWizard();
begin
  WizardForm.LicenseAcceptedRadio.Checked := True;

  // Создаем страницу с детальным прогрессом
  ProgressPage := CreateOutputProgressPage('Подготовка к установке', 'Пожалуйста, подождите...');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  I: Integer;
begin
  if CurStep = ssInstall then
  begin
    // Показываем прогресс подготовки
    ProgressPage.SetText('Подготовка файлов для установки...', '');
    ProgressPage.SetProgress(0, 100);
    ProgressPage.Show;

    try
      // Имитация этапов установки для показа прогресса
      for I := 1 to 20 do
      begin
        Sleep(50);
        ProgressPage.SetProgress(I * 5, 100);
      end;

      ProgressPage.SetText('Установка NEYROLOCK...', 'Копирование файлов приложения');
      Sleep(100);

    finally
      ProgressPage.Hide;
    end;
  end;

  if CurStep = ssPostInstall then
  begin
    ProgressPage.SetText('Завершение установки...', 'Создание ярлыков и регистрация');
    ProgressPage.SetProgress(90, 100);
    ProgressPage.Show;

    try
      Sleep(500);
      ProgressPage.SetProgress(100, 100);
    finally
      ProgressPage.Hide;
    end;
  end;
end;

