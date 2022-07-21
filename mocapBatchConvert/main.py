from os import listdir, makedirs
from os.path import isfile, join, exists
import maya.cmds as cmds
import sys
sys.path.append("I:/script/bin/td/maya/scripts/mocapConvert/mocapBatchConvert/modules")
import mocap
reload(mocap)
from mocap import MocapImport
from datetime import datetime

def set_fps(fps = None):
    fps_string = "pal"
    if fps == 25:
        fps_string = "pal"
    if fps == 24:
        fps_string = "film"
    if fps == 30:
        fps_string = "ntsc"                
    cmds.currentUnit(t=fps_string) 

def eulerFilterCurve(animCurves, filter="euler"):
    for node in animCurves:
		cmds.filterCurve( '%s.rx' % node, '%s.ry' % node, '%s.rz' % node, filter='euler' )

def main():
    mocapFbxPath = 'J:/hx/work/prod/mcp/motiondata/export'
    rigFile = 'J:/test_project/work/progress/mcp/satou_test/rig/tianTuanMo_v005_facial.ma'
    prj = 'hx'
    template_name = 'tianYuanMoAvA'
    skeleton_path = 'J:/hx/work/prod/mcp/motiondata/maya_mocap_rig_fbx/hx_pub_char_tianYuanMoAvA.fbx'
    now = datetime.now()
    current_time = now.strftime("%Y%m%d")
    outPutPath = "J:/%s/work/daily/%s/mocap" % (prj ,current_time)
    if not exists(outPutPath):
        makedirs(outPutPath)
    remove_anim_reference = False
    shift_key = False
    onlyfiles = [f for f in listdir(mocapFbxPath) if isfile(join(mocapFbxPath, f))]
    for _file in onlyfiles:
        print(_file)
        cmds.file(rigFile, open=True, force=True)
        mocap_path = mocapFbxPath + '/' + _file
        set_fps(fps = 25)
        Root_M = cmds.ls('Root_M', long=True)
        cmds.select(Root_M)
        MocapImport(prj, template_name, skeleton_path, mocap_path)
        curve_transforms = [cmds.listRelatives(i, p=1, type='transform')[0] for i in cmds.ls(type='nurbsCurve', o=1, r=1, ni=1)]
        eulerFilterCurve(curve_transforms)
        cmds.file(rename=outPutPath+'/'+_file+".ma")
        cmds.file(save=True, type="mayaAscii")

if __name__ == '__main__':
    main()