#-*- coding:utf-8 -*-
# standard library imports
import os
import sys

# local application/library specific imports
import mocap_matchmaker

if os.environ.get('NMATEST', None):
    reload(mocap_matchmaker)


class MocapImporterWidget(mocap_matchmaker.MocapMatchmakerWidget):

    def __init__(self, parent=None):
        super(MocapImporterWidget, self).__init__(parent=parent)
        self.simple_mode()
        self.remove_project('adv')

    def simple_mode(self):
        self.ui_create.hide()
        self.ui_export.hide()
        self.resize(350, 100)

    def import_mocap_callback(self):
        super(MocapImporterWidget, self).import_mocap(
            use_default_skeleton_path=True,
            remove_anim_reference=True,
            shift_key=True)


def run():
    global mocap_importer_widget
    try:
        mocap_importer_widget.close()
    except:
        pass
    mocap_importer_widget = MocapImporterWidget(
        parent=mocap_matchmaker.get_maya_main_window())
    mocap_importer_widget.show()

if __name__ == '__main__':
    run()

