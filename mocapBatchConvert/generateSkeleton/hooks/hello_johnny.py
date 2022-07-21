#-*- coding:utf-8 -*-
import os

import pymel.core as pm


#-*- coding:utf-8 -*-
import pymel.core as pm


def approx_pos(ctrl, joint, target, precision, max_count, count=0):
    '''Approximate position of object to target
    '''
    diff = target.getTranslation(
        space='world') - joint.getTranslation(space='world')
    if count < max_count and diff.length() > precision:
        ctrl_new_pos = ctrl.getTranslation(space='world') + diff
        ctrl.setTranslation(ctrl_new_pos, space='world')
        approx_pos(ctrl, joint, target, precision, max_count, count + 1)


def post_import_adv(target_namespace, mocap_anim_namespace):
    start_time = int(pm.playbackOptions(q=True, min=True))
    end_time = int(pm.playbackOptions(q=True, max=True))
    for time in xrange(start_time, end_time + 1):
        pm.currentTime(time)

        for ctrl_name, joint_name, target_name in [
                ('PoleArm_L', 'Elbow_L', 'Elbow_MoCap_L'),
                ('PoleArm_R', 'Elbow_R', 'Elbow_MoCap_R'),
                ('PoleLeg_L', 'Knee_L', 'Knee_MoCap_L'),
                ('PoleLeg_R', 'Knee_R', 'Knee_MoCap_R')]:

            ctrl = pm.PyNode('%s:%s' % (target_namespace, ctrl_name))
            joint = pm.PyNode('%s:%s' % (target_namespace, joint_name))
            target = pm.PyNode('%s:%s' % (mocap_anim_namespace, target_name))
            approx_pos(ctrl, joint, target, 0.0001, 50)
            ctrl.translate.setKey()


def post_import_adv_robot(target_namespace, mocap_anim_namespace):
    start_time = int(pm.playbackOptions(q=True, min=True))
    end_time = int(pm.playbackOptions(q=True, max=True))
    for time in xrange(start_time, end_time + 1):

        pm.currentTime(time)

        for ctrl_name, joint_name, target_name in [
                ('PoleArm_L', 'Elbow_L', 'Elbow_MoCap_L'),
                ('PoleArm_R', 'Elbow_R', 'Elbow_MoCap_R')]:

            ctrl = pm.PyNode('%s:%s' % (target_namespace, ctrl_name))
            joint = pm.PyNode('%s:%s' % (target_namespace, joint_name))
            target = pm.PyNode('%s:%s' % (mocap_anim_namespace, target_name))
            approx_pos(ctrl, joint, target, 0.0001, 50)


def pre_import(target_namespace, template_name):
    print 'pre_import', target_namespace, template_name
    # turn on IK
    for node_name in ('FKIKArm_L', 'FKIKArm_R', 'FKIKLeg_L', 'FKIKLeg_R'):
        try:
            node = pm.PyNode('%s:%s' %
                             (target_namespace, node_name)).FKIKBlend.set(10)
        except Exception as e:
            print e


def post_import(target_namespace, mocap_anim_namespace, template_name):
    # if template_name == 'adv_old':
    print '[POST IMPORT] improve adv by approx pos'
    if template_name == 'adv_robot':
        post_import_adv_robot(target_namespace, mocap_anim_namespace)
    else:
        post_import_adv(target_namespace, mocap_anim_namespace)

    print '[POST IMPORT] set controller of hand to FK'
    # set hand to FK
    for node_name in ('FKIKArm_L', 'FKIKArm_R'):
        try:
            node = pm.PyNode('%s:%s' %
                             (target_namespace, node_name)).FKIKBlend.set(0)
        except Exception as e:
            print e


def get_default_skeleton_path(target_namespace):
    for ref in pm.listReferences():
        if target_namespace != ref.namespace:
            continue
        ref_dir = os.path.dirname(ref.path)
        ref_dir = os.path.abspath(ref_dir)
        pub_dir = os.path.join(ref_dir, 'pub')
        if not os.path.isdir(pub_dir):
            return None
        for file_ in os.listdir(pub_dir):
            return os.path.join(pub_dir, file_)
