#-*- coding:utf-8 -*-
VERSION = 'V2.3.3'

# standard library imports
import ConfigParser
import csv
import glob
import os
import re
import sys

# related third party imports
import maya
import pymel.core as pm

from Qt import __binding__, QtGui, QtCore, QtWidgets
if __binding__ == 'PySide2':
    import pyside2uic as pysideuic
    from shiboken2 import wrapInstance
elif __binding__ == 'PySide':
    import pysideuic
    from shiboken import wrapInstance

def getMayaMainWindow():
    import maya.OpenMayaUI as apiUI

    ptr = apiUI.MQtUtil.mainWindow()
    if ptr is not None:
        return wrapInstance(long(ptr), QtWidgets.QWidget)

def add_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)
# local application/library specific imports
# add_path(os.path.dirname(__file__))
import core

# reload for test
if os.environ.get('NMATEST', None):
    reload(core)


TEMPLATE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '.', 'templates'))


def get_maya_main_window():
    ptr = maya.OpenMayaUI.MQtUtil.mainWindow()
    main_win = sip.wrapinstance(long(ptr), QtCore.QObject)
    return main_win


def maya_ui_to_qt_object(maya_ui_name):
    '''
    Given the name of a Maya UI element of any type,
    return the corresponding QWidget or QAction.
    If the object does not exist, returns None
    '''
    ptr = maya.OpenMayaUI.MQtUtil.findControl(maya_ui_name)
    if ptr is None:
        ptr = maya.OpenMayaUI.MQtUtil.findLayout(maya_ui_name)
    if ptr is None:
        ptr = maya.OpenMayaUI.MQtUtil.findMenuItem(maya_ui_name)
    if ptr is not None:
        return sip.wrapinstance(long(ptr), QtCore.QObject)
    return None


class InputDialog(QtWidgets.QDialog):

    def __init__(self, parent=None, title='user input', label='comment', text=''):
        #QtWidgets.QWidget.__init__(self, parent)
        super(InputDialog, self).__init__(parent)

        self.init_widget(label, text)
        self.init_layout()
        self.init_connect()

        self.setWindowTitle(title)

    def init_widget(self, label, text):
        self.label = QtWidgets.QLabel(label)
        self.text = QtWidgets.QLineEdit(text)
        self.ok_button = QtWidgets.QPushButton(u'Ok')
        self.cancel_button = QtWidgets.QPushButton(u'Cancel')

    def init_layout(self):
        main_layout = QtWidgets.QVBoxLayout()

        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.label)
        input_layout.addWidget(self.text)
        main_layout.addLayout(input_layout)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.resize(300, 100)

    def ok_callback(self):
        self.status = True
        self.close()

    def cancel_callback(self):
        self.status = False
        self.close()

    def init_connect(self):
        self.ok_button.clicked.connect(self.ok_callback)
        self.cancel_button.clicked.connect(self.cancel_callback)


class FileDialog(QtWidgets.QDialog):

    def __init__(self, title, default_path, ext, type_, parent=None):
        super(FileDialog, self).__init__(parent)

        self.path = default_path
        self.ext = ext
        self.is_selected = False
        self.type_ = type_

        self.setWindowTitle(title)

        self.init_widget(default_path)
        self.init_layout()
        self.init_connect()

    def init_widget(self, default_path):
        self.ui_path = QtWidgets.QLineEdit(default_path)
        self.ui_select = QtWidgets.QPushButton('...')
        self.ui_ok = QtWidgets.QPushButton(u'Ok')

    def init_layout(self):
        # set font
        font = QtGui.QFont()
        font.setPixelSize(20)
        self.ui_ok.setFont(font)

        # set size policy
        self.ui_path.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.ui_select.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.ui_ok.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(self.ui_path)
        path_layout.addWidget(self.ui_select)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(path_layout)
        main_layout.addWidget(self.ui_ok)

        self.setLayout(main_layout)
        self.resize(500, 100)

    def init_connect(self):
        self.ui_select.clicked.connect(self.select_callback)
        self.ui_ok.clicked.connect(self.ok_callback)

    def select_callback(self):
        current_path = unicode(self.ui_path.text())
        current_directory = os.path.split(current_path)[0]
        if self.type_ == 'open':
            path = unicode(QtWidgets.QFileDialog.getOpenFileName(
                self, u'choose file', current_directory, '*.%s' % self.ext)[0])
        elif self.type_ == 'save':
            path = unicode(QtWidgets.QFileDialog.getSaveFileName(
                self, u'input save file name', current_directory, '*.%s' % self.ext)[0])
        else:
            return
        if path:
            self.ui_path.setText(path)

    def ok_callback(self):
        self.is_selected = True
        self.path = unicode(self.ui_path.text())
        self.close()


class MocapMatchmakerWidget(QtWidgets.QMainWindow):

    template_root = TEMPLATE_ROOT

    ui_create = None
    ui_export = None
    ui_import_mocap = None

    ui_projects = None
    ui_templates = None
    ui_projects_label = None
    ui_templates_label = None

    def __init__(self, template_root=None, parent=None):
        super(MocapMatchmakerWidget, self).__init__(parent)
        if template_root is not None:
            self.template_root = template_root
        self.setWindowTitle(u'Anim / Mocap ツール %s' % VERSION)
        self.init_widget()
        self.init_layout()
        self.init_connect()
        self.init_menu()

    def init_widget(self):
        """Initial widgets.
        """
        self.ui_create = QtWidgets.QPushButton(u'Generate Mocap Skeleton', self)
        self.ui_export = QtWidgets.QPushButton(u'Export Mocap Skeleton', self)
        self.ui_import_mocap = QtWidgets.QPushButton(u'Import Mocap Animation', self)

        self.ui_projects_label = QtWidgets.QLabel(u'Project:')
        self.ui_projects = QtWidgets.QComboBox()
        self.ui_templates_label = QtWidgets.QLabel(u'Type:')
        self.ui_templates = QtWidgets.QComboBox()

        self.refresh_ui_projects()
        self.refresh_ui_templates()

    def refresh_ui_projects(self):
        """Refresh project list by search template path.
        """
        projects = glob.glob(os.path.join(self.template_root, '*'))
        projects = filter(os.path.isdir, projects)
        projects = map(lambda p: os.path.split(p)[-1], projects)
        projects = sorted(projects)

        self.ui_projects.clear()
        map(lambda t: self.ui_projects.addItem(t), projects)

    def remove_project(self, project_name):
        """Remove project from project list.
        """
        index = self.ui_projects.findText(project_name)
        self.ui_projects.removeItem(index)

    def refresh_ui_templates(self):
        """Refresh project list by search template path with selected project.
        """
        project_name = str(self.ui_projects.currentText())
        templates = glob.glob(
            os.path.join(self.template_root, project_name, '*.yaml'))
        templates = map(lambda p: os.path.split(p)[-1], templates)
        templates = filter(lambda p: p.endswith('.yaml'), templates)
        templates = map(lambda p: os.path.splitext(p)[0], templates)
        templates = sorted(templates)
        print self.template_root

        self.ui_templates.clear()
        map(lambda t: self.ui_templates.addItem(t), templates)

    def init_layout(self):
        """Initial layout.
        """
        # set font
        font = QtGui.QFont()
        font.setPixelSize(20)
        for ui in (self.ui_create, self.ui_export, self.ui_import_mocap,
                   self.ui_projects, self.ui_projects_label,
                   self.ui_templates, self.ui_templates_label):
            ui.setFont(font)

        # set size policy
        for ui in (self.ui_create, self.ui_export, self.ui_import_mocap,
                   self.ui_projects, self.ui_templates):
            ui.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # set layout
        project_layout = QtWidgets.QHBoxLayout()
        project_layout.addWidget(self.ui_projects_label)
        project_layout.addWidget(self.ui_projects)

        template_layout = QtWidgets.QHBoxLayout()
        template_layout.addWidget(self.ui_templates_label)
        template_layout.addWidget(self.ui_templates)

        func_layout = QtWidgets.QVBoxLayout()
        func_layout.addLayout(project_layout)
        func_layout.addLayout(template_layout)
        func_layout.addWidget(self.ui_create)
        func_layout.addWidget(self.ui_export)
        func_layout.addWidget(self.ui_import_mocap)

        w = QtWidgets.QWidget()
        w.setLayout(func_layout)
        self.setCentralWidget(w)
        self.resize(350, 200)

    def init_connect(self):
        """Initial connections.
        """
        self.ui_create.clicked.connect(self.create_callback)
        self.ui_export.clicked.connect(self.export_callback)
        self.ui_import_mocap.clicked.connect(self.import_mocap_callback)
        self.ui_projects.currentIndexChanged.connect(self.refresh_ui_templates)

    def init_menu(self):
        """Initial menu.
        """
        action_add_namespace = QtWidgets.QAction(u'&add / edit Namespace', self)
        action_add_namespace.triggered.connect(self.add_namespace_callback)
        action_open_namespace_editor = QtWidgets.QAction(
            u'&Open Namespace Editor', self)
        action_open_namespace_editor.triggered.connect(
            lambda *args: pm.mel.eval('namespaceEditor;'))

        menubar = self.menuBar()
        menu_others = menubar.addMenu(u'&Other')
        menu_others.addAction(action_add_namespace)
        menu_others.addAction(action_open_namespace_editor)

        # menu_others.setWidth(150)
        menubar.setStyleSheet('''
            QMenu {
                margin-left: 10px;
                margin-right: 10px;
                margin-bottom: 10px;
            }''')

    def add_namespace(self, new_namespace, target):
        status = core.add_namespace(new_namespace, target)
        if status is False:
            QtWidgets.QMessageBox.critical(
                self, u'Warning', u'Add namespace "%s" failed' % new_namespace)
            if pm.ls(new_namespace):
                QtWidgets.QMessageBox.critical(
                    self, u'Warning', u'namespace "%s" same name node exists' % new_namespace)
                pm.select(new_namespace)

    def create_callback(self):
        """callback of ui_create.
        """
        # get target, project, template, rule
        target = pm.ls(sl=1)[0]

        project_name = str(self.ui_projects.currentText())
        template_name = str(self.ui_templates.currentText())

        template_path = os.path.join(
            self.template_root, project_name, '%s.ma' % template_name)

        mapping_path = os.path.join(
            self.template_root, project_name, '%s.yaml' % template_name)
        mapping_rules = core.read_yaml(mapping_path)

        # create skeleton
        skeleton_root = core.create_skeleton(
            template_path, mapping_rules, target)

        # add namespace
        asset_file = os.path.split(pm.sceneName())[-1]
        asset_name = os.path.splitext(asset_file)[0]
        asset_name = asset_name.replace('.', '_')
        self.add_namespace(asset_name, skeleton_root)

    def add_namespace_callback(self):
        """callback of ui_add_namespace.
        """
        # REF:
        # http://download.autodesk.com/us/maya/2011help/PyMel/generated/functions/pymel.core.system/pymel.core.system.namespace.html
        sel = pm.ls(sl=1) and pm.ls(sl=1)[0] or None
        if not sel:
            return
        old_namespace = sel.namespace()[:-1]
        input_dialog = InputDialog(self, title=u'add / edit namespace',
                                   label=u'namespace', text=old_namespace)
        input_dialog.exec_()
        if not input_dialog.status:
            return
        new_namespace = unicode(input_dialog.text.text().toUtf8(),
                                encoding='utf-8')
        if not new_namespace:
            return

        self.add_namespace(new_namespace, sel)

    def export_callback(self):
        """callback of ui_export.
        """
        sel = pm.ls(sl=1) and pm.ls(sl=1)[0] or None
        if not sel:
            QtWidgets.QMessageBox.about(self, u'Message', u'Please choose skeleton!!!')
            return

        file_path, file_name = os.path.split(pm.sceneName())
        file_name = os.path.splitext(file_name)[0]
        file_name = file_name.replace('.', '_')

        project_name = str(self.ui_projects.currentText())
        default_path = self.get_default_skeleton_root(file_name)
        if not default_path:
            default_path = file_path
        default_path = os.path.join(default_path, '%s_mocap.fbx' % file_name)

        dialog = FileDialog(u'choose mocap skeleton save folder', default_path,
                            'fbx', 'save', self)
        dialog.exec_()
        if dialog.is_selected is False:
            return
        export_path = dialog.path

        core.export_skeleton(sel, export_path.replace('\\', '/'))

        QtWidgets.QMessageBox.about(self, u'Message', u'export success!!!')

    def get_default_skeleton_root(self, asset_name):
        """Get default skeleton root by hardcode project path.
        """
        project_name = str(self.ui_projects.currentText())
        if project_name != 'victory':
            type_dict = {}
            type_dict['C'] = 'Char'
            type_dict['P'] = 'Props'
            type_dict['S'] = 'Set'
            type_dict['JS'] = 'Unhuman'
            if asset_name and len(asset_name.split('_')) > 2:
                type_short = asset_name.split('_')[1]
            else:
                return ''
            type_ = type_dict.get(type_short, None)
            if type_ is None:
                return ''
            default_root = r'J:\%s\lib\model\%s\%s\rig\pub' % (
                project_name, type_, asset_name)
            if project_name == 'hello_johnny':
                default_root = r'J:\%s_pv\lib\model\%s\%s\rig\pub' % (
                    project_name, type_, asset_name)
            return default_root
        elif project_name == 'victory':
            asset_type = asset_name[0:2]

            default_root = r'J:\%s\work\lib\asset\%s\%s\rig\mcp' %(
                project_name, asset_type, asset_name)

            if os.path.isdir(default_root):
                getVersionList = os.listdir(default_root)
                if getVersionList != None:
                    myDict = {}
                    for i in getVersionList:
                        tmp = '{:05d}'.format(int(i.split('v')[1])) # '{:05d}' incase
                        myDict[tmp] = i
                    maxVerion = myDict[sorted(myDict, reverse=True)[0]]
                    path = os.path.join(default_root, maxVerion)
                    return path
                else:
                    return None

    def get_default_skeleton_path(self, asset_name):
        project_name = str(self.ui_projects.currentText())

        target_namespace = pm.ls(sl=True)[0].namespace()[:-1]
        default_path = core.get_default_skeleton_path(
            project_name, target_namespace)
        if default_path is not None:
            return default_path

        # get path from default method
        default_path = self.get_default_skeleton_root(asset_name)
        print default_path

        try:
            file_name = ""
            print default_path
            if os.path.isdir(default_path):
                for f in os.listdir(default_path):
                    if f.endswith('.fbx'):
                        file_name = f
        except:
            print u'No permisssion: %s' % default_path
            return None
        default_file_path = os.path.join(default_path, file_name)
        return default_file_path

    def get_default_mocap_root(self, asset_name):
        return 'J:/victory/work/prod/mcp/'

    def import_mocap_callback(self,
                              use_default_skeleton_path=False,
                              remove_anim_reference=True,
                              shift_key=False):
        """callback of ui_import_mocap.
        """
        if os.environ.get('NMATEST', None):
            self.import_mocap(
                use_default_skeleton_path, remove_anim_reference, shift_key)
        else:
            try:
                self.import_mocap(
                    use_default_skeleton_path, remove_anim_reference, shift_key)
            except Exception as e:
                print e
                QtWidgets.QMessageBox.critical(self, 'Import Mocap Error', repr(e))

    def get_path_from_user(self, title, default, ext):
        dialog = FileDialog(title, default, ext, 'open', self)
        dialog.exec_()

        if dialog.is_selected is False:
            return None
        if not os.path.isfile(dialog.path):
            QtWidgets.QMessageBox.about(self, u'Message', u'File not exist!!!')
            return None
        return dialog.path

    def import_mocap(self,
                     use_default_skeleton_path,
                     remove_anim_reference,
                     shift_key):
        """Import mocap animation.
        """
        # get target info
        if not pm.ls(sl=1):
            raise Exception('Please select Root of character first')
        target = pm.ls(sl=1)[0]
        target_namespace = target.namespace()[:-1]
        asset_name = target_namespace.split('_')[0]

        project_name = str(self.ui_projects.currentText())
        template_name = str(self.ui_templates.currentText())
        # get skeleton_path
        skeleton_path = self.get_default_skeleton_path(asset_name)
        if not use_default_skeleton_path:
            skeleton_path = self.get_path_from_user(
                u'Choose mocap skeleton', skeleton_path, 'fbx')
        if skeleton_path is None:
            raise Exception(
                'Please select skeleton path !!!')
        if not os.path.isfile(skeleton_path):
            raise Exception(
                'Mocap skeleton path: %s does not exist !!!' % skeleton_path)

        # get mocap_anim_path
        mocap_path = self.get_default_mocap_root(asset_name)
        mocap_path = self.get_path_from_user(
            u'Choose mocap Animation', mocap_path, 'fbx')
        if skeleton_path is None:
            raise Exception(
                'Please select mocap path !!!')
        if not os.path.isfile(mocap_path):
            raise Exception(
                'Mocap animation path: %s does not exist !!!' % mocap_path)

        # get mapping path
        mapping_path = os.path.join(
            self.template_root, project_name, '%s.yaml' % template_name)
        mapping_rules = core.read_yaml(mapping_path)

        # import_animation
        mocap_namespace = core.import_animation(
            target,
            skeleton_path,
            mocap_path,
            project_name,
            template_name,
            mapping_rules)

        # remove anim reference
        if remove_anim_reference:
            for ref in pm.listReferences():
                if ref.namespace == mocap_namespace.split(':')[0]:
                    ref.remove()

        # shift key to 101
        if shift_key:
            mapping_rules = core.read_yaml(mapping_path)

            start_frame = pm.playbackOptions(q=True, minTime=True)
            end_frame = pm.playbackOptions(q=True, maxTime=True)
            core.shift_keyframes_for_animated_nodes(
                namespace=target_namespace, from_frame=start_frame,
                to_frame=101, mapping_rules=mapping_rules)
            pm.playbackOptions(minTime=101)
            pm.playbackOptions(maxTime=end_frame - start_frame + 101)


def run():
    global mocap_matchmaker_widget
    try:
        mocap_matchmaker_widget.close()
    except:
        pass
    mocap_matchmaker_widget = MocapMatchmakerWidget(
        parent=getMayaMainWindow())
    mocap_matchmaker_widget.show()

if __name__ == '__main__':
    run()
