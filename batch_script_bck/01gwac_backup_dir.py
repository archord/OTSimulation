import os
import subprocess


def getIpList():
    
    ipPrefix   =  '172.28.2.'
    
    ips = []
    for i in range(1,11):
        for j in range(1,6):
            ip = "%s%d%d"%(ipPrefix, i,j)
            ips.append(ip)
    return ips

# 定义远程服务器信息
remote_user = 'root'
remote_password = '123456'  # 注意：在实际应用中，硬编码密码是不安全的
remote_base_path = '/data3'
local_base_path = '/data/gwac_backup_50_data_process'

# 假设你已经通过某种方式处理了 SSH 免密登录，或者使用 SSH 密钥对进行了认证
# 这里我们直接调用 scp，不依赖 paramiko 的 SSH 隧道功能

# 生成远程服务器 IP 列表
remote_ips = getIpList()

# 遍历每个远程服务器
for remote_ip in remote_ips:
    # 构造本地目录名称，确保是三位数（前面补0）
    local_dir_suffix = f'{int(remote_ip.split(".")[-1]):03d}'
    local_dir = os.path.join(local_base_path, f'G{local_dir_suffix}')
    
    # 创建本地目录（如果不存在）
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    
    # 构造 scp 命令
    scp_command = f'scp  -o StrictHostKeyChecking=no -r {remote_user}@{remote_ip}:{remote_base_path} {local_dir}/'
    
    # 执行 scp 命令
    try:
        subprocess.run(scp_command, shell=True, check=True)
        print(f"Completed transfer for {remote_ip} to {local_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to transfer for {remote_ip}: {e}")

print("All transfers completed.")