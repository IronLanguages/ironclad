FROM mcr.microsoft.com/dotnet/framework/runtime:4.8.1

SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

# Install VS Build Tools
RUN Invoke-WebRequest -UseBasicParsing https://aka.ms/vs/17/release/vs_buildtools.exe -OutFile vs_BuildTools.exe; \
    # Installer won't detect DOTNET_SKIP_FIRST_TIME_EXPERIENCE if ENV is used, must use setx /M
    setx /M DOTNET_SKIP_FIRST_TIME_EXPERIENCE 1; \
    Start-Process vs_BuildTools.exe '--quiet --wait --norestart --nocache \
        --add Microsoft.VisualStudio.Workload.VCTools \
        --add Microsoft.NetCore.Component.SDK \
        --add Microsoft.Component.VC.Runtime.UCRTSDK \
        --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 \
        --add Microsoft.VisualStudio.Component.Windows10SDK.19041 \
        --add Microsoft.VisualStudio.Component.VC.Llvm.Clang \
        ' -NoNewWindow -Wait

RUN Invoke-WebRequest -UseBasicParsing https://github.com/brechtsanders/winlibs_mingw/releases/download/12.2.0-15.0.7-10.0.0-msvcrt-r4/winlibs-x86_64-posix-seh-gcc-12.2.0-mingw-w64msvcrt-10.0.0-r4.zip -OutFile winlibs.zip; \
    Expand-Archive winlibs.zip -DestinationPath C:\; \
    Remove-Item winlibs.zip; \
    setx /M PATH $($env:PATH + ';C:\mingw64\bin')

# Install Chocolatey and other tools bootstraping the rest of installation
RUN Set-ExecutionPolicy Bypass -Scope Process -Force; \
    # ensure a minimum of TLS 1.2
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; \
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1')); \
        choco install -y python311; \
        choco install -y 7zip; \
        ;

# Install "Windows® SDK for Windows® 7 and .NET Framework 4"
RUN Invoke-WebRequest -UseBasicParsing https://download.microsoft.com/download/F/1/0/F10113F5-B750-4969-A255-274341AC6BCE/GRMSDKX_EN_DVD.iso -OutFile GRMSDKX_EN_DVD.iso; \
    7z.exe x -oWin71SDK GRMSDKX_EN_DVD.iso; \
    Remove-Item GRMSDKX_EN_DVD.iso; \
    Write-Output 'Installing Windows 7 SDK, it can take a while...'; \
    Start-Process \Win71SDK\setup.exe '-q -params:ADDLOCAL=ALL' -NoNewWindow -Wait; \
    Remove-Item -Recurse Win71SDK; \
    ;

# Install "Microsoft Visual C++ 2010 Service Pack 1 Compiler Update for the Windows SDK 7.1"
RUN Invoke-WebRequest -UseBasicParsing https://download.microsoft.com/download/7/5/0/75040801-126C-4591-BCE4-4CD1FD1499AA/VC-Compiler-KB2519277.exe -OutFile VC-Compiler-KB2519277.exe; \
    Write-Output 'Installing MSVC 2010 SP1...'; \
    Start-Process \VC-Compiler-KB2519277.exe '-q' -NoNewWindow -Wait; \
    Remove-Item VC-Compiler-KB2519277.exe; \
    ;

# Install Python packages
RUN py -m pip install --upgrade pip; \
    py -m pip install scons; \
    py -m pip install castxml pygccxml; \
    ;

# Install IronPython and build dependencies
RUN \
    choco install -y vcredist2010; \
    choco install -y python3 --version 3.4.4.20200110; \
    choco install -y ironpython --version 3.4.1; \
    New-Item -Path C:\ProgramData\chocolatey\bin -Name ipyfmwk.exe -ItemType SymbolicLink -Value C:\ProgramData\chocolatey\bin\ipy.exe; \
    dotnet tool install --global ironpython.console --version 3.4.1; \
    ;

SHELL ["cmd.exe", "/C"]
CMD powershell.exe
