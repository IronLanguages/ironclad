FROM mcr.microsoft.com/devcontainers/dotnet:1-6.0
#                                           ^ == bookworm

SHELL ["bash", "-c"]

# Install IronPython
RUN sudo -u vscode -i dotnet tool install --global ironpython.console --version 3.4.1

# Install Python and other build tools
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get -q update && apt-get -q -y upgrade && \
    # these four should have already be installed by the source image, but listed here for clarity
    apt-get -q -y install lsb-release wget gnupg git && \
    apt-get -q -y install software-properties-common && \
    apt-get -q -y install python3-pip && \
    apt-get -q -y install python-is-python3 && \
    apt-get -q -y install scons && \
    apt-get -q -y install castxml python3-pygccxml && \
    apt-get -q -y install nasm && \
    true

# Install Clang/LLVM ver. 16 directly from LLVM repos
RUN ver=16 && \
    wget -nv https://apt.llvm.org/llvm.sh -O /usr/local/sbin/llvm-install.sh && \
    chmod +x /usr/local/sbin/llvm-install.sh && \
    llvm-install.sh $ver && \
    echo if '[[ "$PATH" != *:/usr/lib/llvm-* ]];' then export PATH=\"/usr/lib/llvm-$ver/bin:\$PATH\"\; fi >>/etc/bash.bashrc && \
    true

# Install Anaconda3 v2.3 with Python 3.4.3
RUN wget --progress=dot:giga https://repo.anaconda.com/archive/Anaconda3-2.3.0-Linux-x86_64.sh && \
    bash Anaconda3-2.3.0-Linux-x86_64.sh -b -p /opt/anaconda3 && \
    rm Anaconda3-2.3.0-Linux-x86_64.sh && \
    true
