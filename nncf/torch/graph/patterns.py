"""
 Copyright (c) 2019-2020 Intel Corporation
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
      http://www.apache.org/licenses/LICENSE-2.0
 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

from nncf.common.graph.patterns import GraphPattern
from nncf.common.graph.patterns import create_graph_pattern_from_pattern_view
import networkx as nx

class PatternFactory:
    def __init__(self):
        self.graph_full_pattern = None
        self.pattern_views = None

    def get_full_pattern_graph(self, pattern_graph_path=None):
        if self.graph_full_pattern is not None:
            return self.graph_full_pattern
        path = '/home/aleksei/tmp/pattern.dot'
        self.graph_full_pattern = get_full_pattern_graph(path)
        return self.graph_full_pattern


def get_full_pattern_graph(dot_file_path):
    pattern_graph = nx.drawing.nx_agraph.read_dot(dot_file_path)
    GP = GraphPattern()
    GP.graph = pattern_graph

    return GP


PATTERN_FACTORY = PatternFactory()
