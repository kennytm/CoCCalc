#!/usr/bin/env python3

# To compile:
#
# 1. Copy the 'Documented/updated' and '*.app/res' folder to here.
# 2. ./csv2json.py updated res > info.js

import csv
import json
import os
import os.path
import sys
import itertools
import collections

def parse_texts_csv(filename):
    result = {}
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        next(reader)
        for row in reader:
            result[row['TID']] = row['EN']
    return result

def parse_buildings_csv(filename):
    result = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        next(reader)
        for row in reader:
            if row['TID']:
                info = {
                    'BuildingClass': row['BuildingClass'],
                    'AttackSpeed': int(row['AttackSpeed'] or 0),
                    'AirTargets': row['AirTargets'] == 'true' or row['AltAirTargets'] == 'true',
                    'GroundTargets': row['GroundTargets'] == 'true' or row['AltGroundTargets'] == 'true',
                    'IsSplashDamage': row['DamageRadius'] != '',
                    'Levels': []
                }
                result.append((row['TID'], info))
            else:
                info = result[-1][1]
            info['Levels'].append({
                'Hitpoints': int(row['Hitpoints']),
                'Damage': int(row['Damage'] or 0)
            })
    return result

def parse_characters_csv(filename):
    result = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        next(reader)
        for row in reader:
            if row['TID']:
                info = {
                    'HousingSpace': int(row['HousingSpace']),
                    'TrainingTime': int(row['TrainingTime']),
                    'AttackSpeed': int(row['AttackSpeed']),
                    'PreferedTargetDamageMod': int(row['PreferedTargetDamageMod']),
                    'IsFlying': row['IsFlying'] == 'true',
                    'AirTargets': row['AirTargets'] == 'true',
                    'GroundTargets': row['GroundTargets'] == 'true',
                    'PreferedTargetBuilding': row['PreferedTargetBuilding'] or None,
                    'IsSplashDamage': row['DamageRadius'] != '',
                    'AttackCount': int(row['AttackCount'] or -1),
                    'Levels': []
                }
                result.append((row['TID'], info))
            else:
                info = result[-1][1]
            info['Levels'].append({
                'Hitpoints': int(row['Hitpoints']),
                'TrainingCost': int(row['TrainingCost']),
                'Damage': int(row['Damage'])
            })
    return result

def parse_traps_csv(filename):
    result = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        next(reader)
        for row in reader:
            tid = row['TID']
            if any(tid == x[0] for x in result):   # We ignore Slowbomb.
                continue
            result.append((tid, {
                'AirTargets': row['AirTrigger'] == 'true',
                'GroundTargets': row['GroundTrigger'] == 'true',
                'IsSplashDamage': True,
                'Levels': [{'Damage': int(row['Damage'])}]
            }))
    return result

def parse_heroes_csv(filename):
    result = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        next(reader)
        for row in reader:
            if row['TID']:
                info = {
                    'HousingSpace': int(row['HousingSpace']),
                    'TrainingTime': 0,
                    'AttackSpeed': int(row['AttackSpeed']),
                    'PreferedTargetDamageMod': int(row['PreferedTargetDamageMod']),
                    'IsFlying': row['IsFlying'] == 'true',
                    'AirTargets': row['AirTargets'] == 'true',
                    'GroundTargets': row['GroundTargets'] == 'true',
                    'PreferedTargetBuilding': row['PreferedTargetBuilding'] or None,
                    'IsSplashDamage': row['DamageRadius'] != '',
                    'AttackCount': int(row['AttackCount'] or -1),
                    'Levels': []
                }
                result.append((row['TID'], info))
            else:
                info = result[-1][1]
            info['Levels'].append({
                'Hitpoints': int(row['Hitpoints']),
                'TrainingCost': 0,
                'Damage': int(row['Damage'])
            })
    return result


parsers = {
    'texts': parse_texts_csv,
    'buildings': parse_buildings_csv,
    'characters': parse_characters_csv,
    'traps': parse_traps_csv,
    'heroes': parse_heroes_csv,
}


def parse_all(folders):
    result = {}
    for folder in folders:
        csv_folder = os.path.join(folder, 'csv')
        for filename in os.listdir(csv_folder):
            (fn, ext) = os.path.splitext(filename)
            if ext != '.csv':
                continue
            if fn in result:
                continue
            if fn not in parsers:
                continue
            result[fn] = parsers[fn](os.path.join(csv_folder, filename))
    return result


if __name__ == '__main__':
    result = parse_all(sys.argv[1:])
    json_text = json.dumps(result, ensure_ascii=False, separators=(',', ':'))
    print('set_info(', json_text, ');', sep='')

# csv2json.py --- Convert CoC CSVs to JSON format for CoCCalc.
# Copyright (C) 2013  kennytm
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

