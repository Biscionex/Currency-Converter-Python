#Currency Converter
#key a228cac264e3e98f3fdafb0064c53106
#http://api.exchangeratesapi.io/v1/latest?access_key=a228cac264e3e98f3fdafb0064c53106
#Backend cache

import os
import sys
import time
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QMessageBox, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

API_KEY = os.getenv("EXCHANGE_RATE_API_KEY", "a228cac264e3e98f3fdafb0064c53106")
ENDPOINT = f"http://api.exchangeratesapi.io/v1/latest?access_key={API_KEY}"

class CurrencyBackend:
    def __init__(self, cache_duration_seconds=3600):
        self.cache_duration = cache_duration_seconds
        self.last_fetch_time = 0
        self.rates = {}

    def fetch_rates(self):
        current_time = time.time()
        if self.rates and (current_time - self.last_fetch_time < self.cache_duration):
            return True, "Rates loaded from cache."

        try:
            response = requests.get(ENDPOINT, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("success"):
                self.rates = data.get("rates", {})
                self.last_fetch_time = current_time
                return True, "Rates updated successfully."
            else:
                error_msg = data.get("error", {}).get("info", "Unknown API error")
                return False, f"API Error: {error_msg}"

        except requests.exceptions.RequestException as e:
            return False, f"Network Error: {e}"

    def convert(self, amount: float, from_curr: str, to_curr: str) -> float:
        if from_curr not in self.rates or to_curr not in self.rates:
            raise ValueError("Selected currency rate not available.")

        from_rate = self.rates[from_curr]
        to_rate = self.rates[to_curr]
        
        # Calculate cross-rate via base
        converted = (amount / from_rate) * to_rate
        return round(converted, 2)


class CurrencyConverterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.backend = CurrencyBackend(cache_duration_seconds=1800)
        self.initUI()
        self.load_rates()

    def initUI(self):
        # Window setup
        self.setWindowTitle("Live Currency Converter")
        self.setFixedSize(420, 380)
        
        # Main Layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # Title Header
        title = QLabel("Currency Converter")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Amount Input
        amount_label = QLabel("Amount:")
        amount_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(amount_label)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter amount (e.g., 100)")
        self.amount_input.setFont(QFont("Segoe UI", 11))
        self.amount_input.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px;")
        layout.addWidget(self.amount_input)

        # Currency Selection Layout (From / Swap / To)
        curr_layout = QHBoxLayout()

        # From Currency Dropdown
        self.from_combo = QComboBox()
        self.from_combo.setStyleSheet("padding: 6px; font-size: 14px;")
        curr_layout.addWidget(self.from_combo)

        # Swap Button
        self.swap_btn = QPushButton("⇄")
        self.swap_btn.setFixedWidth(40)
        self.swap_btn.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        self.swap_btn.clicked.connect(self.swap_currencies)
        curr_layout.addWidget(self.swap_btn)

        # To Currency Dropdown
        self.to_combo = QComboBox()
        self.to_combo.setStyleSheet("padding: 6px; font-size: 14px;")
        curr_layout.addWidget(self.to_combo)

        layout.addLayout(curr_layout)

        # Convert Button
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.convert_btn.setStyleSheet(
            "background-color: #0078D4; color: white; padding: 10px; border-radius: 4px;"
        )
        self.convert_btn.clicked.connect(self.perform_conversion)
        layout.addWidget(self.convert_btn)

        # Result Display Label
        self.result_label = QLabel("0.00")
        self.result_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("color: #0078D4; margin-top: 10px;")
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def load_rates(self):
        """Fetch rates and populate dropdown menus."""
        success, message = self.backend.fetch_rates()
        if success:
            currencies = sorted(self.backend.rates.keys())
            self.from_combo.addItems(currencies)
            self.to_combo.addItems(currencies)

            # Set default selections if available
            if "USD" in currencies:
                self.from_combo.setCurrentText("USD")
            if "EUR" in currencies:
                self.to_combo.setCurrentText("EUR")
        else:
            QMessageBox.critical(self, "Error Loading Rates", message)

    def swap_currencies(self):
        """Swap selected values between 'From' and 'To' dropdowns."""
        from_text = self.from_combo.currentText()
        to_text = self.to_combo.currentText()
        self.from_combo.setCurrentText(to_text)
        self.to_combo.setCurrentText(from_text)

    def perform_conversion(self):
        """Validate input and display converted result."""
        raw_amount = self.amount_input.text().strip()
        
        if not raw_amount:
            QMessageBox.warning(self, "Input Error", "Please enter an amount to convert.")
            return

        try:
            amount = float(raw_amount)
            if amount < 0:
                QMessageBox.warning(self, "Input Error", "Amount must be positive.")
                return

            from_curr = self.from_combo.currentText()
            to_curr = self.to_combo.currentText()

            # Perform conversion
            result = self.backend.convert(amount, from_curr, to_curr)
            self.result_label.setText(f"{result:,.2f} {to_curr}")

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid numeric value.")
        except Exception as e:
            QMessageBox.critical(self, "Conversion Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = CurrencyConverterGUI()
    gui.show()
    sys.exit(app.exec_())