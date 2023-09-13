FROM mcr.microsoft.com/windows:ltsc2019

SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

# Install VS Build Tools
RUN Invoke-WebRequest -UseBasicParsing https://aka.ms/vs/16/release/vs_buildtools.exe -OutFile vs_BuildTools.exe; \
    # Installer won't detect DOTNET_SKIP_FIRST_TIME_EXPERIENCE if ENV is used, must use setx /M
    setx /M DOTNET_SKIP_FIRST_TIME_EXPERIENCE 1; \
    Start-Process vs_BuildTools.exe '--quiet --wait --norestart --nocache \
        --add Microsoft.VisualStudio.Workload.VCTools \
        --add Microsoft.NetCore.Component.SDK \
        --add Microsoft.Component.VC.Runtime.UCRTSDK \
        --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 \
        --add Microsoft.VisualStudio.Component.Windows10SDK.19041' \
        -NoNewWindow -Wait

RUN Invoke-WebRequest -UseBasicParsing https://github.com/brechtsanders/winlibs_mingw/releases/download/12.2.0-15.0.7-10.0.0-msvcrt-r4/winlibs-x86_64-posix-seh-gcc-12.2.0-mingw-w64msvcrt-10.0.0-r4.zip -OutFile winlibs.zip; \
    Expand-Archive winlibs.zip -DestinationPath C:\; \
    Remove-Item winlibs.zip

RUN setx /M PATH $($env:PATH + ';C:\mingw64\bin')

RUN Set-ExecutionPolicy Bypass -Scope Process -Force; \
    # ensure a minimum of TLS 1.2
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; \
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1')); \
        choco install -y python3

RUN py -m pip install scons castxml pygccxml

RUN choco install -y python3 --version 3.4.4.20200110 --side-by-side; \
    choco install -y ironpython --version 3.4.1
