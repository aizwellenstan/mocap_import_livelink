#-*- coding:utf-8 -*-
import pymel.core as pm


def parent_constraint(joint, controller, maintain_offset=False):
    controller_name = controller.stripNamespace()
    constraint_name = 'mocap_matchmaker_%s_parent_constraint' % controller_name
    constraint = pm.parentConstraint(joint, controller, maintainOffset=maintain_offset,
                                     name=constraint_name)
    return [constraint]


def point_constraint(joint, controller, maintain_offset=False):
    controller_name = controller.stripNamespace()
    constraint_name = 'mocap_matchmaker_%s_point_constraint' % controller_name

    constraint = pm.pointConstraint(joint, controller, maintainOffset=maintain_offset,
                                    name=constraint_name)
    return [constraint]


def orient_constraint(joint, controller, maintain_offset=True):
    locator_name = 'mocap_matchmaker_%s_locator' % controller.stripNamespace()
    locator = pm.spaceLocator(name=locator_name)
    pm.pointConstraint(joint, locator)
    pm.pointConstraint(joint, locator, e=True, rm=True)
    cro = pm.getAttr(controller+'.rotateOrder')
    pm.setAttr(locator+'.rotateOrder',cro)
    pm.orientConstraint(joint, locator,mo=0)
    pm.orientConstraint(joint, locator, e=True, rm=True)

    controller_name = controller.stripNamespace()

    constraint = None
    # constraint all
    try:
        constraint_name = 'mocap_matchmaker_%s_orient_constraint' % controller_name
        constraint = pm.orientConstraint(locator, controller,
                                         maintainOffset=maintain_offset,
                                         name=constraint_name)
    except Exception as e:
        pm.delete(locator)
        print 'xyz', e

    # constraint x
    if constraint is None:
        try:
            joint.rotateX.connect(controller.rotateX)
        except Exception as e:
            print 'x', e

    # constraint y
    if constraint is None:
        try:
            joint.rotateY.connect(controller.rotateY)
        except Exception as e:
            print 'y', e

    # constraint z
    if constraint is None:
        try:
            joint.rotateZ.connect(controller.rotateZ)
        except Exception as e:
            print 'z', e

    if constraint is None:
        return []
    else:
        pm.parent(locator, joint)
        return [constraint, locator]


def orient_connect(joint, controller, maintain_offset=False):
    if controller.rotateX.isLocked() is False:
        joint.rotateX.connect(controller.rotateX)
    if controller.rotateY.isLocked() is False:
        joint.rotateY.connect(controller.rotateY)
    if controller.rotateZ.isLocked() is False:
        joint.rotateZ.connect(controller.rotateZ)
    return []


def pilot_constraint(joint_, controller, axis, ratio):
    loc_rot = pm.spaceLocator()
    loc_pos = pm.spaceLocator()
    pm.parent(loc_pos, loc_rot)
    for subaxis in axis.split(','):
        if subaxis.startswith('-'):
            loc_pos.attr('translate%s' % subaxis[-1].upper()).set(-ratio)
        else:
            loc_pos.attr('translate%s' % subaxis[-1].upper()).set(ratio)

    pm.parentConstraint(joint_, loc_rot)
    pm.parentConstraint(joint_, loc_rot, e=True, rm=True)
    pm.parent(loc_rot, joint_)

    constraint = pm.pointConstraint(loc_pos, controller, maintainOffset=False)
    return [constraint, loc_rot, loc_pos]
