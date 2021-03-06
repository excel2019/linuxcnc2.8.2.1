# vim: sts=4 sw=4 et
# GladeVcp Widgets
#
# Copyright (c) 2010  Pavel Shramov <shramov@mexmat.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import gi
gi.require_version("Gtk","3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
import cairo
import math

if __name__ == "__main__":
    from hal_widgets import _HalWidgetBase, hal, hal_pin_changed_signal
else:
    from .hal_widgets import _HalWidgetBase, hal, hal_pin_changed_signal

MAX_INT = 0x7fffffff

def Gdk_color_tuple(c):
    if not c:
        return 0, 0, 0
    return c.red_float, c.green_float, c.blue_float

class HAL_Meter(Gtk.DrawingArea, _HalWidgetBase):
    __gtype_name__ = 'HAL_Meter'
    __gsignals__ = dict([hal_pin_changed_signal])
    __gproperties__ = {
        'invert' : ( GObject.TYPE_BOOLEAN, 'Inverted', 'Invert min-max direction',
                    False, GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT),
        'min' : ( GObject.TYPE_FLOAT, 'Min', 'Minimum value',
                    -MAX_INT, MAX_INT, 0, GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT),
        'max'  : ( GObject.TYPE_FLOAT, 'Max', 'Maximum value',
                    -MAX_INT, MAX_INT, 100, GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT),
        'value' : ( GObject.TYPE_FLOAT, 'Value', 'Current meter value (for glade testing)',
                    -MAX_INT, MAX_INT, 0, GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT),
        'majorscale' : ( GObject.TYPE_FLOAT, 'Major scale', 'Major ticks',
                    -MAX_INT, MAX_INT, 10, GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT),
        'minorscale'  : ( GObject.TYPE_FLOAT, 'Minor scale', 'Minor ticks',
                    -MAX_INT, MAX_INT, 2, GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT),
        'z0_color' : ( Gdk.Color.__gtype__, 'Zone 0 color', "Set color for first zone",
                        GObject.ParamFlags.READWRITE),
        'z1_color' : ( Gdk.Color.__gtype__, 'Zone 1 color', "Set color for second zone",
                        GObject.ParamFlags.READWRITE),
        'z2_color' : ( Gdk.Color.__gtype__, 'Zone 2 color', "Set color for third zone",
                        GObject.ParamFlags.READWRITE),
        'z0_border' : ( GObject.TYPE_FLOAT, 'Zone 0 up limit', 'Up limit of zone 0',
                    -MAX_INT, MAX_INT, MAX_INT, GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT),
        'z1_border' : ( GObject.TYPE_FLOAT, 'Zone 1 up limit', 'Up limit of zone 1',
                    -MAX_INT, MAX_INT, MAX_INT, GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT),
        'bg_color' : ( Gdk.Color.__gtype__, 'Background', "Choose background color",
                        GObject.ParamFlags.READWRITE),
        'force_size' : ( GObject.TYPE_INT, 'Forced size', 'Force meter size not dependent on widget size. -1 to disable',
                    -1, MAX_INT, -1, GObject.ParamFlags.READWRITE | GObject.ParamFlags.CONSTRUCT),
        'text_template' : ( GObject.TYPE_STRING, 'Text template',
                'Text template to display. Python formatting may be used for one variable',
                "%.02f", GObject.ParamFlags.READWRITE|GObject.ParamFlags.CONSTRUCT),
        'label' : ( GObject.TYPE_STRING, 'Meter label', 'Label to display',
                "", GObject.ParamFlags.READWRITE|GObject.ParamFlags.CONSTRUCT),
        'sublabel' : ( GObject.TYPE_STRING, 'Meter sub label', 'Sub text to display',
                "", GObject.ParamFlags.READWRITE|GObject.ParamFlags.CONSTRUCT),
    }
    __gproperties = __gproperties__

    def __init__(self):
        super(HAL_Meter, self).__init__()

        self.bg_color = Gdk.Color.parse('white')[1]
        self.z0_color = Gdk.Color.parse('green')[1]
        self.z1_color = Gdk.Color.parse('yellow')[1]
        self.z2_color = Gdk.Color.parse('red')[1]

        self.force_radius = None

        self.connect("draw", self.expose)

    def _hal_init(self):
        _HalWidgetBase._hal_init(self)
        self.hal_pin = self.hal.newpin(self.hal_name, hal.HAL_FLOAT, hal.HAL_IN)
        self.hal_pin.connect('value-changed', lambda p: self.set_value(p.value))
        self.hal_pin.connect('value-changed', lambda s: self.emit('hal-pin-changed', s))

    def expose(self, widget, event):
        if self.is_sensitive():
            alpha = 1
        else:
            alpha = 0.3

        w = self.get_allocated_width()
        h = self.get_allocated_height()
        r = min(w, h) / 2

        fr = self.force_size

        if fr > 0: r = min(fr, r)

        if r < 20:
            r = 40
            self.set_size_request(2 * r, 2 * r)

        cr = widget.get_property('window').cairo_create()
        def set_color(c):
            return cr.set_source_rgba(c.red_float, c.green_float, c.blue_float, alpha)

        cr.set_line_width(2)
        set_color(Gdk.Color.parse('black')[1])

        #print w, h, aw, ah, fw, fh
        cr.translate(w / 2, h / 2)
        cr.arc(0, 0, r, 0, 2*math.pi)
        cr.clip_preserve()
        cr.stroke()

        r -= 1

        cr.set_line_width(1)
        set_color(self.bg_color)
        cr.arc(0, 0, r, 0, 2*math.pi)
        cr.stroke_preserve()
        cr.fill()

        a_delta = math.pi / 6
        a_start = 0.5 * math.pi + a_delta
        a_size = 2 * math.pi - 2 * a_delta

        def angle(v):
            size = self.max - self.min
            v = max(self.min, v)
            v = min(self.max, v)
            return a_start + a_size * (v - self.min) / size

        set_color(self.z2_color)
        self.draw_zone(cr, r, angle(self.z1_border), angle(self.max))
        set_color(self.z1_color)
        self.draw_zone(cr, r, angle(self.z0_border), angle(self.z1_border))
        set_color(self.z0_color)
        self.draw_zone(cr, r, angle(self.min), angle(self.z0_border))

        set_color(Gdk.Color.parse('black')[1])
        cr.set_font_size(r/10)

        v = self.min
        while v <= self.max:
            if int(v) - v == 0: v = int(v)
            self.draw_tick(cr, r, 0.15 * r, angle(v), text=str(v))
            v += self.majorscale

        v = self.min
        while v <= self.max:
            self.draw_tick(cr, r, 0.05 * r, angle(v))
            v += self.minorscale

        self.text_at(cr, self.sublabel, 0, r/5)

        cr.set_font_size(r/5)
        self.text_at(cr, self.label, 0, -r/5)

        set_color(Gdk.Color.parse('red')[1])
        self.draw_arrow(cr, r, angle(self.value))

        set_color(Gdk.Color.parse('black')[1])
        self.text_at(cr, self.text_template % self.value, 0, 0.8 * r)
        return True

    def draw_zone(self, cr, r, start, stop):
        cr.arc(0, 0, r, start, stop)
        cr.line_to(0.9 * r * math.cos(stop), 0.9 * r * math.sin(stop))
        cr.arc_negative(0, 0, 0.9 * r, stop, start)
        cr.line_to(r * math.cos(start), r * math.sin(start))
        cr.stroke_preserve()
        cr.fill()

    def draw_tick(self, cr, r, sz, a, text=None):
        cr.move_to((r - sz) * math.cos(a), (r - sz) * math.sin(a))
        cr.line_to(r * math.cos(a), r * math.sin(a))
        cr.stroke()
        if not text:
            return
        self.text_at(cr, text, 0.75 * r * math.cos(a), 0.75 * r * math.sin(a))

    def text_at(self, cr, text, x, y, xalign='center', yalign='center'):
        xbearing, ybearing, width, height, xadvance, yadvance = cr.text_extents(text)
        #print xbearing, ybearing, width, height, xadvance, yadvance
        if xalign == 'center':
            x = x - width/2
        elif xalign == 'right':
            x = x - width
        if yalign == 'center':
            y = y + height/2
        elif yalign == 'top':
            y = y + height
        cr.move_to(x, y)
        cr.show_text(text)

    def draw_arrow(self, cr, r, a):
        cr.rotate(a)
        cr.move_to(0, 0)
        cr.line_to(-r/10, r/20)
        cr.line_to(0.8 * r, 0)
        cr.line_to(-r/10, -r/20)
        cr.line_to(0, 0)
        cr.stroke_preserve()
        cr.fill()
        cr.rotate(-a)

    def set_value(self, v):
        self.value = v
        self.queue_draw()

    def do_get_property(self, property):
        name = property.name.replace('-', '_')
        if name in list(self.__gproperties.keys()):
            return getattr(self, name)
        else:
            raise AttributeError('unknown property %s' % property.name)

    def do_set_property(self, property, value):
        name = property.name.replace('-', '_')

        if name == 'text_template':
            try:
                v = value % 0.0
            except Exception as e:
                print("Invalid format string '%s': %s" % (value, e))
                return False
        if name in ['bg_color', 'z0_color', 'z1_color', 'z2_color']:
            if not value:
                return False

        if name in list(self.__gproperties.keys()):
            setattr(self, name, value)
            self.queue_draw()
        else:
            raise AttributeError('unknown property %s' % property.name)

        if name in ['force_size', 'force_size']:
            #print "Forcing size request %s" % name
            self.set_size_request(self.force_size, self.force_size)

        self.queue_draw()
        return True

def main():
    window = Gtk.Window()
    meter = HAL_Meter()
    meter.set_property('value', 123.456)
    window.add(meter)
    window.connect("destroy", Gtk.main_quit)
    window.set_title("HAL_Meter")
    window.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
