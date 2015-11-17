# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject
from yumex.misc import CONFIG


class SearchBar(GObject.GObject):
    """Handling the search UI."""

    __gsignals__ = {'search': (GObject.SignalFlags.RUN_FIRST,
                                    None,
                                    (GObject.TYPE_STRING,
                                     GObject.TYPE_STRING,
                                     GObject.TYPE_PYOBJECT,))
                    }

    FIELDS = ['name', 'summary', 'description']
    TYPES = ['prefix', 'keyword', 'fields']

    def __init__(self, win):
        GObject.GObject.__init__(self)
        self.win = win
        self.search_type = 'prefix'
        self.search_fields = ['name', 'summary']
        self.active = False
        # widgets
        self._bar = self.win.get_ui('search_bar')
        # Searchbar togglebutton
        self._toggle = self.win.get_ui('sch_togglebutton')
        self._toggle.connect('toggled', self.on_toggle)
        # Search Entry
        self._entry = self.win.get_ui('search_entry')
        self._entry.connect('activate', self.on_entry_activate)
        self._entry.connect('icon-press', self.on_entry_icon)
        # Search Options
        self._options = self.win.get_ui('search-options')
        self._options_button = self.win.get_ui('sch_options_button')
        self._options_button.connect('clicked', self.on_options_button)
        # Search Spinner
        self._spinner = self.win.get_ui('search_spinner')
        self._spinner.stop()
        # setup field checkboxes
        for key in SearchBar.FIELDS:
            wid = self.win.get_ui('sch_fld_%s' % key)
            if key in self.search_fields:
                wid.set_active(True)
            wid.connect('toggled', self.on_fields_changed, key)
        self._set_fields_sensitive(False)
        # setup search type radiobuttons
        for key in SearchBar.TYPES:
            wid = self.win.get_ui('sch_opt_%s' % key)
            if key == self.search_type:
                wid.set_active(True)
            wid.connect('toggled', self.on_type_changed, key)
        # setup search option popover
        self.opt_popover = Gtk.Popover.new(self._options_button)
        self.opt_popover.set_size_request(50, 100)
        opt_grid = self.win.get_ui('sch_opt_grid')
        self.opt_popover.add(opt_grid)

    def show_spinner(self, state=True):
        """Set is spinner in searchbar is running."""
        if state:
            self._spinner.start()
        else:
            self._spinner.stop()

    def toggle(self):
        self._toggle.set_active(not self._toggle.get_active())

    def _set_fields_sensitive(self, state=True):
        """Set sensitivity of field checkboxes."""
        for key in SearchBar.FIELDS:
            wid = self.win.get_ui('sch_fld_%s' % key)
            wid.set_sensitive(state)

    def _get_active_field(self):
        """Get the active search fields, based on checkbox states."""
        active = []
        for key in SearchBar.FIELDS:
            wid = self.win.get_ui('sch_fld_%s' % key)
            if wid.get_active():
                active.append(key)
        return active

    def _set_focus(self):
        """Set focus on search entry and move cursor to end of text."""
        self._entry.grab_focus()
        self._entry.emit(
            'move-cursor', Gtk.MovementStep.BUFFER_ENDS, 1, False)

    def on_options_button(self, widget):
        """Search Option button is toggled."""
        if self.opt_popover.get_visible():
            self.opt_popover.hide()
            self._set_focus()
        else:
            self.opt_popover.show_all()

    def on_toggle(self, widget=None):
        """Search Toggle button is toggled."""
        self._bar.set_search_mode(not self._bar.get_search_mode())
        if self._bar.get_search_mode():
            self._set_focus()
        self.active = self._bar.get_search_mode()

    def on_type_changed(self, widget, key):
        """Search type is changed."""
        if widget.get_active():
            self.search_type = key
            if self.search_type == 'fields':
                self._set_fields_sensitive(True)
            else:
                self._set_fields_sensitive(False)

    def on_fields_changed(self, widget, key):
        """Search fields is changed."""
        self.search_fields = self._get_active_field()

    def on_entry_activate(self, widget):
        """Seach entry is activated"""
        # make sure search option is hidden
        self.signal()

    def on_entry_icon(self, widget, icon_pos, event):
        """Search icon press callback."""
        # clear icon pressed
        if icon_pos == Gtk.EntryIconPosition.SECONDARY:
            self._entry.set_text('')
            self._entry.emit('activate')

    def signal(self):
        """Emit a seach signal with key, search type & fields."""
        txt = self._entry.get_text()
        if self.search_type == 'fields':
            self.emit('search', txt, self.search_type, self.search_fields)
        else:
            self.emit('search', txt, self.search_type, [])

    def reset(self):
        self._entry.set_text('')

    def hide(self):
        if self.active:
            self._bar.set_search_mode(False)

    def show(self):
        if self.active:
            self._bar.set_search_mode(True)
            self._set_focus()


class Options(GObject.GObject):
    """Handling the mainmenu options"""

    __gsignals__ = {'option-changed': (GObject.SignalFlags.RUN_FIRST,
                                       None,
                                       (GObject.TYPE_STRING,
                                        GObject.TYPE_BOOLEAN,)
                                       )}

    OPTIONS = ['newest_only', 'clean_unused', 'clean_instonly']

    def __init__(self, win):
        GObject.GObject.__init__(self)
        self.win = win
        for key in Options.OPTIONS:
            wid = self.win.get_ui('option_%s' % key)
            wid.set_active(getattr(CONFIG.session, key))
            wid.connect('toggled', self.on_toggled, key)

    def on_toggled(self, widget, flt):
        """An option is changed."""
        self.emit('option-changed', flt, widget.get_active())


class Filters(GObject.GObject):
    """Handling the package filter UI."""

    __gsignals__ = {'filter-changed': (GObject.SignalFlags.RUN_FIRST,
                                       None,
                                       (GObject.TYPE_STRING,)
                                       )}

    FILTERS = ['updates', 'installed', 'available', 'all']

    def __init__(self, win):
        GObject.GObject.__init__(self)
        self.win = win
        self.current = 'updates'
        for flt in Filters.FILTERS:
            wid = self.win.get_ui('flt_%s' % flt)
            wid.connect('toggled', self.on_toggled, flt)

    def on_toggled(self, widget, flt):
        """Active filter is changed."""
        if widget.get_active():
            self.current = flt
            self.emit('filter-changed', flt)

    def set_active(self, flt):
        """Set the active filter."""
        if flt in Filters.FILTERS:
            wid = self.win.get_ui('flt_%s' % flt)
            if not wid.get_active():
                wid.set_active(True)
            else:
                self.current = flt
                self.emit('filter-changed', flt)
        else:
            print('unknown filter : ', flt)


class Content(GObject.GObject):
    """Handling the content pages"""

    __gsignals__ = {'page-changed': (GObject.SignalFlags.RUN_FIRST,
                                       None,
                                       (GObject.TYPE_STRING,)
                                       )}

    MENUS = ['packages', 'groups', 'history', 'actions']

    def __init__(self, win):
        GObject.GObject.__init__(self)
        self.win = win
        self._stack = self.win.get_ui('main_stack')
        self.switcher = self.win.get_ui('main_switcher')
        # catch changes in active page in stack
        self._stack.connect('notify::visible-child', self.on_switch)
        for key in Content.MENUS:
            wid = self.win.get_ui('main_%s' % key)
            wid.connect('activate', self.on_menu_select, key)

    def select_page(self, page):
        """Set the active page."""
        self._stack.set_visible_child_name(page)

    def on_menu_select(self, widget, page):
        """Main menu page entry is seleceted"""
        self.select_page(page)

    def on_switch(self, widget, data):
        """The active page is changed."""
        child = self._stack.get_visible_child_name()
        self.emit('page-changed', child)
