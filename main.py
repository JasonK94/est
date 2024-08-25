import os
import sys
import paramiko
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLineEdit, QFileDialog,
                             QLabel, QInputDialog, QListWidget, QTextEdit)
os.environ['R_HOME'] = 'C:\\Program Files\\R\\R-4.3.3'
from PyQt5.QtCore import Qt
import rpy2.robjects as ro
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.ssh_client = None

    def initUI(self):
        self.setWindowTitle('Remote Data Loader')

        layout = QVBoxLayout()

        # Status box
        self.status_box = QTextEdit(self)
        self.status_box.setReadOnly(True)
        self.status_box.setFixedHeight(50)
        layout.addWidget(self.status_box)

        # Input fields for connection
        self.ip_input = QLineEdit(self)
        self.ip_input.setPlaceholderText('Server IP')
        layout.addWidget(self.ip_input)

        self.port_input = QLineEdit(self)
        self.port_input.setPlaceholderText('Port')
        layout.addWidget(self.port_input)

        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText('Username')
        layout.addWidget(self.user_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText('Password')
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.connect_btn = QPushButton('Connect to Server', self)
        self.connect_btn.clicked.connect(self.connect_to_server)
        layout.addWidget(self.connect_btn)

        self.load_data_btn = QPushButton('Load Data', self)
        self.load_data_btn.clicked.connect(self.load_data)
        layout.addWidget(self.load_data_btn)

        self.file_list_widget = QListWidget(self)
        layout.addWidget(self.file_list_widget)

        # Error box
        self.error_box = QTextEdit(self)
        self.error_box.setReadOnly(True)
        self.error_box.setFixedHeight(50)
        layout.addWidget(self.error_box)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def connect_to_server(self):
        ip = self.ip_input.text()
        port = int(self.port_input.text())
        username = self.user_input.text()
        password = self.password_input.text()

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.ssh_client.connect(ip, port, username, password)
            self.status_box.setText(f"Connected to {ip}")
        except Exception as e:
            self.status_box.setText(f"Connection failed: {str(e)}")
            self.ssh_client = None  # Reset ssh_client if connection failed

    def load_data(self):
        if self.ssh_client is None:
            self.error_box.setText("Please connect to the server first.")
            return

        remote_dir = '/'  # Default starting remote directory
        self.populate_file_list(remote_dir)

    def populate_file_list(self, remote_dir):
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(f'ls -p {remote_dir}')
            file_list = stdout.read().decode().splitlines()
            self.file_list_widget.clear()
            for file in file_list:
                self.file_list_widget.addItem(f"{remote_dir}{file}")
            self.file_list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        except Exception as e:
            self.error_box.setText(f"Failed to retrieve file list: {str(e)}")

    def on_item_double_clicked(self, item):
        selected_item = item.text()
        if selected_item.endswith('/'):
            # If it's a directory, open it
            self.populate_file_list(selected_item)
        else:
            # If it's a file, process it
            self.run_r_script_on_server(selected_item)

    def run_r_script_on_server(self, file_path):
        try:
            r_command = f'Rscript -e "data <- Seurat::Read10X(data=\'{file_path}\'); summary(data)"'
            stdin, stdout, stderr = self.ssh_client.exec_command(r_command)
            result = stdout.read().decode()
            self.error_box.setText(result)
        except Exception as e:
            self.error_box.setText(f"Failed to run R script: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())