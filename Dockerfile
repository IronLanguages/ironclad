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

RUN Invoke-WebRequest -UseBasicParsing -UserAgent "Wget" https://sourceforge.net/projects/mingw/files/Installer/mingw-get/mingw-get-0.6.2-beta-20131004-1/mingw-get-0.6.2-mingw32-beta-20131004-1-bin.zip/download -OutFile mingw-get-0.6.2-mingw32-beta-20131004-1-bin.zip; \
    Expand-Archive mingw-get-0.6.2-mingw32-beta-20131004-1-bin.zip MinGW; \
    C:\MinGW\bin\mingw-get.exe update; \
    C:\MinGW\bin\mingw-get.exe install mingw32-base mingw32-gcc-g++ msys-base mingw32-pexports	

RUN Invoke-WebRequest -UseBasicParsing https://www.nasm.us/pub/nasm/releasebuilds/2.16.01/win32/nasm-2.16.01-installer-x86.exe -OutFile nasm-2.16.01-installer-x86.exe; \
    C:\nasm-2.16.01-installer-x86.exe /S /AllUsers

RUN setx /M PATH $($env:PATH + ';C:\MinGW\bin;C:\Program Files (x86)\NASM')

RUN Set-ExecutionPolicy Bypass -Scope Process -Force; \
    # ensure a minimum of TLS 1.2
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; \
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1')); \
        choco install -y python3

RUN py -m pip install scons castxml pygccxml

RUN choco install -y python2 -ForceX86; \
    choco install -y ironpython --version 2.7.12
