#
# SchoolTool - common information systems platform for school administration
# Copyright (c) 2009 Shuttleworth Foundation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
Upgrade SchoolTool to generation 30.

Remove unused attributes from person schema.
"""
import transaction

from zope.app.generations.utility import findObjectsProviding
from zope.app.publication.zopepublication import ZopePublication

from schooltool.group.interfaces import IGroup
from schooltool.course.interfaces import ICourse
from schooltool.relationship.interfaces import IRelationshipLinks
from schooltool.relationship.relationship import getRelatedObjects
from schooltool.relationship.relationship import relate, unrelate
from schooltool.app.membership import URIMember, URIGroup, URIMembership


def evolve(context):
    root = context.connection.root().get(ZopePublication.root_name, None)

    savepoint_counter = 0

    # Groups are no longer allowed as members of a section.
    groups = findObjectsProviding(root, IGroup)
    for group in groups:
        targets = getRelatedObjects(
            group, URIGroup, rel_type=URIMembership)
        group_members = getRelatedObjects(
            group, URIMember, rel_type=URIMembership)

        for target in targets:
            target_members = getRelatedObjects(
                target, URIMember, rel_type=URIMembership)
            for member in group_members:
                if member not in target_members:
                    relate(URIMembership,
                           (member, URIMember),
                           (target, URIGroup))
                savepoint_counter += 1
            unrelate(URIMembership,
                     (group, URIMember),
                     (target, URIGroup))
        if savepoint_counter % 2000 == 0:
            transaction.savepoint(optimistic=True)

    # Courses gained several new attributes, fill in their course_id
    courses = findObjectsProviding(root, ICourse)
    for course in courses:
        if getattr(course, 'course_id', None) is None:
            course.course_id = course.__name__