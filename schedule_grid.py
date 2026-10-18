from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


SLOT_MINUTES = 30
SLOT_COUNT = 24 * 60 // SLOT_MINUTES
DAY_HEADERS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
ALLOWED_COLOR = QColor("#75d28b")
BLOCKED_COLOR = QColor("#e8ebf0")


def minutes_from_time(value):
    try:
        hours, minutes = (int(part) for part in value.split(":"))
    except (AttributeError, TypeError, ValueError):
        return None
    if not 0 <= hours <= 23 or not 0 <= minutes <= 59:
        return None
    return hours * 60 + minutes


def time_from_minutes(value):
    value %= 24 * 60
    return f"{value // 60:02d}:{value % 60:02d}"


def schedules_to_slots(schedules, user_id):
    """Convert API intervals to a 48 x 7 boolean grid."""
    slots = [[False for _ in range(7)] for _ in range(SLOT_COUNT)]
    for schedule in schedules:
        if schedule.get("user_id") != user_id:
            continue
        weekday = schedule.get("weekday")
        start = minutes_from_time(schedule.get("start"))
        end = minutes_from_time(schedule.get("end"))
        if not isinstance(weekday, int) or not 1 <= weekday <= 7:
            continue
        if start is None or end is None:
            continue

        # An API interval includes both endpoints. Mark every half-hour cell
        # whose time range intersects it, including overnight intervals.
        ranges = [(start, end)] if start <= end else [(start, 1439), (0, end)]
        days = [weekday - 1] if start <= end else [weekday - 1, weekday % 7]
        for (range_start, range_end), day in zip(ranges, days):
            first = range_start // SLOT_MINUTES
            last = range_end // SLOT_MINUTES
            for row in range(first, last + 1):
                slots[row][day] = True
    return slots


def slots_to_intervals(slots):
    """Collapse a boolean grid into API intervals with minute-accurate ends."""
    intervals = []
    for day in range(7):
        row = 0
        while row < SLOT_COUNT:
            if not slots[row][day]:
                row += 1
                continue
            start = row
            while row + 1 < SLOT_COUNT and slots[row + 1][day]:
                row += 1
            end = row
            intervals.append(
                {
                    "weekday": day + 1,
                    "start": time_from_minutes(start * SLOT_MINUTES),
                    "end": time_from_minutes((end + 1) * SLOT_MINUTES - 1),
                }
            )
            row += 1
    return intervals


class ScheduleGrid(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(7, SLOT_COUNT, parent)
        self._slots = [[False for _ in range(7)] for _ in range(SLOT_COUNT)]
        self.setHorizontalHeader(RotatedTimeHeader(self))
        self.setHorizontalHeaderLabels(
            [time_from_minutes(column * SLOT_MINUTES) for column in range(SLOT_COUNT)]
        )
        self.setVerticalHeaderLabels(DAY_HEADERS)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setDefaultSectionSize(22)
        self.horizontalHeader().setMinimumSectionSize(16)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.verticalHeader().setDefaultSectionSize(64)
        self.verticalHeader().setFixedWidth(72)
        self.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verticalHeader().setStyleSheet(
            "QHeaderView::section {"
            " background: #eef5fc; color: #11182e; border: 1px solid #e2eaf4;"
            " border-radius: 10px; font-size: 16px; font-weight: 700; margin: 3px;"
            "}"
        )
        self.setAlternatingRowColors(False)
        self.setShowGrid(True)
        self.setStyleSheet(
            "QTableWidget { background: white; border: none; gridline-color: white; }"
        )
        for row in range(7):
            for column in range(SLOT_COUNT):
                item = QTableWidgetItem()
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.setItem(row, column, item)
        self.cellClicked.connect(self.toggle_slot)
        self._repaint_all()

    def set_slots(self, slots):
        self._slots = [list(row) for row in slots]
        self._repaint_all()

    def slots(self):
        return [list(row) for row in self._slots]

    def toggle_slot(self, row, column):
        self._slots[column][row] = not self._slots[column][row]
        self._paint_cell(row, column)

    def _repaint_all(self):
        for row in range(7):
            for column in range(SLOT_COUNT):
                self._paint_cell(row, column)

    def _paint_cell(self, row, column):
        color = ALLOWED_COLOR if self._slots[column][row] else BLOCKED_COLOR
        self.item(row, column).setBackground(color)


class RotatedTimeHeader(QHeaderView):
    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setSectionsClickable(False)
        self.setFixedHeight(84)

    def sizeHint(self):
        hint = super().sizeHint()
        return QSize(hint.width(), 84)

    def paintSection(self, painter, rect, logical_index):
        painter.save()
        painter.fillRect(rect, QColor("#ffffff"))
        label = self.model().headerData(
            logical_index,
            self.orientation(),
            Qt.ItemDataRole.DisplayRole,
        )
        painter.setPen(QColor("#17213a"))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(rect.center())
        painter.rotate(-90)
        painter.drawText(
            QRectF(
                -rect.height() / 2,
                -rect.width() / 2,
                rect.height(),
                rect.width(),
            ),
            Qt.AlignmentFlag.AlignCenter,
            str(label),
        )
        painter.restore()
