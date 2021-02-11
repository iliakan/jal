from jal.widgets.view_delegate import *
from jal.constants import ColumnWidth, TransactionType
from PySide2 import QtWidgets
from PySide2.QtCore import QObject, SIGNAL, Slot
from functools import partial
from jal.widgets.mapper_delegate import MapperDelegate
from jal.ui_custom.helpers import g_tr, UseSqlTable, ConfigureTableView, ConfigureDataMappers
import jal.ui_custom.reference_data as ui               # Full import due to "cyclic" reference


class TableViewConfig:
    ACTIONS = 3
    ACTION_DETAILS = 4
    TRADES = 5
    DIVIDENDS = 6
    TRANSFERS = 7
    CORP_ACTIONS = 8
    ACCOUNT_TYPES = 9
    ACCOUNTS = 10
    ASSETS = 11
    PEERS = 12
    CATEGORIES = 13
    TAGS = 14
    COUNTRIES = 15
    QUOTES =16

    ACTION_SRC = 0
    ACTION_SIGNAL = 1
    ACTION_SLOT = 2

    DLG_TABLE = 0
    DLG_TITLE = 1
    DLG_COLUMNS = 2
    DLG_SEARCH = 3
    DLG_TOGGLE = 4
    DLG_TREE = 5
    DLG_RELATIONS = 6

    table_names = {
        ACTIONS: 'actions',
        ACTION_DETAILS: 'action_details',
        TRADES: 'trades',
        DIVIDENDS: 'dividends',
        TRANSFERS: 'transfers',
        CORP_ACTIONS: 'corp_actions'
    }

    table_relations = {
        ACTIONS: None,
        ACTION_DETAILS: [("category_id", "categories", "id", "name", None),
                         ("tag_id", "tags", "id", "tag", None)],
        TRADES: None,
        DIVIDENDS: None,
        TRANSFERS: None,
        CORP_ACTIONS: None
    }

    table_view_columns = {
        ACTIONS: [],
        ACTION_DETAILS: [("id", None, None, None, None),
                         ("pid", None, None, None, None),
                         ("category_id", g_tr('TableViewConfig', "Category"), 200, None, MapperDelegate),
                         ("tag_id", g_tr('TableViewConfig', "Tag"), 200, None, MapperDelegate),
                         ("sum", g_tr('TableViewConfig', "Amount"), 100, None, MapperDelegate),
                         ("alt_sum", g_tr('TableViewConfig', "Amount *"), 100, None, MapperDelegate),
                         ("note", g_tr('TableViewConfig', "Note"), ColumnWidth.STRETCH, None, None)],
        TRADES: [],
        DIVIDENDS: [],
        TRANSFERS: [],
        CORP_ACTIONS: []
    }

    def __init__(self, parent):
        self.parent = parent
        self.delegates_storage = []   #  Keep references to all created delegates here
        self.views = {
            self.ACTIONS: None,
            self.ACTION_DETAILS: parent.ActionDetailsTableView,
            self.TRADES: None,
            self.DIVIDENDS: None,
            self.TRANSFERS: None,
            self.CORP_ACTIONS: None
        }
        self.models = {}
        self.mappers = {}           # Here mapper objects will be stored
        self.widget_mappers = {
            self.ACTIONS: [("timestamp", parent.ActionTimestampEdit),
                           ("account_id", parent.ActionAccountWidget),
                           ("peer_id", parent.ActionPeerWidget)],
            self.ACTION_DETAILS: None,
            self.TRADES: [("timestamp", parent.TradeTimestampEdit),
                          ("account_id", parent.TradeAccountWidget),
                          ("asset_id", parent.TradeAssetWidget),
                          ("settlement", parent.TradeSettlementEdit),
                          ("number", parent.TradeNumberEdit),
                          ("price", parent.TradePriceEdit),
                          ("qty", parent.TradeQtyEdit),
                          ("coupon", parent.TradeCouponEdit),
                          ("fee", parent.TradeFeeEdit),
                          ("note", parent.TradeNoteEdit)],
            self.DIVIDENDS: [("timestamp", parent.DividendTimestampEdit),
                             ("account_id", parent.DividendAccountWidget),
                             ("asset_id", parent.DividendAssetWidget),
                             ("number", parent.DividendNumberEdit),
                             ("sum", parent.DividendSumEdit),
                             ("note", parent.DividendSumDescription),
                             ("sum_tax", parent.DividendTaxEdit)],
            self.TRANSFERS: [("withdrawal_account", parent.TransferFromAccountWidget),
                             ("deposit_account", parent.TransferToAccountWidget),
                             ("fee_account", parent.TransferFeeAccountWidget),
                             ("withdrawal_timestamp", parent.TransferFromTimestamp),
                             ("deposit_timestamp", parent.TransferToTimestamp),
                             ("withdrawal", parent.TransferFromAmount),
                             ("deposit", parent.TransferToAmount),
                             ("fee", parent.TransferFeeAmount),
                             ("note", parent.TransferNote)],
            self.CORP_ACTIONS: [("timestamp", parent.CorpActionTimestampEdit),
                                ("number", parent.CorpActionNumberEdit),
                                ("type", parent.CorpActionTypeCombo),
                                ("account_id", parent.CorpActionAccountWidget),
                                ("asset_id", parent.CorpActionAssetBefore),
                                ("asset_id_new", parent.CorpActionAssetAfter),
                                ("qty", parent.CorpActionQtyBeforeEdit),
                                ("qty_new", parent.CorpActionQtyAfterEdit),
                                ("basis_ratio", parent.CorpActionRatioEdit),
                                ("note", parent.CorpActionNodeEdit)]
        }
        self.dialogs = {
            # see DLG_ constants for reference
            self.ACCOUNT_TYPES: ('account_types',
                                 g_tr('TableViewConfig', g_tr('TableViewConfig', "Account Types")),
                                 [("id", None, 0, None, None),
                                  ("name", g_tr('TableViewConfig', "Account Type"), ColumnWidth.STRETCH, Qt.AscendingOrder, None)],
                                 None,
                                 None,
                                 False,
                                 None
                                 ),
            self.ACCOUNTS: ('accounts',
                            g_tr('TableViewConfig', "Accounts"),
                            [("id", None, 0, None, None),
                             ("name", g_tr('TableViewConfig', "Name"), ColumnWidth.STRETCH, Qt.AscendingOrder, None),
                             ("type_id", None, 0, None, None),
                             ("currency_id", g_tr('TableViewConfig', "Currency"), None, None, ui.ReferenceLookupDelegate),
                             ("active", g_tr('TableViewConfig', "Act."), 32, None, ui.ReferenceBoolDelegate),
                             ("number", g_tr('TableViewConfig', "Account #"), None, None, None),
                             ("reconciled_on", g_tr('TableViewConfig', "Reconciled @"), ColumnWidth.FOR_DATETIME,
                              None, ui.ReferenceTimestampDelegate),
                             ("organization_id", g_tr('TableViewConfig', "Bank"), None, None, ui.ReferencePeerDelegate),
                             ("country_id", g_tr('TableViewConfig', "CC"), 50, None, ui.ReferenceLookupDelegate)],
                            "name",
                            ("active", g_tr('TableViewConfig', "Show inactive")),
                            False,
                            [("type_id", "account_types", "id", "name", g_tr('TableViewConfig', "Account type:")),
                             ("currency_id", "currencies", "id", "name", None),
                             ("organization_id", "agents", "id", "name", None),
                             ("country_id", "countries", "id", "code", None)]
                            ),
            self.ASSETS: ("assets",
                          g_tr('TableViewConfig', "Assets"),
                          [("id", None, 0, None, None),
                           ("name", g_tr('TableViewConfig', "Symbol"), None, Qt.AscendingOrder, None),
                           ("type_id", None, 0, None, None),
                           ("full_name", g_tr('TableViewConfig', "Name"), ColumnWidth.STRETCH, None, None),
                           ("isin", g_tr('TableViewConfig', "ISIN"), None, None, None),
                           ("country_id", g_tr('TableViewConfig', "Country"), None, None, ui.ReferenceLookupDelegate),
                           ("src_id", g_tr('TableViewConfig', "Data source"), None, None, ui.ReferenceLookupDelegate)],
                          "full_name",
                          None,
                          False,
                          [("type_id", "asset_types", "id", "name", g_tr('TableViewConfig', "Asset type:")),
                           ("country_id", "countries", "id", "name", None),
                           ("src_id", "data_sources", "id", "name", None)]
            ),
            self.PEERS: ("agents_ext",
                          g_tr('TableViewConfig', "Peers"),
                          [("id", " ", 16, None, ui.ReferenceTreeDelegate),
                           ("pid", None, 0, None, None),
                           ("name", g_tr('TableViewConfig', "Name"), ColumnWidth.STRETCH, Qt.AscendingOrder, None),
                           ("location", g_tr('TableViewConfig', "Location"), None, None, None),
                           ("actions_count", g_tr('TableViewConfig', "Docs count"), None, None, ui.ReferenceIntDelegate),
                           ("children_count", None, None, None, None)],
                          "name",
                          None,
                          True,
                          None
            ),
            self.CATEGORIES: ("categories_ext",
                              g_tr('TableViewConfig', "Categories"),
                              [("id", " ", 16, None, ui.ReferenceTreeDelegate),
                               ("pid", None, 0, None, None),
                               ("name", g_tr('TableViewConfig', "Name"), ColumnWidth.STRETCH, Qt.AscendingOrder, None),
                               ("often", g_tr('TableViewConfig', "Often"), None, None, ui.ReferenceBoolDelegate),
                               ("special", None, 0, None, None),
                               ("children_count", None, None, None, None)],
                              "name",
                              None,
                              True,
                              None
            ),
            self.TAGS: ("tags",
                        g_tr('TableViewConfig', "Tags"),
                        [("id", None, 0, None, None),
                         ("tag", g_tr('TableViewConfig', "Tag"), ColumnWidth.STRETCH, Qt.AscendingOrder, None)],
                        "tag",
                        None,
                        False,
                        None
            ),
            self.COUNTRIES: ("countries",
                             g_tr('TableViewConfig', "Countries"),
                             [("id", None, 0, None, None),
                              ("name", g_tr('TableViewConfig', "Country"), ColumnWidth.STRETCH, Qt.AscendingOrder, None),
                              ("code", g_tr('TableViewConfig', "Code"), 50, None, None),
                              ("tax_treaty", g_tr('TableViewConfig', "Tax Treaty"), None, None, ui.ReferenceBoolDelegate)],
                             None,
                             None,
                             False,
                             None
            ),
            self.QUOTES: ("quotes",
                          g_tr('TableViewConfig', "Quotes"),
                          [("id", None, 0, None, None),
                           ("timestamp", g_tr('TableViewConfig', "Date"), ColumnWidth.FOR_DATETIME, None, ui.ReferenceTimestampDelegate),
                           ("asset_id", g_tr('TableViewConfig', "Asset"), None, None, ui.ReferenceLookupDelegate),
                           ("quote", g_tr('TableViewConfig', "Quote"), 100, None, None)],
                          "name",
                          None,
                          False,
                          [("asset_id", "assets", "id", "name", None)]
            )
        }
        self.actions = [
            (parent.actionExit,             "triggered()",              QtWidgets.QApplication.instance().quit),
            (parent.action_Load_quotes,     "triggered()",              partial(parent.downloader.showQuoteDownloadDialog, parent)),
            (parent.actionImportStatement,  "triggered()",              parent.statements.loadReport),
            (parent.actionImportSlipRU,     "triggered()",              parent.importSlip),
            (parent.actionBackup,           "triggered()",              parent.backup.create),
            (parent.actionRestore,          "triggered()",              parent.backup.restore),
            (parent.action_Re_build_Ledger, "triggered()",              partial(parent.ledger.showRebuildDialog, parent)),
            (parent.actionAccountTypes,     "triggered()",              partial(self.show_dialog, self.ACCOUNT_TYPES)),
            (parent.actionAccounts,         "triggered()",              partial(self.show_dialog, self.ACCOUNTS)),
            (parent.actionAssets,           "triggered()",              partial(self.show_dialog, self.ASSETS)),
            (parent.actionPeers,            "triggered()",              partial(self.show_dialog, self.PEERS)),
            (parent.actionCategories,       "triggered()",              partial(self.show_dialog, self.CATEGORIES)),
            (parent.actionTags,             "triggered()",              partial(self.show_dialog, self.TAGS)),
            (parent.actionCountries,        "triggered()",              partial(self.show_dialog, self.COUNTRIES)),
            (parent.actionQuotes,           "triggered()",              partial(self.show_dialog, self.QUOTES)),
            (parent.PrepareTaxForms,        "triggered()",              partial(parent.taxes.showTaxesDialog, parent)),
            (parent.BalanceDate,            "dateChanged(QDate)",       parent.BalancesTableView.model().setDate),
            (parent.HoldingsDate,           "dateChanged(QDate)",       parent.HoldingsTableView.model().setDate),
            (parent.BalancesCurrencyCombo,  "changed(int)",             parent.BalancesTableView.model().setCurrency),
            (parent.BalancesTableView,      "doubleClicked(QModelIndex)", parent.OnBalanceDoubleClick),
            (parent.HoldingsCurrencyCombo,  "changed(int)",             parent.HoldingsTableView.model().setCurrency),
            (parent.ReportRangeCombo,       "currentIndexChanged(int)", parent.onReportRangeChange),
            (parent.RunReportBtn,           "clicked()",                parent.onRunReport),
            (parent.SaveReportBtn,          "clicked()",                parent.reports.saveReport),
            (parent.ShowInactiveCheckBox,   "stateChanged(int)",        parent.BalancesTableView.model().toggleActive),
            (parent.DateRangeCombo,         "currentIndexChanged(int)", parent.OnOperationsRangeChange),
            (parent.ChooseAccountBtn,       "changed(int)",             parent.OperationsTableView.model().setAccount),
            (parent.SearchString,           "textChanged(QString)",     parent.OperationsTableView.model().filterText),
            (parent.AddActionDetail,        "clicked()",                partial(parent.operations.addOperationChild, TransactionType.Action)),
            (parent.RemoveActionDetail,     "clicked()",                partial(parent.operations.deleteOperationChild, TransactionType.Action)),
            (parent.DeleteOperationBtn,     "clicked()",                parent.operations.deleteOperation),
            (parent.CopyOperationBtn,       "clicked()",                parent.operations.copyOperation),
            (parent.SaveOperationBtn,       "clicked()",                parent.operations.commitOperation),
            (parent.RevertOperationBtn,     "clicked()",                parent.operations.revertOperation)
        ]

    def tr(self, name):
        pass

    def configure(self, i):
        self.models[i] = UseSqlTable(self.parent, self.table_names[i], self.table_view_columns[i],
                            relations=self.table_relations[i])
        if self.views[i]:
            delegates = ConfigureTableView(self.views[i], self.models[i], self.table_view_columns[i])
            self.delegates_storage.append(delegates)
            self.views[i].show()
        if self.widget_mappers[i]:
            self.mappers[i] = ConfigureDataMappers(self.models[i], self.widget_mappers[i], MapperDelegate)
        else:
            self.mappers[i] = None
        self.models[i].select()

    def configure_all(self):
        for table in self.table_names:
            self.configure(table)
        for action in self.actions:
            QObject.connect(action[self.ACTION_SRC], SIGNAL(action[self.ACTION_SIGNAL]), action[self.ACTION_SLOT])

    @Slot()
    def show_dialog(self, dlg_id):
        ui.ReferenceDataDialog(self.parent.db,
                               self.dialogs[dlg_id][self.DLG_TABLE],
                               self.dialogs[dlg_id][self.DLG_COLUMNS],
                               title=self.dialogs[dlg_id][self.DLG_TITLE],
                               search_field=self.dialogs[dlg_id][self.DLG_SEARCH],
                               toggle=self.dialogs[dlg_id][self.DLG_TOGGLE],
                               tree_view=self.dialogs[dlg_id][self.DLG_TREE],
                               relations=self.dialogs[dlg_id][self.DLG_RELATIONS]
                               ).exec_()
