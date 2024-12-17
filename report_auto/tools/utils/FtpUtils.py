import ftplib
import logging
import os


class FTPUploader:
    def __init__(self, ftp_host, ftp_user, ftp_password, remote_root_dir):
        self.ftp_host = ftp_host
        self.ftp_user = ftp_user
        self.ftp_password = ftp_password
        self.remote_root_dir = remote_root_dir
        self.ftp = None
        # 配置日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def connect(self):
        """连接到FTP服务器"""
        try:
            self.ftp = ftplib.FTP(self.ftp_host)
            self.ftp.login(user=self.ftp_user, passwd=self.ftp_password)
            logging.info(f"Connected to FTP server at {self.ftp_host}")
        except Exception as e:
            logging.error(f"Failed to connect to FTP server: {e}")
            raise

    def disconnect(self):
        """断开与FTP服务器的连接"""
        if self.ftp:
            self.ftp.quit()
            logging.info("Disconnected from FTP server")

    def create_remote_directory(self, path):
        """在远程服务器上创建目录"""
        try:
            self.ftp.mkd(path)
            logging.info(f"Created directory on FTP server: {path}")
        except ftplib.error_perm as e:
            # 目录已经存在
            if not str(e).startswith('550'):
                logging.error(f"Error creating directory {path}: {e}")
                raise

    def upload_file(self, local_path, remote_path):
        """上传文件到远程服务器"""
        try:
            with open(local_path, 'rb') as file:
                self.ftp.storbinary(f'STOR {remote_path}', file)
            logging.info(f"Uploaded file to FTP server: {local_path} -> {remote_path}")
        except Exception as e:
            logging.error(f"Failed to upload file {local_path}: {e}")

    def traverse_and_upload(self, local_root_dir):
        """遍历本地目录并上传文件到远程服务器"""
        for root, dirs, files in os.walk(local_root_dir):
            relative_path = os.path.relpath(root, local_root_dir)
            remote_path = os.path.join(self.remote_root_dir, relative_path)

            # 创建远程目录
            if relative_path != '.':
                self.create_remote_directory(remote_path)

            # 上传文件
            for file_name in files:
                local_file_path = os.path.join(root, file_name)
                remote_file_path = os.path.join(remote_path, file_name)
                self.upload_file(local_file_path, remote_file_path)

    def upload_directory(self, local_root_dir):
        """上传整个目录及其子目录和文件"""
        try:
            self.connect()
            self.traverse_and_upload(local_root_dir)
        finally:
            self.disconnect()


# 示例用法
if __name__ == "__main__":
    # 配置FTP服务器信息
    ftp_host = 'your_ftp_server_address'
    ftp_user = 'your_ftp_username'
    ftp_password = 'your_ftp_password'
    remote_root_dir = '/remote/directory/path'

    # 本地顶级父目录
    local_root_dir = r'C:\Users\Administrator\Downloads\output'

    uploader = FTPUploader(ftp_host, ftp_user, ftp_password, remote_root_dir)
    uploader.upload_directory(local_root_dir)
