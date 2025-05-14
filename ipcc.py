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

    if not shutil.which("ipsw"):
        missing_tools.append("ipsw")

    seven_zip_name = '7z' if sys.platform.startswith('win32') else '7zz'
    if not shutil.which(seven_zip_name):
        missing_tools.append(seven_zip_name)

    if not missing_tools:
        print("所有依赖工具检查通过，可以继续操作。")
        return

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
    ipcc_output_dir = os.path.join(os.getcwd(), "ipcc", ipsw_basename)

    # 如果 ipcc_output_dir 已存在，说明已处理过，跳过该文件
    if os.path.exists(ipcc_output_dir):
        print(f"[{display_name}] 该文件在 ipcc 文件夹中已存在处理完成的内容，跳过处理。")
        return

    os.makedirs(ipcc_output_dir, exist_ok=True)

    # 解压 .ipsw 中的 AEA 文件
    try:
        print(f"[{display_name}] 获取 AEA 文件中...")
        with zipfile.ZipFile(ipsw_file, 'r') as zip_ref:
            aea_files = [f for f in zip_ref.infolist() if f.filename.endswith('.aea')]
            if not aea_files:
                print(f"[{display_name}] 未找到 AEA 文件，跳过处理")
                return
            largest_aea = max(aea_files, key=lambda x: x.file_size)
            zip_ref.extract(largest_aea, base_dir)
            aea_path = os.path.join(base_dir, os.path.basename(largest_aea.filename))

        print(f"[{ipsw_basename}] 解密 AEA 文件...")
        subprocess.run(
            ["ipsw", "fw", "aea", aea_path, "-o", base_dir],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )

        os.remove(aea_path)

        # 查找解密后的 DMG 文件
        dmg_file = next((f for f in glob.glob(os.path.join(base_dir, "*.dmg"))), None)
        if not dmg_file:
            print(f"[{display_name}] 未找到 DMG 文件")
            return

        # 提取运营商配置文件到 Payload 根目录
        print(f"[{display_name}] 提取运营商配置文件...")
        temp_extract_dir = os.path.join(payload_dir, "_temp")
        os.makedirs(temp_extract_dir, exist_ok=True)

        seven_zip_command = {
            'win32': '7z',
            'darwin': '7zz',
            'linux': '7zz'
        }.get(sys.platform, '7zz')

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
        os.remove(dmg_file)

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

            for item in os.listdir(src_bundle_path):
                src_item = os.path.join(src_bundle_path, item)
                dst_item = os.path.join(dst_bundle_path, item)
                if os.path.isfile(src_item):
                    shutil.copy2(src_item, dst_item)
                elif os.path.isdir(src_item):
                    shutil.copytree(src_item, dst_item, dirs_exist_ok=True)

        shutil.rmtree(temp_extract_dir, ignore_errors=True)
        print(f"[{display_name}] 运营商配置文件提取完成")

        # 打包 ipcc 文件
        for bundle_name in os.listdir(payload_dir):
            src_bundle = os.path.join(payload_dir, bundle_name)
            if not os.path.isdir(src_bundle) or not bundle_name.endswith('.bundle'):
                continue

            ipcc_file = os.path.join(ipcc_output_dir, f"{bundle_name}.ipcc")
            print(f"[{display_name}] 生成 {bundle_name}.ipcc...")

            with tempfile.TemporaryDirectory() as temp_dir:
                new_payload_dir = os.path.join(temp_dir, "Payload")
                os.makedirs(new_payload_dir, exist_ok=True)

                dst_bundle = os.path.join(new_payload_dir, bundle_name)
                shutil.copytree(src_bundle, dst_bundle)

                with zipfile.ZipFile(ipcc_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
                        for dir_name in dirs:
                            dir_path = os.path.join(root, dir_name)
                            arcname = os.path.relpath(dir_path, temp_dir)
                            zipinfo = zipfile.ZipInfo(arcname + '/')
                            zipf.writestr(zipinfo, '')

        print(f"[{display_name}] 所有 ipcc 文件打包完成")

        shutil.rmtree(base_dir)

    except subprocess.CalledProcessError as e:
        print(f"[{display_name}] 子进程命令执行失败: {e.cmd}")
        shutil.rmtree(ipcc_output_dir)
    except Exception as e:
        print(f"[{display_name}] 处理异常: {e}")

def process_all_ipsw():
    ipsw_files = [
        os.path.join(os.getcwd(), f)
        for f in os.listdir()
        if f.lower().endswith('.ipsw')
    ]

    if not ipsw_files:
        print("当前目录未找到任何 IPSW 文件")
        return

    with ThreadPoolExecutor(max_workers=MAX_JOBS) as executor:
        futures = {executor.submit(process_ipsw, f): f for f in ipsw_files}
        for future in as_completed(futures):
            file = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[{os.path.basename(file)}] 处理失败: {e}")

if __name__ == "__main__":
    try:
        check_tools_usable()
        process_all_ipsw()
        print("所有文件处理完成！")
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)
