#-*- coding:utf-8 -*-
# standard library imports
from inspect import getmembers, isfunction
import functools
import json
import os
import sys

# related third party imports
import pymel.core as pm

# local application/library specific imports
import mapping
import hooks

if os.environ.get('NMATEST', None):
    reload(mapping)
    reload(hooks)


def add_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)
# add path for yaml
python_version = '%d.%d' % sys.version_info[:2]
add_path(r'I:\script\bin\td\3rd\lib\python\%s' % python_version)
import yaml


def write_yaml(data, path):
    u"""Write data to path as yaml format.
    """
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, indent=4)


def read_yaml(path):
    u"""Read data from path as yaml format.
    """
    with open(path) as f:
        return yaml.load(f)


def write_json(data, path):
    u"""Write data to path as json format.
    """
    with open(path, 'w') as f:
        f.write(
            json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))


def read_json(path):
    u"""Read data from path as json format.
    """
    with open(path) as f:
        return json.load(f)


def reparent_children_to_parent_and_delete_self(target):
    print 'delete', target
    parent = target.getParent()
    for child in target.getChildren():
        pm.parent(child, parent)
    pm.delete(target)


def delete_unused_joints(grandpa, target, namespace, rules):
    for child in target.getChildren():
        if not isinstance(child, pm.nodetypes.Joint):
            delete_unused_joints(target, child, namespace, rules)
            continue

        # get name without dag path and namespace
        child_name = child.nodeName().split(':')[-1]
        rule = rules.get(child_name, {})
        alignment = rule.get('alignment', None)
        alignment = '%s:%s' % (namespace, alignment)

        if not rule:
            # delete joint without mapping rule
            reparent_children_to_parent_and_delete_self(child)
            delete_unused_joints(grandpa, target, namespace, rules)
            break
        elif alignment is not None and not pm.ls(alignment):
            # delete joint whose alignment node does not exist
            reparent_children_to_parent_and_delete_self(child)
            delete_unused_joints(grandpa, target, namespace, rules)
            break
        else:
            # keep joint, recursive delete unused child joints
            delete_unused_joints(target, child, namespace, rules)


def align_joints(joint_root, rules, target_namespace):
    for joint_ in joint_root.getChildren():
        # get name without dag path and namespace
        node_name = joint_.nodeName().split(':')[-1]
        rule = rules.get(node_name, None)
        if rule:
            alignment_name = rule['alignment']
            alignment_name = '%s:%s' % (target_namespace, alignment_name)
            alignment_node = pm.PyNode(alignment_name)

            # set rotate order
            joint_.rotateOrder.set(alignment_node.rotateOrder.get())

            # align position and rotation by parent constraint
            pm.parentConstraint(alignment_node, joint_)
            pm.parentConstraint(alignment_node, joint_, e=True, rm=True)

            # freeze rotate
            pm.makeIdentity(joint_, apply=True, translate=True, rotate=True,
                            scale=True)

        align_joints(joint_, rules, target_namespace)


def add_namespace(namespace, root):
    u"""Add namespace to root and root's children recursively.
    """
    old_namespace = root.namespace()[:-1]

    if not pm.namespace(exists=':%s' % namespace):
        if pm.ls(namespace):
            # if node named namespace exists, return False
            return False
        pm.namespace(add=namespace)
    for node in pm.ls(root, dag=1):
        new_name = ':%s:%s' % (namespace, node.nodeName())
        node.rename(new_name)

    pm.namespace(set=':')
    if old_namespace and pm.namespace(exists=':%s' % old_namespace):
        try:
            pm.namespace(rm=old_namespace)
        except Exception as e:
            print e
    return True


def bind_skin(target, asset_name):
    u"""
    ref: C:\Program Files\Autodesk\Maya2012\scripts\others\performSkinCluster.mel
    newSkinCluster "-toSelectedBones -normalizeWeights 1 -mi 5 -dr 10 -rui false,multipleBindPose,1";
    """
    print target, asset_name
    # select meshes and nurbses
    geos = []
    meshes = pm.ls(target, dag=True, type='mesh', l=True, visible=True)
    for geo in meshes:
        if not pm.listConnections(geo, type="shadingEngine"):
            continue
        try:
            dup = pm.duplicate(geo, rr=True)[0]
        except Exception as e:
            print e
            continue
        for c in dup.getChildren():
            if c.intermediateObject.get() is True:
                pm.delete(c)
        for attr_name in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
            dup.attr(attr_name).unlock()
        pm.parent(dup, w=True)
        geos.append(dup)

    nurbses = pm.ls(
        target, dag=True, type='nurbsSurface', l=True, visible=True)
    for geo in nurbses:
        if not pm.listConnections(geo, type="shadingEngine"):
            continue
        dup = pm.nurbsToPoly(
            geo,
            name=geo.stripNamespace() + '_poly',
            matchNormalDir=True,
            constructionHistory=True,
            format=1,  # Standard Fit
            polygonType=1,  # Quads
            polygonCount=200,
            chordHeightRatio=0.9,
            fractionalTolerance=0.01,
            minEdgeLength=0.001,
            delta=0.1,
            uType=1,
            uNumber=3,
            vType=1,
            vNumber=3,
            useChordHeight=False,
            useChordHeightRatio=False,
            chordHeight=0.2,
            edgeSwap=False,
            normalizeTrimmedUVRange=False,
            matchRenderTessellation=False,
            useSurfaceShader=True)[0]
        dup = pm.PyNode(dup)
        geos.append(dup)

    # no meshs or nurbses, return
    if not geos:
        print 'no mesh'
        return

    # merge geos
    geo_tmp = pm.group(geos, name='geo_tmp', world=True)
    merged_geo = pm.polyUnite(geo_tmp,
                              name='%s_Body_Mocap' % asset_name,
                              constructionHistory=False,
                              mergeUVSets=False)[0]
    try:
        pm.delete(geo_tmp)
    except Exception as e:
        print e
    merged_geo.displayInvisibleFaces.set(0)
    pm.sets(pm.PyNode('initialShadingGroup'), e=True, forceElement=merged_geo)

    grp = pm.group(merged_geo, name='geometry', world=True)
    pm.parent(grp, target)

    # bind
    joints = pm.ls(target, dag=True, type='joint')
    skin_cluster = pm.skinCluster(
        joints + [merged_geo],
        toSelectedBones=True,  # selected joints
        ignoreHierarchy=True,  # closest distance
        skinMethod=0,  # classical linear skinning
        normalizeWeights=2,  # interactive
        maximumInfluences=5,
        obeyMaxInfluences=False,
        dropoffRate=10.0,
        removeUnusedInfluence=False)
    skin_cluster.normalizeWeights.set(1)


def create_skeleton(template_path, mapping_rules, target):
    # import
    print "debug............."
    print template_path
    print mapping_rules
    print target
    nodes = pm.importFile(template_path, returnNewNodes=True)

    # find root of joints
    root = None
    for node in nodes:
        if not isinstance(node, pm.nodetypes.Transform):
            continue
        if node.getParent() is None:
            root = node
            break

    # align
    target_namespace = target.namespace()[:-1]
    delete_unused_joints(
        grandpa=root,
        target=root,
        namespace=target_namespace,
        rules=mapping_rules)

    align_joints(
        joint_root=root,
        rules=mapping_rules,
        target_namespace=target_namespace)

    # bind skin
    asset_file = os.path.split(pm.sceneName())[-1]
    asset_name = os.path.splitext(asset_file)[0]

    try:
        bind_skin(target, asset_name)
    except Exception as e:
        print e

    return root


def export_skeleton(target_root, export_path):
    u"""Export skeleton to fbx.
    """
    pm.select(target_root)

    fbx_plugin = 'fbxmaya'
    if fbx_plugin not in pm.pluginInfo(query=True, listPlugins=True):
        pm.loadPlugin(fbx_plugin)
    pm.mel.eval('FBXProperty Export|IncludeGrp|Animation|Deformation -v true;')
    pm.mel.eval('FBXExportSkins -v true')
    pm.mel.eval('FBXExportShapes -v true')
    pm.mel.eval(
        'FBXProperty Export|AdvOptGrp|UnitsGrp|DynamicScaleConversion -v true;')
    pm.mel.eval('FBXExportUpAxis y')
    pm.mel.eval('FBXExportInAscii -v false')
    pm.mel.eval('FBXExportFileVersion FBX201000')
    pm.mel.eval('FBXExport -f "%s" -s' % export_path)

#=========================================================================
# Functions to Link Character to T-Pose
#=========================================================================


def connect_skeleton_to_rig(joints, mapping_rules, target_namespace):
    mapping_functions = [f for f in getmembers(mapping) if isfunction(f[1])]

    # remove target reference edits
    for ref in pm.listReferences():
        if ref.namespace == target_namespace:
            ref.clean()

    all_temp_nodes = []
    all_controllers = []
    # link joints
    for joint in joints:
        name = joint.stripNamespace()
        rule = mapping_rules.get(name, None)
        if not rule:
            continue

        for mapping_name, mapping_targets in rule.items():
            if mapping_name == 'alignment':
                continue

            mapping_function = [f[1]
                                for f in mapping_functions if f[0] == mapping_name][0]

            for mapping_kwargs in mapping_targets:
                controller_name = mapping_kwargs.pop('controller')
                controller_name = '%s:%s' % (target_namespace, controller_name)
                if not pm.ls(controller_name):
                    raise Exception('%s does not exist!!!' % controller_name)
                controller = pm.PyNode(controller_name)
                mapping_kwargs = dict([(str(m[0]), m[1])
                                       for m in mapping_kwargs.items()])
                temp_nodes = mapping_function(
                    joint, controller, **mapping_kwargs)

                all_controllers = all_controllers + [controller]
                all_temp_nodes = all_temp_nodes + temp_nodes

    return all_temp_nodes, all_controllers


def connect_mocap_to_skeleton(from_namespace, to_namespace):
    attrs = ['translateX', 'translateY', 'translateZ',
             'rotateX', 'rotateY', 'rotateZ']
    source_joints = pm.ls('%s:*' % from_namespace, type='joint')
    source_joints = sorted(
        source_joints, key=lambda n: len(n.longName().split('|')))
    for source_joint in source_joints:
        joint_name = source_joint.stripNamespace()
        try:
            target_joint = pm.PyNode('%s:%s' % (to_namespace, joint_name))
        except Exception as e:
            print e
            continue

        for name in attrs:
            if not source_joint.hasAttr(name):
                continue
            source_joint.attr(name).connect(target_joint.attr(name))

    # force evaluate all ndoes
    ct = pm.currentTime(q=True)
    pm.currentTime(ct + 1)
    pm.currentTime(ct)


def get_min_max_keyframes(target_namespace, attrs):
    min_frame = 10000
    max_frame = 0
    for source_joint in pm.ls('%s:*' % target_namespace, type='joint'):
        joint_name = source_joint.stripNamespace()
        for name in attrs:
            if not source_joint.hasAttr(name):
                continue
            for source_input in source_joint.attr(name).inputs():
                if not isinstance(source_input, pm.nodetypes.AnimCurve):
                    continue
                key_count = pm.keyframe(source_input, q=True, kc=True)
                key_frames = pm.keyframe(
                    source_input, q=True, index=[0, key_count - 1], tc=True)
                if key_frames[0] < min_frame:
                    min_frame = key_frames[0]
                if key_frames[-1] > max_frame:
                    max_frame = key_frames[-1]
    return min_frame, max_frame


def set_playback_range_to_fit_keyframes(target_namespace):
    target_attrs = ['translateX', 'translateY', 'translateZ',
                    'rotateX', 'rotateY', 'rotateZ']
    start_frame, end_frame = get_min_max_keyframes(
        target_namespace, target_attrs)
    pm.playbackOptions(minTime=start_frame)
    pm.playbackOptions(maxTime=end_frame)


def shift_keyframes(node, from_frame, to_frame, attr_names):
    shift_frames = to_frame - from_frame
    for attr_name in attr_names:
        if not node.hasAttr(attr_name):
            continue
        for input_ in node.attr(attr_name).inputs():
            if not isinstance(input_, pm.nodetypes.AnimCurve):
                continue
            key_count = pm.keyframe(input_, q=True, kc=True)
            key_frames = pm.keyframe(
                input_, q=True, index=[0, key_count - 1], tc=True)
            if key_frames[0] == to_frame:
                continue
            pm.keyframe(
                input_, e=True,
                includeUpperBound=True,
                relative=True,
                option='over',
                timeChange=shift_frames,
                valueChange=0)


def shift_keyframes_for_animated_nodes(namespace, from_frame, to_frame, mapping_rules):
    # get controller_names
    controller_names = []
    for joint_name, joint_mapping_rule in mapping_rules.items():
        for mapping_method, mapping_targets in joint_mapping_rule.items():
            if mapping_method == 'alignment':
                continue
            for mapping_target in mapping_targets:
                controller = mapping_target['controller']
                controller_names.append(controller)

    for controller_name in controller_names:
        controller = pm.PyNode('%s:%s' % (namespace, controller_name))
        shift_keyframes(controller, from_frame, to_frame,
                        ['translateX', 'translateY', 'translateZ',
                         'rotateX', 'rotateY', 'rotateZ'])


def bake_animation(controllers, constraints):
    u"""Bake animation from start to end of playback range.
    """
    start_frame = pm.playbackOptions(q=True, minTime=True)
    end_frame = pm.playbackOptions(q=True, maxTime=True)
    pm.bakeResults(
        controllers,
        simulation=True,
        time=(start_frame, end_frame),
        sampleBy=1,
        disableImplicitControl=True,  # ?
        preserveOutsideKeys=True,  # ?
        sparseAnimCurveBake=False,  # ?
        removeBakedAttributeFromLayer=False,  # ?
        bakeOnOverrideLayer=False,  # ?
        controlPoints=False,  # ?
        shape=True  # ?
    )

    # delete constraints after bake animation
    pm.delete(constraints)


def get_asset_name_from_namespace(namespace):
    u"""Parse namespace to get asset name.
    """
    for r in pm.listReferences():
        if r.namespace == namespace:
            file_name = os.path.split(r.path)[-1]
            asset_name, ext = os.path.splitext(file_name)
            return asset_name
    return None


def pre_import(project_name, template_name, target_namespace):
    if not hasattr(hooks, project_name):
        return
    if not hasattr(hooks.__dict__[project_name], 'pre_import'):
        return

    hooks.__dict__[project_name].pre_import(target_namespace, template_name)


def post_import(project_name, template_name, target_namespace, mocap_namespace):
    if not hasattr(hooks, project_name):
        return
    if not hasattr(hooks.__dict__[project_name], 'post_import'):
        return

    hooks.__dict__[project_name].post_import(
        target_namespace, mocap_namespace, template_name)


def get_default_skeleton_path(project_name, target_namespace):
    # get path from hook
    if not hasattr(hooks, project_name):
        return None
    if not hasattr(hooks.__dict__[project_name], 'get_default_skeleton_path'):
        return None

    return hooks.__dict__[project_name].get_default_skeleton_path(target_namespace)


def remove_reference(namespace):
    for ref in pm.listReferences():
        if ref.namespace == namespace.split(':')[0]:
            ref.remove()


def create_skeleton_reference(target_namespace, skeleton_path):
    # create reference
    skeleton_namespace = '%s_skeleton' % target_namespace
    remove_reference(skeleton_namespace)
    pm.loadPlugin('fbxmaya')
    skeleton_nodes = pm.createReference(skeleton_path,
                                        namespace=skeleton_namespace,
                                        returnNewNodes=True)
    # get skeleton joints sorted from root to leaf
    skeleton_joints = [
        n for n in skeleton_nodes if isinstance(n, pm.nodetypes.Joint)]
    skeleton_joints = sorted(
        skeleton_joints, key=lambda n: len(n.fullPath().split('|')))
    # update skeleton namespace
    skeleton_namespace = skeleton_joints[0].namespace()[:-1]
    return skeleton_namespace, skeleton_joints


def create_mocap_reference(target_namespace, mocap_path):
    # create reference
    mocap_namespace = '%s_mocap' % target_namespace
    remove_reference(mocap_namespace)
    mocap_nodes = pm.createReference(mocap_path,
                                     namespace=mocap_namespace,
                                     returnNewNodes=True)
    # get mocap joints
    mocap_joints = [
        n for n in mocap_nodes if isinstance(n, pm.nodetypes.Joint)]
    # update mocap namespace
    mocap_namespace = mocap_joints[0].namespace()[:-1]
    return mocap_namespace, mocap_joints


def import_animation(target, skeleton_path, mocap_path,
                     project_name, template_name, mapping_rules):
    # pre import
    target_namespace = target.namespace()[:-1]
    pre_import(project_name, template_name, target_namespace)

    # reference skeleton
    skeleton_namespace, skeleton_joints = create_skeleton_reference(
        target_namespace, skeleton_path)

    # reference mocap
    mocap_namespace, _ = create_mocap_reference(target_namespace, mocap_path)

    # connect skeleton to rig
    constraints, controllers = connect_skeleton_to_rig(
        skeleton_joints, mapping_rules, target_namespace)

    # connect mocap to skeleton
    connect_mocap_to_skeleton(mocap_namespace, skeleton_namespace)

    # set frame range
    set_playback_range_to_fit_keyframes(mocap_namespace)

    # bake animation
    bake_animation(controllers, constraints)

    # remove skeleton reference
    remove_reference(skeleton_namespace)

    # post import
    post_import(
        project_name, template_name, target_namespace, mocap_namespace)

    return mocap_namespace

