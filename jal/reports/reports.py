import logging
import importlib

from enum import Enum, auto
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import Qt, QObject
from data_export.helpers import XLSX
from jal.reports.income_spending_report import IncomeSpendingReport
from jal.reports.p_and_l_report import ProfitLossReportModel
from jal.reports.deals_report import DealsReportModel
from jal.reports.category_report import CategoryReportModel


#-----------------------------------------------------------------------------------------------------------------------
class ReportType(Enum):
    IncomeSpending = auto()
    ProfitLoss = auto()
    Deals = auto()
    ByCategory = auto()


class JalReports(QObject):
    def __init__(self, parent, MdiArea):
        super().__init__()
        self.parent = parent
        self.mdi = MdiArea
        self.items = [
            # 'name' - Title string to display in main menu
            # 'module' - module name inside 'jal/reports' that contains descendant of ReportWidget class
            # 'window_class' - class name that is derived from ReportWidget class
            {
                'name': self.tr("Holdings"),
                'module': 'holdings',
                'window_class': 'HoldingsReport'
            },
            {
                'name': self.tr("Other"),
                'module': 'reports_widget',
                'window_class': 'ReportsWidget'
            }
        ]

    # method is called directly from menu, so it contains QAction that was triggered
    def show(self, action):
        report_loader = self.items[action.data()]
        try:
            module = importlib.import_module(f"jal.reports.{report_loader['module']}")
        except ModuleNotFoundError:
            logging.error(self.tr("Report module not found: ") + report_loader['module'])
            return
        class_instance = getattr(module, report_loader['window_class'])
        report = class_instance(self.mdi)
        self.mdi.addSubWindow(report, maximized=True)

#-----------------------------------------------------------------------------------------------------------------------
class Reports(QObject):
    def __init__(self, report_table_view, report_tree_view):
        super().__init__()

        self.table_view = report_table_view
        self.tree_view = report_tree_view
        self.model = None

    def runReport(self, report_type, begin=0, end=0, account_id=0, group_dates=0):
        if report_type == ReportType.IncomeSpending:
            self.model = IncomeSpendingReport(self.tree_view)
            self.tree_view.setModel(self.model)
            self.tree_view.setVisible(True)
            self.table_view.setVisible(False)
        elif report_type == ReportType.ProfitLoss:
            self.model = ProfitLossReportModel(self.table_view)
            self.table_view.setModel(self.model)
            self.tree_view.setVisible(False)
            self.table_view.setVisible(True)
        elif report_type == ReportType.Deals:
            self.model = DealsReportModel(self.table_view)
            self.table_view.setModel(self.model)
            self.tree_view.setVisible(False)
            self.table_view.setVisible(True)
        elif report_type == ReportType.ByCategory:
            self.model = CategoryReportModel(self.table_view)
            self.table_view.setModel(self.model)
            self.tree_view.setVisible(False)
            self.table_view.setVisible(True)
        else:
            assert False

        try:
            self.model.prepare(begin, end, account_id, group_dates)
        except ValueError as e:
            QMessageBox().warning(None, self.tr("Report creation error"), str(e), QMessageBox.Ok)
            return
        self.model.configureView()

    def saveReport(self):
        filename, filter = QFileDialog.getSaveFileName(None, self.tr("Save report to:"),
                                                       ".", self.tr("Excel files (*.xlsx)"))
        if filename:
            if filter == self.tr("Excel files (*.xlsx)") and filename[-5:] != '.xlsx':
                filename = filename + '.xlsx'
        else:
            return

        report = XLSX(filename)
        sheet = report.add_report_sheet(self.tr("Report"))

        model = self.table_view.model()
        headers = {}
        for col in range(model.columnCount()):
            headers[col] = (model.headerData(col, Qt.Horizontal), report.formats.ColumnHeader())
        report.write_row(sheet, 0, headers)

        for row in range(model.rowCount()):
            data_row = {}
            for col in range(model.columnCount()):
                data_row[col] = (model.data(model.index(row, col)), report.formats.Text(row))
            report.write_row(sheet, row+1, data_row)

        report.save()
