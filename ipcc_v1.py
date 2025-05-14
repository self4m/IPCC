import glob
import multiprocessing
import os
import shutil
import sys
import subprocess
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_JOBS = multiprocessing.cpu_count()


# 检查工具的可用性
def check_tools_usable():
    missing_tools = []

    # 检查 ipsw 是否可用
    if not shutil.which("ipsw"):
        missing_tools.append("ipsw")

    # 特别处理 7z，在 windwos 上用 7z 检查
    seven_zip_name = '7z' if sys.platform.startswith('win32') else '7zz'
    if not shutil.which(seven_zip_name):
        missing_tools.append(seven_zip_name)

    if not missing_tools:
        print("所有依赖工具检查通过，可以继续操作。")
        return

    # 输出缺失的工具信息
    print("错误：以下必需工具未找到，请先安装后再运行程序：")
    for tool in missing_tools:
        print(f"  - {tool} 工具未找到，请安装。")

    sys.exit(1)


# 处理ipsw文件
def process_ipsw(ipsw_file):
    display_name = os.path.basename(ipsw_file)
    print(f"[{display_name}] 开始处理...")

    ipsw_basename = display_name.replace(".ipsw", "")
    base_dir = os.path.join(os.getcwd(), ipsw_basename)
    payload_dir = os.path.join(base_dir, "Payload")
    ipcc_output_dir = os.path.join(base_dir, "ipcc")

    # 创建基础目录
    try:
        print(f"[{display_name}] 开始创建基础目录...")
        os.makedirs(base_dir, exist_ok=True)
    except PermissionError as e:
        print(f"[{display_name}]权限错误: 创建目录 {base_dir} 时发生错误. 错误信息: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[{display_name}]未知错误: 在创建目录 {base_dir} 时发生错误. 错误信息: {e}")
        sys.exit(1)

    # 强制清除旧的 Payload 和 ipcc 目录
    print(f"[{display_name}] 清除 Payload 和 ipcc 目录...")
    for d in [payload_dir, ipcc_output_dir]:
        try:
            if os.path.exists(d):
                shutil.rmtree(d)
            os.makedirs(d)
        except PermissionError as e:
            print(f"[{display_name}]权限错误: 没有足够的权限删除或创建目录 {d}. 错误信息: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[{display_name}]未知错误: 无法删除或创建目录 {d} 时发生错误. 错误信息: {e}")
            sys.exit(1)

    # 清理旧的 .aea 和 .dmg 文件
    print(f"[{display_name}] 清除 .aea 和 .dmg 文件...")
    for pattern in ['*.aea', '*.dmg']:
        for d in glob.glob(os.path.join(base_dir, pattern)):
            try:
                os.remove(d)
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"[{display_name}]未知错误: 无法删除文件 {d}. 错误信息: : {e}")
                sys.exit(1)

    # 解压 .ipsw 中的 AEA 文件
    try:
        print(f"[{display_name}] 开始获取 AEA 文件...")
        with zipfile.ZipFile(ipsw_file, 'r') as zip_ref:
            aea_files = [f for f in zip_ref.infolist() if f.filename.endswith('.aea')]
            if not aea_files:
                print(f"[{display_name}] 未找到 AEA 文件，跳过处理")
                return
            largest_aea = max(aea_files, key=lambda x: x.file_size)
            zip_ref.extract(largest_aea, base_dir)
            aea_path = os.path.join(base_dir, os.path.basename(largest_aea.filename))

        print(f"[{ipsw_basename}] 正在解密AEA文件...")
        try:
            subprocess.run(
                ["ipsw", "fw", "aea", aea_path, "-o", base_dir],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT
            )
        except Exception as e:
            print(f"[{display_name}]未知错误: 在解密AEA文件时发生错误. 错误信息: {e}")
            sys.exit(1)

        # 查找解密后的 DMG 文件
        dmg_file = next((f for f in glob.glob(os.path.join(base_dir, "*.dmg"))), None)
        if not dmg_file:
            print(f"[{display_name}] 未找到 DMG 文件")
            return

        # 提取运营商配置文件到 Payload 根目录下
        print(f"[{display_name}] 提取运营商配置文件...")
        temp_extract_dir = os.path.join(payload_dir, "_temp")
        os.makedirs(temp_extract_dir, exist_ok=True)

        seven_zip_command = {
            'win32': '7z',
            'darwin': '7zz',
            'linux': '7zz'
        }.get(sys.platform, '7zz')  # 默认为 '7zz'

        subprocess.run(
            [
                seven_zip_command, 'x', dmg_file,
                'System/Library/Carrier Bundles/iPhone/*.bundle/*',
                f'-o{temp_extract_dir}',
                '-y', '-r'
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 平铺 .bundle 结构到 Payload 根目录下
        carrier_root = os.path.join(temp_extract_dir, "System", "Library", "Carrier Bundles", "iPhone")
        if not os.path.exists(carrier_root):
            print(f"[{display_name}] 未找到运营商包目录")
            return

        for bundle_name in os.listdir(carrier_root):
            src_bundle_path = os.path.join(carrier_root, bundle_name)
            if not os.path.isdir(src_bundle_path):
                continue

            dst_bundle_path = os.path.join(payload_dir, bundle_name)
            os.makedirs(dst_bundle_path, exist_ok=True)

            # 复制并重命名文件到目标路径
            for item in os.listdir(src_bundle_path):
                src_item = os.path.join(src_bundle_path, item)
                dst_item = os.path.join(dst_bundle_path, item)
                if os.path.isfile(src_item):
                    shutil.copy2(src_item, dst_item)
                elif os.path.isdir(src_item):
                    shutil.copytree(src_item, dst_item, dirs_exist_ok=True)

        # 清理临时目录
        shutil.rmtree(temp_extract_dir, ignore_errors=True)
        print(f"[{display_name}] 运营商配置文件提取完成")

        # 使用标准结构打包 .ipcc
        for bundle_name in os.listdir(payload_dir):
            src_bundle = os.path.join(payload_dir, bundle_name)
            if not os.path.isdir(src_bundle) or not bundle_name.endswith('.bundle'):
                continue

            ipcc_file = os.path.join(ipcc_output_dir, f"{bundle_name}.ipcc")
            print(f"[{display_name}] 正在生成 {bundle_name}.ipcc")

            # 使用临时目录创建 Payload 结构
            with tempfile.TemporaryDirectory() as temp_dir:
                new_payload_dir = os.path.join(temp_dir, "Payload")
                os.makedirs(new_payload_dir, exist_ok=True)

                dst_bundle = os.path.join(new_payload_dir, bundle_name)
                shutil.copytree(src_bundle, dst_bundle)

                # 创建 .ipcc 文件
                with zipfile.ZipFile(ipcc_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        # 添加文件
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)

                        # 添加空目录
                        for dir_name in dirs:
                            dir_path = os.path.join(root, dir_name)
                            arcname = os.path.relpath(dir_path, temp_dir)
                            zipinfo = zipfile.ZipInfo(arcname + '/')
                            zipf.writestr(zipinfo, '')

        print(f"[{display_name}] 所有的 ipcc 文件已经打包完成")

    except subprocess.CalledProcessError as e:
        print(f"[{display_name}] 命令执行失败: {e.cmd}")
    except Exception as e:
        print(f"[{display_name}] 处理异常: {str(e)}")


def process_all_ipsw():
    # 查找ipsw文件位置
    ipsw_files = [
        os.path.join(os.getcwd(), f)
        for f in os.listdir()
        if f.lower().endswith('.ipsw')
    ]

    if not ipsw_files:
        print("当前目录未找到任何 IPSW 文件")
        return

    # 定义线程池
    with ThreadPoolExecutor(max_workers=MAX_JOBS) as executor:
        futures = {executor.submit(process_ipsw, f): f for f in ipsw_files}

        for future in as_completed(futures):
            file = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[{os.path.basename(file)}] 处理失败: {str(e)}")


# 主入口
if __name__ == "__main__":
    try:
        check_tools_usable()
        process_all_ipsw()
        print("所有文件处理完成！")
    except Exception as e:
        print(f"发生错误: {str(e)}")
        sys.exit(1)
