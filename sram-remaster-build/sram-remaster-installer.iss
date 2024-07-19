#define MyAppName "SRAM Remaster"
#define MyAppVersion "1.0"
#define MyAppPublisher "Charles-Philippe Bernard"
#define MyAppURL "https://github.com/frangin2003"
#define MyAppExeName "start_game.exe"

[Setup]
AppId={{12345678-1234-1234-1234-123456789012}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={pf}\SRAM remaster
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=Setup
SetupIconFile=installer\icon.ico
WizardImageFile=installer\largebackground.bmp
WizardSmallImageFile=installer\smallbackground.bmp
Compression=lzma
SolidCompression=yes
ExtraDiskSpaceRequired=6551502848

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "game\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{commondesktop}\SRAM Remaster"; Filename: "{app}\start_game.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\start_game.exe"; Description: "Start {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
var
  LogMemo: TMemo;

procedure LogMessage(const Msg: string);
begin
  Log(Msg);
  if LogMemo <> nil then
  begin
    LogMemo.Lines.Add(Msg);
  end;
end;

function OnDownloadProgress(const Url, Filename: string; const Progress, ProgressMax: Int64): Boolean;
begin
  if ProgressMax <> 0 then
    LogMessage(Format('  %d of %d bytes done.', [Progress, ProgressMax]))
  else
    LogMessage(Format('  %d bytes done.', [Progress]));
  Result := True;
end;

procedure DownloadAndInstallOllama();
var
  ResultCode: Integer;
begin
  if MsgBox('Do you want to download and install Ollama?', mbConfirmation, MB_YESNO) = IDYES then
  begin
    LogMessage('Downloading Ollama...');
    WizardForm.StatusLabel.Caption := 'Downloading Ollama...';
    WizardForm.ProgressGauge.Style := npbstMarquee;
    try
      DownloadTemporaryFile('https://ollama.com/download/OllamaSetup.exe', 'OllamaSetup.exe', '', @OnDownloadProgress);
    finally
      WizardForm.ProgressGauge.Style := npbstNormal;
    end;
    
    LogMessage('Installing Ollama...');
    WizardForm.StatusLabel.Caption := 'Installing Ollama...';
    Exec(ExpandConstant('{tmp}\OllamaSetup.exe'), '', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    if ResultCode = 0 then
    begin
      LogMessage('Ollama installed successfully.');
      MsgBox('Ollama has been successfully installed.', mbInformation, MB_OK);
    end
    else
    begin
      LogMessage('Ollama installation failed.');
      MsgBox('Ollama installation failed. Setup will now exit.', mbError, MB_OK);
      Abort();
    end;
  end
  else
  begin
    MsgBox('Ollama installation skipped. Some features may not be available.', mbInformation, MB_OK);
  end;
end;

procedure InstallLlama3();
var
  ResultCode: Integer;
begin
  LogMessage('Installing Llama3 8b...');
  MsgBox('Now installing Llama3 8b model... Close the window when you see the ">>>" invite', mbInformation, MB_OK);
  WizardForm.StatusLabel.Caption := 'Installing Llama3 8b...';
  Exec('cmd.exe', '/C ollama run llama3', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
  LogMessage('Llama3 8b installed successfully.');
end;

procedure InitializeWizard();
begin
  LogMemo := TMemo.Create(WizardForm);
  LogMemo.Parent := WizardForm;
  LogMemo.Left := 0;
  LogMemo.Top := 200;
  LogMemo.Width := WizardForm.ClientWidth;
  LogMemo.Height := WizardForm.ClientHeight - 272;
  LogMemo.ScrollBars := ssVertical;
  LogMemo.ReadOnly := True;
  LogMemo.Color := clBtnFace;
  LogMessage('Installer initialized.');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    LogMessage('Starting installation process...');
    LogMessage('The installation will take:');
    LogMessage('Game=700MB');
    LogMessage('Ollama=2GB');
    LogMessage('Llama3-8b=4.1GB');
    DownloadAndInstallOllama();
    InstallLlama3();
  end;
end;