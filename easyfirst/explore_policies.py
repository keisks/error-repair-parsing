## Copyright 2013 Yoav Goldberg
##
##    This is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This code is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this code.  If not, see <http://www.gnu.org/licenses/>.

import random
class ExplorePolicy:
   def __init__(self, first_iter, rate):
      self.first_iter = first_iter
      self.rate = rate
   def should_explore(self, iter):
      return iter >= self.first_iter and random.random() < self.rate

exploration_policies = {
      'none' : ExplorePolicy(0,0),
      'coling2012' : ExplorePolicy(2,0.9),
      'always' : ExplorePolicy(0,1),
}


