import os
import sys
import zipfile
import subprocess
import multiprocessing
import plistlib
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import tempfile

MAX_JOBS = multiprocessing.cpu_count()

# 检查工具的可用性
def check_tools_usable():
    if sys.platform != 'darwin':
        print("此脚本仅适用于 macOS 系统。")
        sys.exit(1)

    if not shutil.which('ipsw'):
        print("错误：ipsw 工具未找到，请安装后再运行程序。")
        sys.exit(1)

    print("所有依赖工具检查通过，可以继续操作。")

def process_ipsw(ipsw_file):
    display_name = os.path.basename(ipsw_file)
    print(f"[{display_name}] 开始处理...")

    ipsw_basename = display_name.replace(".ipsw", "")
    base_dir = os.path.join(os.getcwd(), ipsw_basename)
    ipcc_output_dir = os.path.join(os.getcwd(), "ipcc", ipsw_basename)

    # 如果 ipcc_output_dir 已存在，说明已处理过，跳过该文件
    if os.path.exists(ipcc_output_dir):
        print(f"[{display_name}] 该文件在 ipcc 文件夹中已存在处理完成的内容，跳过处理。")
        return

    os.makedirs(ipcc_output_dir, exist_ok=True)

    try:
        print(f"[{display_name}] 解压 AEA 文件...")
        with zipfile.ZipFile(ipsw_file, 'r') as zip_ref:
            aea_files = [f for f in zip_ref.infolist() if f.filename.endswith('.aea')]
            if not aea_files:
                print(f"[{display_name}] 未找到 AEA 文件，跳过")
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

        dmg_file = next((f for f in glob.glob(os.path.join(base_dir, "*.dmg"))), None)
        if not dmg_file:
            print(f"[{ipsw_basename}] 解密失败，未生成 DMG 文件")
            return

        print(f"[{ipsw_basename}] 挂载 DMG 镜像...")
        mount_result = subprocess.run(
            ["hdiutil", "attach", "-plist", "-nobrowse", "-noverify", "-readonly", dmg_file],
            capture_output=True,
            check=True
        )

        plist_data = plistlib.loads(mount_result.stdout)
        mount_point = next(
            (e["mount-point"] for e in plist_data.get("system-entities", []) if "mount-point" in e),
            None
        )

        if not mount_point or not os.path.exists(mount_point):
            print(f"[{ipsw_basename}] 挂载失败，找不到挂载点")
            return

        try:
            carrier_path = os.path.join(mount_point, "System", "Library", "Carrier Bundles", "iPhone")
            if not os.path.isdir(carrier_path):
                print(f"[{ipsw_basename}] 未找到运营商包目录")
                return

            for bundle_name in os.listdir(carrier_path):
                bundle_path = os.path.join(carrier_path, bundle_name)
                if not os.path.isdir(bundle_path) or not bundle_name.endswith('.bundle'):
                    continue

                ipcc_file = os.path.join(ipcc_output_dir, f"{bundle_name}.ipcc")
                print(f"[{ipsw_basename}] 生成 {bundle_name}.ipcc")

                with tempfile.TemporaryDirectory() as temp_dir:
                    payload_dir = os.path.join(temp_dir, "Payload")
                    os.makedirs(payload_dir, exist_ok=True)

                    dst_bundle_path = os.path.join(payload_dir, bundle_name)
                    shutil.copytree(bundle_path, dst_bundle_path)

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

        finally:
            print(f"[{ipsw_basename}] 卸载 DMG...")
            subprocess.run(
                ["hdiutil", "detach", mount_point, "-force"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                check=False
            )
            os.remove(dmg_file)

        print(f"[{display_name}] ipcc 文件已打包完成")

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
                print(f"[{os.path.basename(file)}] 处理失败: {str(e)}")

if __name__ == "__main__":
    try:
        check_tools_usable()
        process_all_ipsw()
        print("所有文件处理完成！")
    except Exception as e:
        print(f"发生错误: {str(e)}")
        sys.exit(1)
