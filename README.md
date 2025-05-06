# 一、操作说明

使用 `Python` 提取 `ipsw` 固件中加密的镜像文件  

使用 `ipsw` 工具对加密的镜像文件进行解密  

使用 `7z` 提取镜像文件中相关的运营商配置文件  

按照标准的 `ipcc` 文件格式打包运营商配置文件  

---

# 二、运行环境

## 1. 包管理器工具

- windwos 安装 scoop

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

- linux 安装 snap （Ubuntu 可以跳过）

```bash
apt install snapd
```

- macOS 安装 brew 

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew update
```



## 2. Python 环境

Python 官方下载地址：https://www.python.org/downloads/

建议至少使用Python 3.8或更新的版本

- windwos

  推荐下载安装包进行安装，并勾选添加Path到环境变量

- linux macOS 

  系统默认安装python工具，无需安装

  

## 3. 7zip 解压缩工具

7zip 官方下载地址：https://www.7-zip.org/download.html

- windows 

  下载安装包进行安装并在 环境变量 → 系统 → Path 中添加 7z 的安装路径

- linux

  官网下载二进制安装包进行安装

  包管理器版本过于老旧！包管理器版本过于老旧！包管理器版本过于老旧！

  ```bash
  # 下载二进制安装包到指定目录，以 7-Zip 24.09 (2024-11-29) 版本为例
  mkdir 7z && cd 7z && wget https://www.7-zip.org/a/7z2409-linux-x64.tar.xz
  
  # 解压到当前目录的7z文件夹下
  tar -xJf 7z2409-linux-x64.tar.xz
  
  # 赋予文件可执行权限
  chmod +x 7zz 7zzs
  
  # 复制文件
  sudo cp 7zz /usr/local/bin/ && sudo cp 7zzs /usr/local/bin/
  
  # 删除压缩包等内容
  cd .. && rm -rf 7z
  ```

- macOS

  官网下载二进制安装包进行安装
  
  包管理器版本过于老旧！包管理器版本过于老旧！包管理器版本过于老旧！

  ```bash
  # 下载二进制安装包到指定目录，以 7-Zip 24.09 (2024-11-29) 版本为例
  mkdir 7z && cd 7z && wget https://www.7-zip.org/a/7z2409-mac.tar.xz
  
  # 解压到当前目录的7z文件夹下
  tar -xJf 7z2409-mac.tar.xz
  
  # 赋予文件可执行权限
  chmod +x 7zz
  
  # 复制文件
  sudo cp 7zz /usr/local/bin/
  
  # 删除压缩包等内容
  cd .. && rm -rf 7z
  
  # 使用命令行时记得在设置 → 隐私与安全性 → 安全性 → 允许使用
  ```
  
  

## 4. IPSW 工具

开源项目地址：https://github.com/blacktop/ipsw

- windows

```powershell
scoop bucket add blacktop https://github.com/blacktop/scoop-bucket.git 
scoop install blacktop/ipsw
```

- linux

```bash
snap install ipsw
```

- macOS 

```bash
brew install ipsw
```

---


# 三、使用方法
1. git clone 仓库地址
```
git clone https://github.com/self4m/ipcc.git
```
2. 将`ipsw` 文件放入仓库的根目录

3. 执行脚本处理固件

   - 双击执行

     > windows  `start.bat` 即可开始处理
     >
     > macOS 双击 `start.command` 即可开始处理

   - 命令行执行

     >windows 在 PowerShell 中执行 `python ipcc.py` 命令即可开始处理
     >
     >linux macOS 在 Tetminal 中执行 `python3 ipcc.py` 命令即可开始处理

4. 等待脚本执行完毕
5. 打包的 `ipcc` 文件存储于 `ipsw`  固件同名文件夹中的 `ipcc`  目录下
# 四、注意
1. 每次执行脚本都会删除上一次生成的所有文件，如果存在的话
2. 如果在脚本执行提取以及解密 aea 文件时发生错误，请检查剩余空间是否充足或再次尝试
