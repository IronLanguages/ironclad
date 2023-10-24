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

RUN Set-ExecutionPolicy Bypass -Scope Process -Force; \
    # ensure a minimum of TLS 1.2
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; \
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1')); \
        choco install -y python311

RUN py -m pip install --upgrade pip; \
    py -m pip install scons; \
    py -m pip install castxml pygccxml; \
    ;

RUN \
    choco install -y vcredist2010; \
    choco install -y python3 --version 3.4.4.20200110; \
    choco install -y ironpython --version 3.4.1; \
    ;

SHELL ["cmd.exe", "/C"]
CMD "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64 && powershell