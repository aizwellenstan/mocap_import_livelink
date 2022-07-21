#-*- coding:utf-8 -*-
import pymel.core as pm


def create_fk_stitch(ns):
    temp_ctrl = pm.PyNode('%s:r_legA_knee_FK_ctrl' % ns)

    fk_ctrl_name = '%s:l_legA_ankle_FK_ctrlShape' % ns
    target_joint_name = '%s:l_legA_ankle_FK_ctrl' % ns
    if not pm.ls(fk_ctrl_name):
        fk_ctrl = pm.duplicate(temp_ctrl.getShape(),
                               name=fk_ctrl_name, addShape=True)[0]
        fk_ctrl.visibility.set(True)
        pm.parent(
            fk_ctrl, pm.PyNode(target_joint_name), shape=True, relative=True)

    fk_ctrl_name = '%s:r_legA_ankle_FK_ctrlShape' % ns
    target_joint_name = '%s:r_legA_ankle_FK_ctrl' % ns
    if not pm.ls(fk_ctrl_name):
        fk_ctrl = pm.duplicate(temp_ctrl.getShape(),
                               name=fk_ctrl_name, addShape=True)[0]
        fk_ctrl.visibility.set(True)
        pm.parent(
            fk_ctrl, pm.PyNode(target_joint_name), shape=True, relative=True)


def pre_import(target_namespace, template_name):
    print 'pre_import', target_namespace, template_name
    create_fk_stitch(target_namespace)
    pm.setAttr('%s:r_armA_wrist_ctrl.FK_2_IK' % target_namespace, 1)
    pm.setAttr('%s:l_armA_wrist_ctrl.FK_2_IK' % target_namespace, 1)
    pm.setAttr('%s:r_legA_ankle_ctrl.FK_2_IK' % target_namespace, 1)
    pm.setAttr('%s:l_legA_ankle_ctrl.FK_2_IK' % target_namespace, 1)
    pm.setAttr('%s:m_spineA_head_ctrl.neckCtrl' % target_namespace, 1)


def post_import(target_namespace, mocap_anim_namespace, template_name):
    print 'post_import', target_namespace, mocap_anim_namespace, template_name

