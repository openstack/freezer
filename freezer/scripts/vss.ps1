# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

param([String]$volume="")

$shadow = get-wmiobject win32_shadowcopy

# get static method
$class=[WMICLASS]"root\cimv2:win32_shadowcopy"

# create a new shadow copy
$s1 = $class.create($volume, "ClientAccessible")

# get shadow ID
$s2 = gwmi Win32_ShadowCopy | ? { $_.ID -eq $s1.ShadowID }

$d  = $s2.DeviceObject + "\"

# create a symlink for the shadow path
cmd /c mklink /d $volume\freezer_shadowcopy "$d"

echo "shadow id:" $s2