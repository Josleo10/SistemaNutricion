import unittest
from datetime import date
from nutricion_system.decision_engine import analizar_semana


class TestDecisionEngine(unittest.TestCase):
    def test_dummy(self):
        res = analizar_semana(date(2026, 3, 1), date(2026, 3, 7))
        self.assertIsNotNone(res)


if __name__ == '__main__':
    unittest.main()
