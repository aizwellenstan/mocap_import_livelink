import csv
import maya.cmds as cmds
import sys
import os
from os import listdir
from os.path import isfile, join
import pymel.core as pm

def add_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)
python_version = '%d.%d' % sys.version_info[:2]
print(python_version)

def set_playback_range_to_fit_keyframes():
    pm.playbackOptions(minTime=start_frame)
    pm.playbackOptions(maxTime=end_frame)

def cleanData(data):
    newData = []
    lastTimeCode = 0
    lastData = []
    for d in data:
        if len(d) < 1: continue
        timeCode = int(d[0][-3:])
        if d[1] == "0": continue
        if lastTimeCode > 0:
            if timeCode - lastTimeCode > 1:
                for i in range(0, timeCode - lastTimeCode):
                    newData.append(lastData)
        newData.append(d)
        lastData = d
        lastTimeCode = timeCode
    return newData
    
def createAnimationArr(data):
    animationArr = []
    for d in data:
        if len(d) < 3: continue
        dataDict = {}
        dataDict['EyeBlinkLeft'] = float(d[2])

        dataDict['EyeLookDownLeft'] = float(d[3])*-39

        dataDict['EyeLookInLeft'] = float(d[4])*-49

        dataDict['EyeLookOutLeft'] = float(d[5])*49

        dataDict['EyeLookUpLeft'] = float(d[6])*26

        dataDict['EyeSquintLeft'] = float(d[7])

        dataDict['EyeWideLeft'] = float(d[8])

        dataDict['EyeBlinkRight'] = float(d[9])

        dataDict['EyeLookDownRight'] = float(d[10])*-39

        dataDict['EyeLookInRight'] = float(d[11])*49

        dataDict['EyeLookOutRight'] = float(d[12])*-49

        dataDict['EyeLookUpRight'] = float(d[13])*26

        dataDict['EyeSquintRight'] = float(d[14])

        dataDict['EyeWideRight'] = float(d[15])

        dataDict['JawForward'] = float(d[16])

        dataDict['JawRight'] = float(d[17])

        dataDict['JawLeft'] = float(d[18])

        dataDict['JawOpen'] = float(d[19])

        dataDict['BrowDownLeft'] = float(d[43])

        dataDict['BrowDownRight'] = float(d[44])

        dataDict['BrowInnerUp'] = float(d[45])

        dataDict['BrowOuterUpLeft'] = float(d[46])

        dataDict['BrowOuterUpRight'] = float(d[47])

        dataDict['CheekPuff'] = float(d[48])

        dataDict['CheekSquintLeft'] = float(d[49])
        
        dataDict['CheekSquintRight'] = float(d[50])

        dataDict['NoseSneerLeft'] = float(d[51])

        dataDict['NoseSneerRight'] = float(d[52])
        animationArr.append(dataDict)
    return animationArr

def selectNurbsCurve(nurbsCurveName):
    curve_transforms = [cmds.listRelatives(i, p=1, type='transform')[0] for i
    in cmds.ls(type='nurbsCurve', o=1, r=1, ni=1)]

    for curve in curve_transforms:
        if nurbsCurveName == curve:
            return curve
    return ""

# selectNurbsCurve("UpEyeLid_R")

def read_yaml(path):
    u"""Read data from path as yaml format.
    """
    with open(path) as f:
        return yaml.load(f)

def setKeyframes(data):
    cmds.setKeyframe('face.EyeBlinkRight', value=1, time=0)

    print(len(data))
    frame = 0
    for d in data:
        for key, val in d.items():
            if key == "EyeLookDownRight":
                if val < 0:
                    cmds.setKeyframe('AimEye_R.translateY', value=val, time=frame)
                    cmds.setKeyframe('AimEyeB_R.translateY', value=val, time=frame)
                    cmds.setKeyframe('AimEyeC_R.translateY', value=val, time=frame)
            elif key == "EyeLookUpRight":
                if val > 0:
                    cmds.setKeyframe('AimEye_R.translateY', value=val, time=frame)
                    cmds.setKeyframe('AimEyeB_R.translateY', value=val, time=frame)
                    cmds.setKeyframe('AimEyeC_R.translateY', value=val, time=frame)
            elif key == "EyeLookDownLeft":
                if val < 0:
                    cmds.setKeyframe('AimEye_L.translateY', value=val, time=frame)
                    cmds.setKeyframe('AimEyeB_L.translateY', value=val, time=frame)
                    cmds.setKeyframe('AimEyeC_L.translateY', value=val, time=frame)
            elif key == "EyeLookUpLeft":
                if val > 0:
                    cmds.setKeyframe('AimEye_L.translateY', value=val, time=frame)
                    cmds.setKeyframe('AimEyeB_L.translateY', value=val, time=frame)
                    cmds.setKeyframe('AimEyeC_L.translateY', value=val, time=frame)
            elif key == "EyeLookInLeft":
                if val < 0:
                    cmds.setKeyframe('AimEye_L.translateX', value=val, time=frame)
                    cmds.setKeyframe('AimEyeB_L.translateX', value=val, time=frame)
                    cmds.setKeyframe('AimEyeC_L.translateX', value=val, time=frame)
            elif key == "EyeLookOutLeft":
                if val > 0:
                    cmds.setKeyframe('AimEye_L.translateX', value=val, time=frame)
                    cmds.setKeyframe('AimEyeB_L.translateX', value=val, time=frame)
                    cmds.setKeyframe('AimEyeC_L.translateX', value=val, time=frame)
            elif key == "EyeLookInRight":
                if val > 0:
                    cmds.setKeyframe('AimEye_R.translateX', value=val, time=frame)
                    cmds.setKeyframe('AimEyeB_R.translateX', value=val, time=frame)
                    cmds.setKeyframe('AimEyeC_R.translateX', value=val, time=frame)
            elif key == "EyeLookOutRight":
                if val < 0:
                    cmds.setKeyframe('AimEye_R.translateX', value=val, time=frame)
                    cmds.setKeyframe('AimEyeB_R.translateX', value=val, time=frame)
                    cmds.setKeyframe('AimEyeC_R.translateX', value=val, time=frame)
            else:
                cmds.setKeyframe('face.'+key, value=val, time=frame)
        
        frame += .2

def getData(path):
    data = []
    with open(path) as f:
        reader = csv.reader(f)
        header = next(reader)
        data = [row for row in reader]
       
    return data

def insertKey():
    facialPath = "J:/test_project/work/progress/mcp/satou_test/facial/facialData"
    rigFile = 'J:/test_project/work/progress/mcp/satou_test/rig/tianTuanMo_v006_guide.ma'
    rigFile = 'J:/test_project/work/progress/mcp/satou_test/rig/tianTuanMo_v005_facial.ma'
    
    outPutPath = 'J:/test_project/work/progress/mcp/satou_test/facial/maya'

    onlyfiles = [f for f in listdir(facialPath) if isfile(join(facialPath, f))]

    for f in onlyfiles:
        filePath = facialPath+'/'+f
        data = getData(filePath)
        data = cleanData(data)
        animationArr = createAnimationArr(data)
        fileName = os.path.splitext(f)[0]
        print(fileName)
        cmds.file(rigFile, open=True, force=True)
        setKeyframes(animationArr)
        cmds.file(rename=outPutPath+'/'+fileName+".ma")
        cmds.file(save=True, type="mayaAscii")
