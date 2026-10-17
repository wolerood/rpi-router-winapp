from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from api_client import ApiClient, ApiError
from config import REQUEST_TIMEOUT
from settings import ClientSettings


ACCESS_MODE_TEXT = {
    "schedule": "По расписанию",
    "always_allow": "Всегда разрешать",
    "always_block": "Всегда блокировать",
}

ACCESS_MODE_VALUES = {
    "По расписанию": "schedule",
    "Всегда разрешать": "always_allow",
    "Всегда блокировать": "always_block",
}


class MainWindow(QMainWindow):
    def __init__(self, settings=None):
        super().__init__()

        self.settings = settings or ClientSettings()
        api_url = self.settings.api_url()
        api_token = self.settings.api_token()

        self.setWindowTitle("RPi Router Control")
        self.resize(1150, 700)

        self.api = ApiClient(
            api_url,
            timeout=REQUEST_TIMEOUT,
            api_token=api_token,
        )

        self.users = []
        self.devices = []
        self.clients = []

        self.api_url_edit = QLineEdit(api_url)
        self.api_token_edit = QLineEdit(api_token)
        self.api_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_token_edit.setPlaceholderText("Нужен для изменений")
        self.api_url_edit.editingFinished.connect(
            self.save_connection_settings
        )
        self.api_token_edit.editingFinished.connect(
            self.save_connection_settings
        )

        self.refresh_button = QPushButton("Обновить всё")
        self.refresh_button.clicked.connect(self.refresh_all)

        connection_layout = QHBoxLayout()
        connection_layout.addWidget(QLabel("API:"))
        connection_layout.addWidget(self.api_url_edit, 1)
        connection_layout.addWidget(QLabel("Токен:"))
        connection_layout.addWidget(self.api_token_edit, 1)
        connection_layout.addWidget(self.refresh_button)

        self.tabs = QTabWidget()

        self.users_tab = self.create_users_tab()

        self.devices_tab = self.create_devices_tab()
        self.clients_tab = self.create_clients_tab()

        self.tabs.addTab(self.users_tab, "Пользователи")
        self.tabs.addTab(self.devices_tab, "Устройства")
        self.tabs.addTab(self.clients_tab, "Обнаруженные")

        root_layout = QVBoxLayout()
        root_layout.addLayout(connection_layout)
        root_layout.addWidget(self.tabs)

        central = QWidget()
        central.setLayout(root_layout)
        self.setCentralWidget(central)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(
            "Введите адрес API и нажмите «Обновить всё»"
        )

    def create_users_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        button_layout = QHBoxLayout()

        self.add_user_button = QPushButton("Добавить")
        self.rename_user_button = QPushButton("Переименовать")
        self.delete_user_button = QPushButton("Удалить")

        self.add_user_button.clicked.connect(self.add_user)
        self.rename_user_button.clicked.connect(self.rename_user)
        self.delete_user_button.clicked.connect(self.delete_user)

        button_layout.addWidget(self.add_user_button)
        button_layout.addWidget(self.rename_user_button)
        button_layout.addWidget(self.delete_user_button)
        button_layout.addStretch()

        self.users_table = self.create_table(
            ["ID", "Пользователь", "Режим доступа"]
        )
        self.users_table.itemSelectionChanged.connect(
            self.on_user_selection_changed
        )

        access_panel = QWidget()
        access_layout = QGridLayout()

        self.selected_user_label = QLabel("Пользователь не выбран")

        self.access_mode_combo = QComboBox()
        self.access_mode_combo.addItems(ACCESS_MODE_VALUES.keys())

        self.apply_access_button = QPushButton("Применить режим")
        self.apply_access_button.clicked.connect(
            self.apply_access_mode
        )

        self.access_state_label = QLabel("Текущее состояние: —")
        self.access_reason_label = QLabel("Причина: —")
        self.access_time_label = QLabel("Время RPi: —")

        access_layout.addWidget(
            QLabel("Выбран:"),
            0,
            0,
        )
        access_layout.addWidget(
            self.selected_user_label,
            0,
            1,
            1,
            2,
        )
        access_layout.addWidget(
            QLabel("Режим:"),
            1,
            0,
        )
        access_layout.addWidget(
            self.access_mode_combo,
            1,
            1,
        )
        access_layout.addWidget(
            self.apply_access_button,
            1,
            2,
        )
        access_layout.addWidget(
            self.access_state_label,
            2,
            0,
            1,
            3,
        )
        access_layout.addWidget(
            self.access_reason_label,
            3,
            0,
            1,
            3,
        )
        access_layout.addWidget(
            self.access_time_label,
            4,
            0,
            1,
            3,
        )

        access_panel.setLayout(access_layout)

        layout.addLayout(button_layout)
        layout.addWidget(self.users_table, 1)
        layout.addWidget(access_panel)

        widget.setLayout(layout)

        self.set_user_controls_enabled(False)

        return widget

    def create_devices_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        assignment_layout = QHBoxLayout()
        self.device_owner_label = QLabel("Устройство не выбрано")
        self.device_owner_combo = QComboBox()
        self.assign_device_button = QPushButton("Назначить пользователя")
        self.assign_device_button.clicked.connect(self.assign_device_owner)

        assignment_layout.addWidget(self.device_owner_label)
        assignment_layout.addStretch()
        assignment_layout.addWidget(QLabel("Владелец:"))
        assignment_layout.addWidget(self.device_owner_combo)
        assignment_layout.addWidget(self.assign_device_button)

        self.devices_table = self.create_table(
            ["ID", "Пользователь", "Имя устройства", "MAC"]
        )
        self.devices_table.itemSelectionChanged.connect(
            self.on_device_selection_changed
        )

        layout.addLayout(assignment_layout)
        layout.addWidget(self.devices_table, 1)
        widget.setLayout(layout)

        self.set_device_controls_enabled(False)
        return widget

    def create_clients_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        assignment_layout = QHBoxLayout()
        self.client_owner_label = QLabel("Устройство не выбрано")
        self.client_owner_combo = QComboBox()
        self.assign_client_button = QPushButton("Назначить пользователя")
        self.assign_client_button.clicked.connect(self.assign_client_owner)

        assignment_layout.addWidget(self.client_owner_label)
        assignment_layout.addStretch()
        assignment_layout.addWidget(QLabel("Владелец:"))
        assignment_layout.addWidget(self.client_owner_combo)
        assignment_layout.addWidget(self.assign_client_button)

        self.clients_table = self.create_table(
            [
                "Online",
                "DHCP-имя",
                "IP",
                "MAC",
                "Имя в системе",
                "Пользователь",
            ]
        )
        self.clients_table.itemSelectionChanged.connect(
            self.on_client_selection_changed
        )

        layout.addLayout(assignment_layout)
        layout.addWidget(self.clients_table, 1)
        widget.setLayout(layout)

        self.set_client_controls_enabled(False)
        return widget

    @staticmethod
    def create_table(headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        return table

    @staticmethod
    def wrap_table(table):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget

    @staticmethod
    def set_item(table, row, column, value, alignment=None):
        if value is None:
            value = ""

        item = QTableWidgetItem(str(value))

        if alignment is not None:
            item.setTextAlignment(alignment)

        table.setItem(row, column, item)

    def prepare_api(self):
        base_url = self.api_url_edit.text().strip()

        if not base_url:
            raise ApiError("Введите адрес API Raspberry Pi.")

        self.api.set_base_url(base_url)
        self.api.set_api_token(self.api_token_edit.text())
        self.save_connection_settings()

    def save_connection_settings(self):
        self.settings.save_connection(
            self.api_url_edit.text(),
            self.api_token_edit.text(),
        )

    def closeEvent(self, event):
        self.save_connection_settings()
        super().closeEvent(event)

    def refresh_all(self):
        self.refresh_button.setEnabled(False)
        self.statusBar().showMessage("Получение данных...")

        try:
            self.prepare_api()

            self.users = self.api.get_users()
            self.devices = self.api.get_devices()
            self.clients = self.api.get_clients()

            self.fill_users()
            self.fill_devices()
            self.fill_clients()

        except ApiError as exc:
            self.show_api_error(exc)
            self.statusBar().showMessage("Ошибка соединения")
        else:
            self.statusBar().showMessage(
                f"Получено: "
                f"{len(self.users)} пользователей, "
                f"{len(self.devices)} устройств, "
                f"{len(self.clients)} клиентов"
            )
        finally:
            self.refresh_button.setEnabled(True)

    def refresh_users(self, select_user_id=None):
        try:
            self.prepare_api()
            self.users = self.api.get_users()
            self.fill_users(select_user_id)
        except ApiError as exc:
            self.show_api_error(exc)
            return False

        return True

    def fill_users(self, select_user_id=None):
        self.users_table.blockSignals(True)
        self.users_table.setRowCount(len(self.users))

        selected_row = None

        for row, user in enumerate(self.users):
            user_id = user.get("id")

            self.set_item(
                self.users_table,
                row,
                0,
                user_id,
            )
            self.set_item(
                self.users_table,
                row,
                1,
                user.get("name"),
            )

            mode = user.get("access_mode")
            self.set_item(
                self.users_table,
                row,
                2,
                ACCESS_MODE_TEXT.get(mode, mode),
            )

            if user_id == select_user_id:
                selected_row = row

        self.users_table.blockSignals(False)
        self.fill_device_owner_combo()

        if selected_row is not None:
            self.users_table.selectRow(selected_row)
        else:
            self.users_table.clearSelection()
            self.clear_selected_user()

    def fill_device_owner_combo(self):
        for combo in (self.device_owner_combo, self.client_owner_combo):
            current_user_id = combo.currentData()
            combo.clear()

            for user in self.users:
                combo.addItem(
                    user.get("name", ""),
                    user.get("id"),
                )

            current_index = combo.findData(current_user_id)
            if current_index >= 0:
                combo.setCurrentIndex(current_index)

    def fill_devices(self):
        selected = self.selected_device()
        selected_device_id = selected.get("id") if selected else None
        self.devices_table.setRowCount(len(self.devices))
        selected_row = None

        for row, device in enumerate(self.devices):
            self.set_item(
                self.devices_table,
                row,
                0,
                device.get("id"),
            )
            self.set_item(
                self.devices_table,
                row,
                1,
                device.get("user"),
            )
            self.set_item(
                self.devices_table,
                row,
                2,
                device.get("name"),
            )
            self.set_item(
                self.devices_table,
                row,
                3,
                device.get("mac"),
            )

            if device.get("id") == selected_device_id:
                selected_row = row

        if selected_row is not None:
            self.devices_table.selectRow(selected_row)
        else:
            self.devices_table.clearSelection()
            self.clear_selected_device()

    def fill_clients(self):
        selected = self.selected_client()
        selected_mac = selected.get("mac") if selected else None
        self.clients_table.setRowCount(len(self.clients))
        selected_row = None

        for row, client in enumerate(self.clients):
            online = client.get("online", False)

            self.set_item(
                self.clients_table,
                row,
                0,
                "●" if online else "○",
                Qt.AlignmentFlag.AlignCenter,
            )
            self.set_item(
                self.clients_table,
                row,
                1,
                client.get("name"),
            )
            self.set_item(
                self.clients_table,
                row,
                2,
                client.get("ip"),
            )
            self.set_item(
                self.clients_table,
                row,
                3,
                client.get("mac"),
            )
            self.set_item(
                self.clients_table,
                row,
                4,
                client.get("device_name"),
            )
            self.set_item(
                self.clients_table,
                row,
                5,
                client.get("owner"),
            )

            if str(client.get("mac", "")).lower() == str(
                selected_mac or ""
            ).lower():
                selected_row = row

        if selected_row is not None:
            self.clients_table.selectRow(selected_row)
        else:
            self.clients_table.clearSelection()
            self.clear_selected_client()

    def selected_user(self):
        row = self.users_table.currentRow()

        if row < 0:
            return None

        id_item = self.users_table.item(row, 0)

        if id_item is None:
            return None

        try:
            user_id = int(id_item.text())
        except ValueError:
            return None

        return next(
            (
                user
                for user in self.users
                if user.get("id") == user_id
            ),
            None,
        )

    def selected_device(self):
        row = self.devices_table.currentRow()

        if row < 0:
            return None

        id_item = self.devices_table.item(row, 0)
        if id_item is None:
            return None

        try:
            device_id = int(id_item.text())
        except ValueError:
            return None

        return next(
            (
                device
                for device in self.devices
                if device.get("id") == device_id
            ),
            None,
        )

    def on_device_selection_changed(self):
        device = self.selected_device()

        if device is None:
            self.clear_selected_device()
            return

        self.set_device_controls_enabled(True)
        self.device_owner_label.setText(
            f"{device.get('name')} ({device.get('mac')})"
        )

        user_index = self.device_owner_combo.findData(device.get("user_id"))
        if user_index >= 0:
            self.device_owner_combo.setCurrentIndex(user_index)

    def clear_selected_device(self):
        self.device_owner_label.setText("Устройство не выбрано")
        self.set_device_controls_enabled(False)

    def set_device_controls_enabled(self, enabled):
        has_users = bool(self.users)
        self.device_owner_combo.setEnabled(enabled and has_users)
        self.assign_device_button.setEnabled(enabled and has_users)

    def assign_device_owner(self):
        device = self.selected_device()
        user_id = self.device_owner_combo.currentData()

        if device is None or user_id is None:
            return

        try:
            self.prepare_api()
            updated = self.api.update_device(
                device["id"],
                user_id=user_id,
            )
            self.devices = self.api.get_devices()
        except ApiError as exc:
            self.show_api_error(exc)
            return

        self.fill_devices()
        self.statusBar().showMessage(
            f"Устройство «{updated.get('name')}» назначено "
            f"пользователю «{updated.get('user')}»"
        )

    def selected_client(self):
        row = self.clients_table.currentRow()

        if row < 0:
            return None

        mac_item = self.clients_table.item(row, 3)
        if mac_item is None:
            return None

        mac = mac_item.text().lower()
        return next(
            (
                client
                for client in self.clients
                if str(client.get("mac", "")).lower() == mac
            ),
            None,
        )

    def on_client_selection_changed(self):
        client = self.selected_client()

        if client is None:
            self.clear_selected_client()
            return

        self.client_owner_label.setText(
            f"{client.get('name')} ({client.get('mac')})"
        )
        self.set_client_controls_enabled(True)

        device = self.device_by_mac(client.get("mac"))
        if device is not None:
            user_index = self.client_owner_combo.findData(
                device.get("user_id")
            )
            if user_index >= 0:
                self.client_owner_combo.setCurrentIndex(user_index)

    def clear_selected_client(self):
        self.client_owner_label.setText("Устройство не выбрано")
        self.set_client_controls_enabled(False)

    def set_client_controls_enabled(self, enabled):
        has_users = bool(self.users)
        self.client_owner_combo.setEnabled(enabled and has_users)
        self.assign_client_button.setEnabled(enabled and has_users)

    def device_by_mac(self, mac):
        normalized_mac = str(mac or "").lower()
        return next(
            (
                device
                for device in self.devices
                if str(device.get("mac", "")).lower() == normalized_mac
            ),
            None,
        )

    def assign_client_owner(self):
        client = self.selected_client()
        user_id = self.client_owner_combo.currentData()

        if client is None or user_id is None:
            return

        try:
            self.prepare_api()
            device = self.device_by_mac(client.get("mac"))

            if device is None:
                updated = self.api.create_device(
                    user_id,
                    client.get("mac"),
                    client.get("device_name")
                    or client.get("name")
                    or client.get("mac"),
                )
            else:
                updated = self.api.update_device(
                    device["id"],
                    user_id=user_id,
                )

            self.devices = self.api.get_devices()
            self.clients = self.api.get_clients()
        except ApiError as exc:
            self.show_api_error(exc)
            return

        self.fill_devices()
        self.fill_clients()
        owner = next(
            (
                user.get("name")
                for user in self.users
                if user.get("id") == user_id
            ),
            "",
        )
        self.statusBar().showMessage(
            f"Устройство «{updated.get('name')}» назначено "
            f"пользователю «{owner}»"
        )

    def on_user_selection_changed(self):
        user = self.selected_user()

        if user is None:
            self.clear_selected_user()
            return

        self.set_user_controls_enabled(True)

        self.selected_user_label.setText(
            f"{user.get('name')} (ID {user.get('id')})"
        )

        mode = user.get("access_mode")
        mode_text = ACCESS_MODE_TEXT.get(mode)

        if mode_text is not None:
            index = self.access_mode_combo.findText(mode_text)
            if index >= 0:
                self.access_mode_combo.setCurrentIndex(index)

        self.load_user_access(user["id"])

    def clear_selected_user(self):
        self.set_user_controls_enabled(False)
        self.selected_user_label.setText("Пользователь не выбран")
        self.access_state_label.setText("Текущее состояние: —")
        self.access_reason_label.setText("Причина: —")
        self.access_time_label.setText("Время RPi: —")

    def set_user_controls_enabled(self, enabled):
        self.rename_user_button.setEnabled(enabled)
        self.delete_user_button.setEnabled(enabled)
        self.access_mode_combo.setEnabled(enabled)
        self.apply_access_button.setEnabled(enabled)

    def load_user_access(self, user_id):
        try:
            self.prepare_api()
            state = self.api.get_user_access(user_id)
        except ApiError as exc:
            self.access_state_label.setText(
                "Текущее состояние: ошибка получения"
            )
            self.access_reason_label.setText(
                f"Причина: {exc}"
            )
            self.access_time_label.setText("Время RPi: —")
            return

        allowed = state.get("allowed")

        if allowed is True:
            access_text = "РАЗРЕШЁН"
        elif allowed is False:
            access_text = "ЗАБЛОКИРОВАН"
        else:
            access_text = "НЕИЗВЕСТНО"

        self.access_state_label.setText(
            f"Текущее состояние: {access_text}"
        )
        self.access_reason_label.setText(
            f"Причина: {state.get('reason', '—')}"
        )
        self.access_time_label.setText(
            f"Время RPi: {state.get('time', '—')}, "
            f"день недели: {state.get('weekday', '—')}"
        )

    def add_user(self):
        name, ok = QInputDialog.getText(
            self,
            "Новый пользователь",
            "Имя пользователя:",
        )

        if not ok:
            return

        name = name.strip()

        if not name:
            QMessageBox.warning(
                self,
                "Пользователь",
                "Имя пользователя не должно быть пустым.",
            )
            return

        try:
            self.prepare_api()
            created = self.api.create_user(name)
        except ApiError as exc:
            self.show_api_error(exc)
            return

        self.refresh_users(created.get("id"))
        self.statusBar().showMessage(
            f"Пользователь «{name}» создан"
        )

    def rename_user(self):
        user = self.selected_user()

        if user is None:
            return

        name, ok = QInputDialog.getText(
            self,
            "Переименование пользователя",
            "Новое имя:",
            text=user.get("name", ""),
        )

        if not ok:
            return

        name = name.strip()

        if not name:
            QMessageBox.warning(
                self,
                "Пользователь",
                "Имя пользователя не должно быть пустым.",
            )
            return

        try:
            self.prepare_api()
            self.api.rename_user(user["id"], name)
        except ApiError as exc:
            self.show_api_error(exc)
            return

        self.refresh_users(user["id"])
        self.statusBar().showMessage(
            f"Пользователь переименован в «{name}»"
        )

    def delete_user(self):
        user = self.selected_user()

        if user is None:
            return

        answer = QMessageBox.question(
            self,
            "Удаление пользователя",
            f"Удалить пользователя «{user.get('name')}»?\n\n"
            "API не позволит удалить пользователя, "
            "если к нему привязаны устройства или расписания.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.prepare_api()
            self.api.delete_user(user["id"])
        except ApiError as exc:
            self.show_api_error(exc)
            return

        self.refresh_users()
        self.statusBar().showMessage(
            f"Пользователь «{user.get('name')}» удалён"
        )

    def apply_access_mode(self):
        user = self.selected_user()

        if user is None:
            return

        mode_text = self.access_mode_combo.currentText()
        access_mode = ACCESS_MODE_VALUES[mode_text]

        try:
            self.prepare_api()
            self.api.set_access_mode(
                user["id"],
                access_mode,
            )
        except ApiError as exc:
            self.show_api_error(exc)
            return

        self.refresh_users(user["id"])
        self.load_user_access(user["id"])

        self.statusBar().showMessage(
            f"Для «{user.get('name')}» установлен режим "
            f"«{mode_text}»"
        )

    def show_api_error(self, error):
        QMessageBox.critical(
            self,
            "Ошибка API",
            str(error),
        )
