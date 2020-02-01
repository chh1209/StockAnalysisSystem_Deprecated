#!usr/bin/env python
#-*- coding:utf-8 _*-
"""
@version:
author:Sleepy
@time: 2017/08/08
@file: DataTable.py
@function:
@modify:
"""
import copy
import traceback
import threading

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QHeaderView, QLineEdit, QFileDialog

from Utiltity.common import *
from Utiltity.ui_utility import *
from Utiltity.time_utility import *
from Strategy.StrategyEntry import *
from Analyzer.AnalyzerUtility import *
from stock_analysis_system import StockAnalysisSystem


# --------------------------------------------------- PageTableWidget --------------------------------------------------

class PageTableWidget(QWidget):
    def __init__(self):
        super(PageTableWidget, self).__init__()

        self.__page = 0
        self.__max_page = 0
        self.__item_per_page = 50
        self.__max_item_count = 0

        self.__table_main = EasyQTableWidget()
        self.__layout_bottom = QHBoxLayout()

        self.init_ui()

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(self.__table_main)
        main_layout.addLayout(self.__layout_bottom)

    def __config_control(self):
        self.add_extra_button('<<', '<<')
        self.add_extra_button('<', '<')
        self.add_extra_button('>', '>')
        self.add_extra_button('>>', '>>')

    # ------------------------------------- Function -------------------------------------

    def get_table(self) -> EasyQTableWidget:
        return self.__table_main

    def get_item_offset(self) -> int:
        return self.__page * self.__item_per_page

    def get_item_per_page(self) -> int:
        return self.__item_per_page

    def set_max_item(self, count: int):
        self.__max_item_count = count
        self.__update_max_page()

    def set_item_pre_page(self, count: int):
        if self.__item_per_page != count:
            self.__item_per_page = count
            self.__update_max_page()
            self.on_content_update()

    def add_extra_button(self, caption: str, button_mark: str):
        button = QPushButton(caption)
        self.__layout_bottom.addWidget(button)
        button.clicked.connect(partial(self.on_button_event, button_mark))

    # ---------------------------------- Event Handling ----------------------------------

    def on_button_event(self, control: str):
        if control in ['<<', '<', '>', '>>']:
            self.on_page_control(control)
        else:
            self.on_extra_control(control)

    def on_page_control(self, control: str):
        if control == '<<':
            self.__page = 0
        elif control == '<':
            self.__page = max(self.__page - 1, 0)
        elif control == '>':
            self.__page = min(self.__page + 1, self.__max_page)
        elif control == '>>':
            self.__page = self.__max_page
        self.on_content_update()

    # ------------------------------------- Override -------------------------------------

    def on_extra_control(self, control: str):
        # TODO: Override this function to handle extra button event
        pass

    def on_content_update(self):
        # TODO: Override this function to handle content update
        pass

    def __update_max_page(self):
        self.__max_page = (self.__max_item_count / self.__item_per_page) if self.__item_per_page > 0 else 0
        if self.__page > self.__max_page:
            self.__page = self.__max_page


# ---------------------------------------------------- StrategyUi ----------------------------------------------------

class StrategyUi(QWidget):
    TABLE_HEADER_SELECTOR = ['', 'Selector', 'Comments', 'UUID', 'Status']
    TABLE_HEADER_ANALYZER = ['', 'Strategy', 'Comments', 'UUID', 'Status']

    def __init__(self):
        super(StrategyUi, self).__init__()
        self.__data_hub = StockAnalysisSystem().get_data_hub_entry()
        self.__strategy_entry = StockAnalysisSystem().get_strategy_entry()

        self.__analyzer_info = self.load_analyzer_info()

        # Thread and task related
        self.__lock = threading.Lock()
        self.__task_thread = None
        self.__selector_list = []
        self.__analyzer_list = []
        self.__progress_rate = ProgressRate()

        # Timer for update status
        self.__timer = QTimer()
        self.__timer.setInterval(1000)
        self.__timer.timeout.connect(self.on_timer)
        self.__timer.start()

        # UI related
        group, layout = create_v_group_box('Selector')
        self.__group_selector = group
        self.__layout_selector = layout

        group, layout = create_v_group_box('Analyzer')
        self.__group_analyzer = group
        self.__layout_analyzer = layout

        group, layout = create_h_group_box('Result')
        self.__group_result = group
        self.__layout_result = layout

        self.__table_selector = EasyQTableWidget()
        self.__table_analyzer = EasyQTableWidget()

        self.__edit_path = QLineEdit('analysis_report.xlsx')
        self.__button_browse = QPushButton('Browse')

        self.__button_selector = QPushButton('Selector')
        self.__button_analyzer = QPushButton('Analyzer')
        self.__button_result = QPushButton('Result')
        self.__button_run_strategy = QPushButton('Run Strategy')

        self.init_ui()
        self.update_selector()
        self.update_analyzer()

    # ---------------------------------------------------- UI Init -----------------------------------------------------

    def init_ui(self):
        self.__layout_control()
        self.__config_control()

    def __layout_control(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setMinimumSize(600, 400)

        self.__layout_selector.addWidget(self.__table_selector)
        main_layout.addWidget(self.__group_selector)

        self.__layout_analyzer.addWidget(self.__table_analyzer)
        main_layout.addWidget(self.__group_analyzer)

        self.__layout_result.addWidget(self.__edit_path)
        self.__layout_result.addWidget(self.__button_browse)
        main_layout.addWidget(self.__group_result)

        bottom_control_area = QHBoxLayout()
        main_layout.addLayout(bottom_control_area)

        bottom_control_area.addWidget(QLabel('Strategy Flow: '), 99)
        bottom_control_area.addWidget(self.__button_selector)
        bottom_control_area.addWidget(QLabel('==>'))
        bottom_control_area.addWidget(self.__button_analyzer)
        bottom_control_area.addWidget(QLabel('==>'))
        bottom_control_area.addWidget(self.__button_result)
        bottom_control_area.addWidget(QLabel(' | '))
        bottom_control_area.addWidget(self.__button_run_strategy)

    def __config_control(self):
        for _ in StrategyUi.TABLE_HEADER_SELECTOR:
            self.__table_selector.insertColumn(0)
        self.__table_selector.setHorizontalHeaderLabels(StrategyUi.TABLE_HEADER_SELECTOR)
        self.__table_selector.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        for _ in StrategyUi.TABLE_HEADER_ANALYZER:
            self.__table_analyzer.insertColumn(0)
        self.__table_analyzer.setHorizontalHeaderLabels(StrategyUi.TABLE_HEADER_ANALYZER)
        self.__table_analyzer.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.__layout_selector.setSpacing(0)
        self.__layout_analyzer.setSpacing(0)
        self.__layout_result.setSpacing(0)
        self.__layout_selector.setContentsMargins(0, 0, 0, 0)
        self.__layout_analyzer.setContentsMargins(0, 0, 0, 0)
        # self.__layout_result.setContentsMargins(0, 0, 0, 0)

        self.__button_result.clicked.connect(self.on_button_browse)
        self.__button_browse.clicked.connect(self.on_button_browse)
        self.__button_selector.clicked.connect(self.on_button_selector)
        self.__button_analyzer.clicked.connect(self.on_button_analyzer)
        self.__button_run_strategy.clicked.connect(self.on_button_run_strategy)

    def on_button_browse(self):
        file_path, ok = QFileDialog.getSaveFileName(self, 'Select Result Excel Path', '',
                                                    'XLSX Files (*.xlsx);;All Files (*)')
        if ok:
            self.__edit_path.setText(file_path)

    def on_button_selector(self):
        self.__group_selector.setVisible(True)
        self.__group_analyzer.setVisible(not self.__group_analyzer.isVisible())

    def on_button_analyzer(self):
        self.__group_analyzer.setVisible(True)
        self.__group_selector.setVisible(not self.__group_selector.isVisible())

    def on_button_run_strategy(self):
        selector_list = []
        analyzer_list = []

        for i in range(0, self.__table_analyzer.rowCount()):
            if self.__table_analyzer.item(i, 0).checkState() == QtCore.Qt.Checked:
                uuid = self.__table_analyzer.item(i, 3).text()
                analyzer_list.append(uuid)

        self.__lock.acquire()
        self.__selector_list = selector_list
        self.__analyzer_list = analyzer_list
        self.__lock.release()

        self.execute_update_task()

    def on_timer(self):
        for i in range(0, self.__table_analyzer.rowCount()):
            uuid = self.__table_analyzer.item(i, 3).text()
            if self.__progress_rate.has_progress(uuid):
                rate = self.__progress_rate.get_progress_rate(uuid)
                self.__table_analyzer.item(i, 4).setText('%.2f%%' % (rate * 100))
            else:
                self.__table_analyzer.item(i, 4).setText(str(''))

    def closeEvent(self, event):
        if self.__task_thread is not None:
            QMessageBox.information(self,
                                    QtCore.QCoreApplication.translate('', '无法关闭窗口'),
                                    QtCore.QCoreApplication.translate('', '策略运行过程中无法关闭此窗口'),
                                    QMessageBox.Close, QMessageBox.Close)
            event.ignore()
        else:
            event.accept()

    # --------------------------------------------------------------------------------------

    def update_selector(self):
        self.__table_selector.clear()
        self.__table_selector.setRowCount(0)
        self.__table_selector.setHorizontalHeaderLabels(StrategyUi.TABLE_HEADER_SELECTOR)

        self.__table_selector.AppendRow(['', '所有股票', '当前只支持所有股票，不选默认也是所有股票', '-'])

        # Add check box
        check_item = QTableWidgetItem()
        check_item.setCheckState(QtCore.Qt.Unchecked)
        self.__table_selector.setItem(0, 0, check_item)

    def update_analyzer(self):
        self.__table_analyzer.clear()
        self.__table_analyzer.setRowCount(0)
        self.__table_analyzer.setHorizontalHeaderLabels(StrategyUi.TABLE_HEADER_ANALYZER)

        for method_uuid, method_name, method_detail in self.__analyzer_info:
            line = []
            line.append('')             # Place holder for check box
            line.append(method_name)
            line.append(method_detail)
            line.append(method_uuid)
            line.append('')             # Place holder for status

            self.__table_analyzer.AppendRow(line)
            index = self.__table_analyzer.rowCount() - 1

            # Add check box
            check_item = QTableWidgetItem()
            check_item.setCheckState(QtCore.Qt.Unchecked)
            self.__table_analyzer.setItem(index, 0, check_item)

    # --------------------------------------------------------------------------

    def load_analyzer_info(self) -> [(str, str, str)]:
        info = []
        probs = self.__strategy_entry.strategy_prob()
        for prob in probs:
            methods = prob.get('methods', [])
            for method in methods:
                method_uuid = method[0]
                method_name = method[1]
                method_detail = method[2]
                method_entry = method[3]
                if method_entry is not None and '测试' not in method_name:
                    # Notice the item order
                    info.append([method_uuid, method_name, method_detail])
        return info

    # --------------------------------- Thread ---------------------------------

    def execute_update_task(self):
        if self.__task_thread is None:
            self.__task_thread = threading.Thread(target=self.ui_task)
            self.__task_thread.start()
        else:
            print('Task already running...')
            QMessageBox.information(self,
                                    QtCore.QCoreApplication.translate('', '无法执行'),
                                    QtCore.QCoreApplication.translate('', '已经有策略在运行中，无法同时运行多个策略'),
                                    QMessageBox.Close, QMessageBox.Close)

    def ui_task(self):
        print('Strategy task start.')

        self.__lock.acquire()
        selector_list = self.__selector_list
        analyzer_list = self.__analyzer_list
        self.__lock.release()

        data_utility = self.__data_hub.get_data_utility()
        stock_list = data_utility.get_stock_identities()

        self.__progress_rate.reset()

        # ------------- Run analyzer -------------
        clock = Clock()
        result = self.__strategy_entry.run_strategy(stock_list, analyzer_list, progress=self.__progress_rate)
        print('Analysis time spending: ' + str(clock.elapsed_s()) + ' s')

        # ----------- Generate report ------------
        clock.reset()
        name_dict = self.__strategy_entry.strategy_name_dict()
        generate_analysis_report(result, 'analysis_report.xlsx', name_dict)
        print('Generate report time spending: ' + str(clock.elapsed_s()) + ' s')

        # ----------------- End ------------------
        self.__task_thread = None
        print('Update task finished.')


# ----------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    dlg = WrapperQDialog(StrategyUi())
    dlg.exec()


# ----------------------------------------------------------------------------------------------------------------------

def exception_hook(type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(type, value, tback)


sys.excepthook = exception_hook


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass






































