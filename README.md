# 一、项目说明

通过镜像文件获取运营商配置文件制作 ipcc 文件进行升级，以达到不更新系统升级 ipcc 版本的目的

## 操作方法

- 使用 `Python` 提取 `ipsw` 固件中的加密镜像文件
- 使用 `ipsw` 工具对其进行解密 （ios18 开始 Apple 对 ipsw 文件里面的 dmg 进行的加密处理）
- 通过 macOS 挂载或 `7z` 提取镜像内的运营商配置文件
- 按标准 `ipcc` 文件格式打包运营商配置文件，并通过 爱思助手 进行安装  

---

# 二、运行环境

## 1. Python 环境

Python 官方下载地址：https://www.python.org/downloads/

建议至少使用Python 3.8或更新的版本

- windwos

  推荐下载安装包进行安装，并勾选添加Path到环境变量

- linux macOS 

  系统默认安装python工具，无需再次安装


## 2. 7zip 解压缩工具

7zip 官方下载地址：https://www.7-zip.org/download.html

- macOS

  通过官网下载二进制安装包进行安装，**如果使用`mac.py`脚本处理可以不安装 7zip 工具**  

  ```bash
  # 下载二进制安装包到指定目录，以 7-Zip 25.01（2025-08-03）版本为例
  mkdir 7z && cd 7z && wget https://www.7-zip.org/a/7z2501-mac.tar.xz
  
  # 解压到当前目录的7z文件夹下
  tar -xJf 7z2501-mac.tar.xz
  
  # 赋予文件可执行权限
  chmod +x 7zz
  
  # 复制文件
  sudo cp 7zz /usr/local/bin/
  
  # 删除压缩包等内容
  cd .. && rm -rf 7z
  
  # 使用命令行时记得在设置 → 隐私与安全性 → 安全性 → 允许使用
  ```

- windows 

  官网下载 .exe 安装包进行安装并在 环境变量 → 系统 → Path 中添加 7z 的安装路径  

  ```text
  以 amd64 7-Zip 25.01（2025-08-03）版本为例，下载链接如下
  https://www.7-zip.org/a/7z2501-x64.exe
  ```

- linux

  通过官网下载二进制安装包进行安装

  ```bash
  # 下载二进制安装包到指定目录，以 amd64 7-Zip 25.01（2025-08-03）版本为例
  mkdir 7z && cd 7z && wget https://www.7-zip.org/a/7z2501-linux-x64.tar.xz
  
  # 解压到当前目录的7z文件夹下
  tar -xJf 7z2501-linux-x64.tar.xz
  
  # 赋予文件可执行权限
  chmod +x 7zz 7zzs
  
  # 复制文件
  sudo cp 7zz /usr/local/bin/ && sudo cp 7zzs /usr/local/bin/
  
  # 删除压缩包等内容
  cd .. && rm -rf 7z
  ```

## 3. IPSW 工具（提取 ios18 及以上系统版本时需要安装）

开源项目地址：https://github.com/blacktop/ipsw

### 3.1 macOS 

- 安装 brew 

  ```
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  brew update
  ```


- 安装 ipsw

  ```
  brew install ipsw
  ```

### 3.2 windows

- 安装 scoop

  ```
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
  ```

- 安装 ipsw

  ```
  scoop bucket add blacktop https://github.com/blacktop/scoop-bucket.git 
  scoop install blacktop/ipsw
  ```

### 3.3 linux

- 安装 snap

  ```
  # Ubuntu 可以跳过安装
  apt install snapd
  ```

- 安装 ipsw

  ```
  snap install ipsw
  ```

---

# 三、使用方法

1. git clone 仓库地址

```
git clone https://github.com/self4m/ipcc.git
```

2. 将`ipsw` 文件放入仓库的根目录

3. 执行脚本处理固件

   - macOS系统可以双击 `start.command` 或通过命令行运行 `python3 ipcc.py` 命令即可开始处理 

   - windows系统可以双击 `start.bat` 或通过命令行运行 `python ipcc.py` 命令即可开始处理

4. 等待脚本执行完毕

5. 打包完成的的 `ipcc` 文件将存储于 `ipcc` 目录下的 `ipsw` 固件同名文件夹中

# 四、注意

1. 如果 `ipcc` 目录下已存在 `ipsw` 固件同名文件夹则将删除目录以重新生成文件

2. 如果在脚本执行提取以及解密 aea 文件时发生错误，请检查剩余空间是否充足或再次尝试