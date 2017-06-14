## Copyright 2013 Yoav Goldberg
##
##    This is is free software: you can redistribute it and/or modify
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

PAD={'lem':'_','dform':'__PAD__','ctag':'__PAD__','form':"__PAD__",'tag':'__PAD__','id':-1,'parent':-1,'pprel':'_'} # unify this location
PADEND={'lem':'_','dform':'__PADE__','ctag':'__PADE__','form':"__PADE__",'tag':'__PADE__','id':-1,'parent':-1, 'pprel':'_'} # unify this location
PADSTART={'lem':'_','dform':'__PADS__','ctag':'__PADS__','form':"__PADS__",'tag':'__PADS__','id':-1,'parent':-1, 'pprel':'_'} # unify this location
PADMID={'lem':'_','dform':'__PADM__','ctag':'__PADM__','form':"__PADM__",'tag':'__PADM__','id':-1,'parent':-1,'pprel':'_'} # unify this location
NOPARENT={'lem':'_','parent':-1,'id':-1,'tag':'NOPARENT','ctag':'NOPARENT','form':'_NOPARENT_','dform':'NOPARENT'}     # unify this location

ROOT={'lem':'_','parent':-1,'prel':'--','id':0,'tag':'ROOT','ctag':'ROOT','form':'_ROOT_','dform':'ROOT'}     # unify this location

### Data / structures #{{{

SHIFT=0
REDUCE_L=1
REDUCE_R=2
STN_CHUNK=3

POP=3
NOP=4


#}}}

