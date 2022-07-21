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
        

def pre_import(target_namespace, template_name):
    print('pre_import', target_namespace, template_name, target_namespace, template_name)

    for node_name in ('FKIKArm1_R', 'FKIKArm2_R', 'FKIKArm1_L', 'FKIKArm2_L', 'FKIKLeg_R', 'FKIKLeg_L'):
        try:
            node = pm.PyNode('%s:%s' %(target_namespace, node_name)).FKIKBlend.set(10)
        except Exception as e:
            print(e)

def post_import(target_namespace, mocap_anim_namespace, template_name):
    print('[POST IMPORT] for tianYuanMoAvA', target_namespace, mocap_anim_namespace, template_name)
    start_time = int(pm.playbackOptions(q=True, min=True))
    end_time = int(pm.playbackOptions(q=True, max=True))
    for time in xrange(start_time, end_time + 1):

        pm.currentTime(time)

        for ctrl_name, joint_name, target_name in [
                ('PoleArm1_R', 'Elbow_R', 'Elbow_R'),
                ('PoleArm2_R', 'ElbowB_R', 'ElbowB_R'),
                ('PoleArm1_L', 'Elbow_L', 'Elbow_L'),
                ('PoleArm2_L', 'ElbowB_L', 'ElbowB_L'),
                ('PoleLeg_R', 'Knee_R', 'Knee_R'),
                ('PoleLeg_L', 'Knee_L', 'Knee_L')]:

            ctrl = pm.PyNode('%s:%s' % (target_namespace, ctrl_name))
            joint = pm.PyNode('%s:%s' % (target_namespace, joint_name))
            target = pm.PyNode('%s:%s' % (mocap_anim_namespace, target_name))
            approx_pos(ctrl, joint, target, 0.0001, 50)
            ctrl.translate.setKey()

    for node_name in ('FKIKArm1_R', 'FKIKArm2_R', 'FKIKArm1_L', 'FKIKArm2_L'):
        try:
            node = pm.PyNode('%s:%s' % (target_namespace, node_name)).FKIKBlend.set(0)
        except Exception as e:
            print(e)

