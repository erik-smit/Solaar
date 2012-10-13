#
#
#

from gi.repository import (Gtk, Gdk)

from logitech.devices import constants as C


_DEVICE_ICON_SIZE = Gtk.IconSize.DIALOG
_STATUS_ICON_SIZE = Gtk.IconSize.DND
_PLACEHOLDER = '~'


def _find_children(container, *child_names):
	def _iterate_children(widget, names, result, count):
		wname = widget.get_name()
		if wname in names:
			index = names.index(wname)
			names[index] = None
			result[index] = widget
			count -= 1

		if count > 0 and isinstance(widget, Gtk.Container):
			for w in widget:
				count = _iterate_children(w, names, result, count)
				if count == 0:
					break

		return count

	names = list(child_names)
	count = len(names)
	result = [None] * count
	_iterate_children(container, names, result, count)
	return result if count > 1 else result[0]


def _update_receiver_box(box, rstatus):
	label, buttons_box = _find_children(box, 'label', 'buttons')
	label.set_text(rstatus.text or '')
	buttons_box.set_visible(rstatus.code >= C.STATUS.CONNECTED)


def _update_device_box(frame, devstatus):
	if devstatus is None:
		frame.set_visible(False)
		frame.set_name(_PLACEHOLDER)
		return

	icon, label = _find_children(frame, 'icon', 'label')

	frame.set_visible(True)
	if frame.get_name() != devstatus.name:
		frame.set_name(devstatus.name)
		icon.set_from_icon_name(devstatus.name, _DEVICE_ICON_SIZE)
		icon.set_tooltip_text(devstatus.name)
		label.set_markup('<b>' + devstatus.name + '</b>')

	status = _find_children(frame, 'status')
	if devstatus.code < C.STATUS.CONNECTED:
		icon.set_sensitive(False)
		label.set_sensitive(False)
		status.set_visible(False)
		return

	icon.set_sensitive(True)
	label.set_sensitive(True)
	status.set_visible(True)
	status_icons = status.get_children()

	battery_icon, battery_label = status_icons[0:2]
	battery_level = getattr(devstatus, C.PROPS.BATTERY_LEVEL, None)
	if battery_level is None:
		battery_icon.set_sensitive(False)
		battery_icon.set_from_icon_name('battery_unknown', _STATUS_ICON_SIZE)
		battery_label.set_sensitive(False)
		battery_label.set_text('')
	else:
		battery_icon.set_sensitive(True)
		icon_name = 'battery_%02d' % (20 * ((battery_level + 10) // 20))
		battery_icon.set_from_icon_name(icon_name, _STATUS_ICON_SIZE)
		battery_label.set_sensitive(True)
		battery_label.set_text('%d%%' % battery_level)

	battery_status = getattr(devstatus, C.PROPS.BATTERY_STATUS, None)
	if battery_status is None:
		battery_icon.set_tooltip_text('')
	else:
		battery_icon.set_tooltip_text(battery_status)

	light_icon, light_label = status_icons[2:4]
	light_level = getattr(devstatus, C.PROPS.LIGHT_LEVEL, None)
	if light_level is None:
		light_icon.set_visible(False)
		light_label.set_visible(False)
	else:
		light_icon.set_visible(True)
		icon_name = 'light_%02d' % (20 * ((light_level + 50) // 100))
		light_icon.set_from_icon_name(icon_name, _STATUS_ICON_SIZE)
		light_label.set_visible(True)
		light_label.set_text('%d lux' % light_level)


def update(window, rstatus, devices, icon_name=None):
	if window and window.get_child():
		if icon_name is not None:
			window.set_icon_name(icon_name)

		vbox = window.get_child()
		controls = list(vbox.get_children())
		_update_receiver_box(controls[0], rstatus)
		for index in range(1, len(controls)):
			_update_device_box(controls[index], devices.get(index))


def _device_box(name=None, has_status_icons=True, has_frame=True):
	box = Gtk.HBox(homogeneous=False, spacing=10)
	box.set_border_width(4)

	icon = Gtk.Image()
	if name:
		icon.set_from_icon_name(name, _DEVICE_ICON_SIZE)
		icon.set_tooltip_text(name)
	else:
		icon.set_from_icon_name('dialog-question', _DEVICE_ICON_SIZE)
	icon.set_alignment(0.5, 0)
	icon.set_name('icon')
	box.pack_start(icon, False, False, 0)

	vbox = Gtk.VBox(homogeneous=False, spacing=8)
	box.pack_start(vbox, True, True, 0)

	label = Gtk.Label('Initializing...')
	label.set_alignment(0, 0.5)
	label.set_name('label')

	status_box = Gtk.HBox(homogeneous=False, spacing=0)
	status_box.set_name('status')

	if has_status_icons:
		vbox.pack_start(label, True, True, 0)

		battery_icon = Gtk.Image.new_from_icon_name('battery_unknown', _STATUS_ICON_SIZE)
		status_box.pack_start(battery_icon, False, True, 0)
		battery_label = Gtk.Label()
		battery_label.set_width_chars(6)
		battery_label.set_alignment(0, 0.5)
		status_box.pack_start(battery_label, False, True, 0)

		light_icon = Gtk.Image.new_from_icon_name('light_unknown', _STATUS_ICON_SIZE)
		status_box.pack_start(light_icon, False, True, 0)
		light_label = Gtk.Label()
		light_label.set_alignment(0, 0.5)
		light_label.set_width_chars(8)
		status_box.pack_start(light_label, False, True, 0)
	else:
		status_box.pack_start(label, True, True, 0)

		toolbar = Gtk.Toolbar()
		toolbar.set_style(Gtk.ToolbarStyle.ICONS)
		toolbar.set_icon_size(Gtk.IconSize.MENU)
		toolbar.set_name('buttons')
		toolbar.set_show_arrow(False)
		status_box.pack_end(toolbar, False, False, 0)

	vbox.pack_start(status_box, True, True, 0)

	box.show_all()

	if has_frame:
		frame = Gtk.Frame()
		frame.add(box)
		return frame
	else:
		toolbar.set_visible(False)
		return box


def create(title, rstatus, systray=False):
	window = Gtk.Window()
	window.set_title(title)
	window.set_role('status-window')

	vbox = Gtk.VBox(homogeneous=False, spacing=4)
	vbox.set_border_width(4)

	rbox = _device_box(rstatus.name, False, False)
	vbox.add(rbox)
	for i in range(1, 1 + rstatus.max_devices):
		dbox = _device_box()
		vbox.add(dbox)
	vbox.set_visible(True)

	window.add(vbox)

	geometry = Gdk.Geometry()
	geometry.min_width = 260
	geometry.min_height = 40
	window.set_geometry_hints(vbox, geometry, Gdk.WindowHints.MIN_SIZE)
	window.set_resizable(False)

	if systray:
		def _state_event(window, event):
			if event.new_window_state & Gdk.WindowState.ICONIFIED:
				# position = window.get_position()
				window.hide()
				window.deiconify()
				# window.move(*position)
				return True

		window.set_keep_above(True)
		# window.set_deletable(False)
		# window.set_decorated(False)
		window.set_position(Gtk.WindowPosition.MOUSE)
		# window.set_type_hint(Gdk.WindowTypeHint.MENU)
		window.set_skip_taskbar_hint(True)
		window.set_skip_pager_hint(True)

		window.connect('window-state-event', _state_event)
		window.connect('delete-event', lambda w, e: toggle(None, window) or True)
	else:
		window.set_position(Gtk.WindowPosition.CENTER)
		window.connect('delete-event', Gtk.main_quit)

	return window


def toggle(_, window):
	if window.get_visible():
		# position = window.get_position()
		window.hide()
		# window.move(*position)
	else:
		window.present()
