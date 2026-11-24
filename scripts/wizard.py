#!/usr/bin/env python3
"""Render a looping wizard animation from GitHub's contribution calendar."""
import json
import math
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont

USER = os.environ.get('GITHUB_USERNAME', 'Matheus-Manhezi')
QUERY = '''query($login: String!) { user(login: $login) { contributionsCollection { contributionCalendar { weeks { contributionDays { contributionCount date } } } } } }'''

def calendar():
    request = urllib.request.Request('https://api.github.com/graphql', data=json.dumps({'query': QUERY, 'variables': {'login': USER}}).encode(), headers={'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'], 'Content-Type': 'application/json', 'User-Agent': 'wizard-contributions'})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get('errors') or not data.get('data', {}).get('user'):
        raise RuntimeError('Unable to read contribution calendar: ' + str(data.get('errors', 'user not found')))
    return data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']

def render(weeks, path):
    width, height = 960, 240
    left, top, cell, gap = 68, 56, 12, 4
    colors = ['#25243c', '#405065', '#587e79', '#75b69b', '#ade6bf']
    cells = []
    for col, week in enumerate(weeks):
        for row, day in enumerate(week['contributionDays']):
            # GitHub orders each week Sunday through Saturday, including partial weeks.
            from datetime import date
            weekday = (date.fromisoformat(day['date']).weekday() + 1) % 7
            count = day['contributionCount']
            level = 0 if count == 0 else 1 if count < 4 else 2 if count < 8 else 3 if count < 16 else 4
            cells.append((col, weekday, count, level))
    active = [(c, r) for c, r, count, _ in cells if count]
    targets = active[::max(1, math.ceil(len(active) / 24))][:24]
    frames = []
    font = ImageFont.load_default()
    steps = max(1, len(targets))
    for frame in range(steps * 4 + 12):
        image = Image.new('RGB', (width, height), '#100f20')
        d = ImageDraw.Draw(image)
        d.rounded_rectangle((2, 2, width-3, height-3), radius=14, outline='#4c3b70', width=2)
        d.text((25, 19), 'THE ARCHMAGE OF COMMITS', font=font, fill='#d8c5ff')
        d.text((25, 221), 'Casting fireball on GitHub contributions', font=font, fill='#a095bc')
        ix = min(frame // 4, steps)
        for col, row, count, level in cells:
            x, y = left + col * (cell + gap), top + row * (cell + gap)
            hit = (col, row) in targets[:ix]
            d.rounded_rectangle((x, y, x+cell, y+cell), radius=2, fill=colors[0 if hit else level])
        if targets:
            target = targets[min(ix, len(targets)-1)]
            tx, ty = left + target[0]*(cell+gap)+6, top + target[1]*(cell+gap)+6
            wx = max(40, min(width-45, tx-65))
        else:
            tx, ty, wx = 120, 100, 55
        wy = 194
        # Pixel-art wizard: hat, face, robe, staff.
        d.polygon([(wx-15,wy-25),(wx,wy-59),(wx+11,wy-25)], fill='#8255bf')
        d.rectangle((wx-19,wy-27,wx+16,wy-23), fill='#b592e8')
        d.rectangle((wx-9,wy-23,wx+8,wy-10), fill='#efc7a8')
        d.rectangle((wx+3,wy-20,wx+5,wy-18), fill='#25182e')
        d.polygon([(wx-12,wy-10),(wx+9,wy-10),(wx+16,wy+16),(wx-18,wy+16)], fill='#65419c')
        d.line((wx+15,wy+14,wx+24,wy-27), fill='#b18c5a', width=3)
        d.ellipse((wx+20,wy-33,wx+28,wy-25), fill='#c89fff')
        if targets and ix < len(targets):
            phase = (frame % 4 + 1) / 4
            fx = int((wx+25)*(1-phase) + tx*phase)
            fy = int((wy-30)*(1-phase) + ty*phase)
            d.ellipse((fx-6,fy-6,fx+6,fy+6), fill='#f15b2a')
            d.ellipse((fx-3,fy-3,fx+3,fy+3), fill='#ffe38a')
        frames.append(image.convert('P', palette=Image.Palette.ADAPTIVE, colors=64))
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=120, loop=0, optimize=True)

if __name__ == '__main__':
    render(calendar(), 'dist/wizard.gif')
