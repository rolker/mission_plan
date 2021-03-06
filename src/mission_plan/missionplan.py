#!/usr/bin/env python

# A script to generate an example mission file.

import geographic_msgs.msg as geo
import json
import yaml
from collections import OrderedDict
import copy

import marine_msgs.msg as mp

# To Do:
# Sort out how to force printing of parameters and behaviors before navigation.

class Mission:
    ''' A class to define and write a mission plan template for field robots.

    Mission plans for field robots answer the general questions,
    "Where am I to go?" and "What am I to do?". The mission class implements these with
    "navigation" instructions and "behaviors", respectively (also classes defined here).

    Mission plans are composed of two sections: "default_parameters" and
    "navigation".

    "default_parameters" allow an initial (default) configuratioon of a
     robot to be specified. This default configuration also includes behaviors that
    become active immediately on mission activation.

    "navigation" provides for a sequential list of navigation paths, where each path
    specifies one or more locations (waypoints), and possibly orientation in space 
    (and possibly time). Embedded in navigation paths can be new parameters and 
    behaviors that become active when the objective is undertaken.
    '''

    def __init__(self,mission_name="mission"):
        '''Create containers for a basic, default mission plan.'''
        self.mission_name = mission_name
        self.plan = {
        'DEFAULT_PARAMETERS':{'behaviors':{}},
        'NAVIGATION':[]
        }
        
    def add_default_parameter(self,parameter,value):
        ''' Adds a key-value pair to the default parameters'''
        self.plan['DEFAULT_PARAMETERS'][parameter] = value
            
    def add_default_behavior(self,behavior):
        ''' Adds a behavior (see the behavior class) to the default behavior list.'''
        self.plan['DEFAULT_PARAMETERS']['behaviors'][behavior.name] = {}
        for key in behavior.bhv.keys():
            self.plan['DEFAULT_PARAMETERS']['behaviors'][behavior.name][key] = behavior.bhv[key]
            
    def add_navigation_path(self,nav,idx = None):
        ''' A method to add a new navigation objective in the sequential list'''
        if idx is None:
            idx = len(self.plan['NAVIGATION'])
        self.plan['NAVIGATION'].insert(idx, nav)
        
    def __str__(self):
        '''Provide the mission plan in JSON format.'''
#        return json.dumps(self.plan,sort_keys = True,indent=4)
        return json.dumps(self.plan,indent=4)

    def tofile(self,filename= None):
        if filename is None and self.mission_name is not None:
            filename = self.mission_name + '.txt'
        else:
            filename = 'mission.txt'
            
        with open(filename,'w') as outfile:
            #json.dump(self.plan,outfile, sort_keys=True, indent=4)
            json.dump(self.plan,outfile, indent=4)

    def fromfile(self,filename='mission.txt'):
        with open(filename,'r') as infile:
            self.plan = json.load(infile)
            
    def fromString(self, missionString):
        self.plan = json.loads(missionString)

class Behavior:
    '''A class to define a template for specifying behavior parameters.
    
    Behaviors tell an autonomous field robot what to do in certain conditions. 
    They can be run concurrently. When they are turned on / off can be 
    specified explicitly in a mission file (by time or space) or may be
    set to run continuously (or not at all) with a default configuration.

    Only two behavior parameters are required - "Enabled" and "Active".
    They both take boolean assignments. When Enabled == True, the behavior
    is marked for operation, allowing the robot's state machine to start
    processes and initialize systems as required. However the behavior does
    nothing unless Active == True. Otherwise (e.g. Active==False) the behavior
    can be considered to be in standby.

    Other behavior parameters are specific to each robot and system and
    as such are left to the designers to specify. The add_behavior_parameter()
    method provides a simple way to add these additional key:value pairs.
    ''' 
    def __init__(self,behavior_name = "Behavior01"):
        self.bhv = {}
        self.name = behavior_name
        #self.bhv["name"] = behavior_name
        self.bhv["Enabled"] = True
        self.bhv["Active"] = False

    def add_behavior_parameter(self,parameter,value):
        '''A method to add a new parameter and value to a behavior.'''
        self.bhv[parameter] = value

class GeoNavWaypoint:
    ''' A class to define a human-readable template for points in space and time.

    This class definition utilizes ROS messages as templates from which
    the basic class properites are built. These messages are newly defined
    as part of this associated mission_plan ROS package and are intended
    for human interaction with the robot, and not for internal navigation.

    For example, GeoPoseNavEuler provides a Pose message whose position coordinates
    are specified in Latitude, Longitude and Altitude and whose orientation
    coordinates are specified as pitch, roll and heading (True). (Geo indicates
    geographic coordinates, Pose indicates position and orientation, NavEuler indicates
    not pitch, roll, yaw but rather pitch, roll, heading. (Yaw is measured
    counter clockwise from East, while Heading is measured clockwise from North in
    accordance with PEP XXX. This set of coordinates and conventions provides an
    immediately human-understandable pose.
     '''
    
    def __init__(self):
        #self.pt = yaml.load(str(geo.GeoPose()))
        wpt_template = yaml.load(str(mp.GeoPoseNavEuler()))
        initmsg(wpt_template)
        self.pt = wpt_template


class GeoNavPath:
    ''' A class that implements a container holding a sequential list of navigation
    objectives, along with parameters and behaviors to be implemented when the 
    path is undertaken. Paths maybe labeled with a "pathtype" allowing a programmer
    to define various kinds of paths.'''
    
    def __init__(self):
        self.path = OrderedDict([('name',None),
                                ('pathtype',None),
                                ('parameters',{}),
                                ('behaviors',{}),
                                ('nav',[])])
        #self.path = {"aname":None,"parameters":{},"nav":[],"behaviors":{},"pathtype":None}

    def add_path_behavior(self,behavior):
        self.path["behaviors"][behavior.name] = {}
        for key in behavior.bhv.keys():
                self.path["behaviors"][behavior.name][key] = behavior.bhv[key]
                
    def del_path_behavior(self,behavior_name):
        del self.path["behaviors"][behavior_name]

    def add_path_parameter(self, parameter, value):
        self.path["parameters"][parameter] = value

    def add_navigation(self, nav, idx=None):
        ''' A method to add a new navigation objective in the sequential list'''
        if idx is None:
            idx = len(self.path["nav"])
        self.path["nav"].insert(idx, nav)


def initmsg(msg):
    ''' A utility method to initialize all variables in a nested dictionary to None '''
    ''' Need to suggest to ROS folks that message should not initialize to 0'''
    for k,v in msg.iteritems():
        if isinstance(v, dict):
           initmsg(v)
        else:
            msg[k] = None


if __name__ == '__main__':

    # Create a mission 
    M = Mission('Example_Mission')
    M.add_default_parameter('defaultspeed_ms',2.0)
    M.add_default_parameter('minimumdepth_m', 2.0)
    M.add_default_parameter('maximumdepth_m', 2.0)
    M.add_default_parameter('vessellength_m', 4.0)
    M.add_default_parameter('vesselwidth_m', 1.4)

    # Create a Collision Avoidance Behavior and add it as a default behavior.
    B = Behavior('collision_avoidance')
    B.add_behavior_parameter('minimumdistance_m',2.0)
    B.add_behavior_parameter('maxrange_m',100.0)
    M.add_default_behavior(B)
    

    # Create a path example. Simplify this by copying the initial waypoint and modifying it as necesary.


    path = GeoNavPath()
    path.path['name'] = 'First Three Points'
    wpt = GeoNavWaypoint()
    wpt.pt['position']['latitude'] = 43.0
    wpt.pt['position']['longitude'] = -70.0
    wpt2 = GeoNavWaypoint()
    wpt2.pt["position"]["latitude"] = 42.5
    wpt2.pt["position"]["longitude"] = -70.05
    wpt3 = GeoNavWaypoint()
    wpt3.pt["position"]["latitude"] = 42.5
    wpt3.pt["position"]["longitude"] = -69.95

    # Add the new waypoints to the path.
    path.add_navigation(wpt.pt)
    path.add_navigation(wpt2.pt)
    path.add_navigation(wpt3.pt)
    path.add_path_behavior(B)
    path.path["pathtype"] = "trackline"

    # Add the path to navigation.
    M.add_navigation_path(path.path)

    # Create a second path...
    path = GeoNavPath()
    path.path['name'] = "End"
    wpt = GeoNavWaypoint()
    wpt.pt['position']['latitude'] = 43.0
    wpt.pt['position']['longitude'] = -70.0
    path.add_navigation(wpt.pt)
    
    B = Behavior('collision_avoidance')
    B.add_behavior_parameter('minimumdistance_m',4.0)
    B.add_behavior_parameter('maxrange_m',50.0)
    path.add_path_behavior(B)
    path.path['pathtype'] = 'waypoint'
    M.add_navigation_path(path.path)
    # Print the resulting mission plan to a STDOUT and a file.
    print(M)
    M.tofile()

    # Read it back in.
    MM = Mission("Read From File")
    MM.fromfile('Example_Mission.txt')
    if MM.plan == M.plan:
        print "true"
    #print(MM)




