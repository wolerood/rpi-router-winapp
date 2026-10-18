import unittest

from schedule_grid import schedules_to_slots, slots_to_intervals


class ScheduleGridConversionTests(unittest.TestCase):
    def test_schedule_marks_intersecting_half_hour_cells(self):
        slots = schedules_to_slots(
            [{"user_id": 2, "weekday": 1, "start": "06:00", "end": "07:59"}],
            2,
        )
        self.assertTrue(slots[12][0])
        self.assertTrue(slots[15][0])
        self.assertFalse(slots[16][0])

    def test_other_users_are_ignored(self):
        slots = schedules_to_slots(
            [{"user_id": 3, "weekday": 1, "start": "06:00", "end": "07:59"}],
            2,
        )
        self.assertFalse(any(any(row) for row in slots))

    def test_contiguous_slots_become_one_minute_accurate_interval(self):
        slots = [[False for _ in range(7)] for _ in range(48)]
        for row in range(12, 16):
            slots[row][0] = True
        self.assertEqual(
            slots_to_intervals(slots),
            [{"weekday": 1, "start": "06:00", "end": "07:59"}],
        )

    def test_overnight_interval_marks_both_days(self):
        slots = schedules_to_slots(
            [{"user_id": 2, "weekday": 7, "start": "23:30", "end": "00:29"}],
            2,
        )
        self.assertTrue(slots[47][6])
        self.assertTrue(slots[0][0])


if __name__ == "__main__":
    unittest.main()
