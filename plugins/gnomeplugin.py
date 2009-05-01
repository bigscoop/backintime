#    Back In Time
#    Copyright (C) 2008-2009 Oprea Dan
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import os
import pluginmanager
import tools
import logger
import threading
import time


if len( os.getenv( 'DISPLAY', '' ) ) == 0:
	os.putenv( 'DISPLAY', ':0.0' )


class GnomePlugin( pluginmanager.Plugin ):

	class Systray( threading.Thread ):
		def __init__( self, snapshots ):
			import pygtk
			pygtk.require("2.0")
			import gtk
			import gnome

			threading.Thread.__init__( self )
			self.stop_flag = False
			self.snapshots = snapshots
			self.config = self.snapshots.config

			gnome_props = { gnome.PARAM_APP_DATADIR : '/usr/share' }
			gnome.program_init( 'backintime', self.config.VERSION, properties = gnome_props )

		def start( self ):
			self.stop_flag = False
			threading.Thread.start( self )

		def stop( self ):
			self.stop_flag = True
			try:
				self.join()
			except:
				pass

		def show_notification( self, icon ):
			import pynotify
			self.notification.set_timeout( pynotify.EXPIRES_NEVER )
			self.notification.show()

		def run( self ):
			import gtk
			import pynotify

			logger.info( '[GnomePlugin.Systray.run]' )

			gtk.gdk.threads_init()
			display = gtk.gdk.display_get_default()
			
			if display is None:
				logger.info( '[GnomePlugin.Systray.run] display KO' )
				return

			status_icon = None
			try:
				status_icon = gtk.StatusIcon()
			except:
				pass

			if status_icon is None:
				logger.info( '[GnomePlugin.Systray.run] no status_icon' )
				return

			attach_notification = True
			last_message = None
			first_error = self.config.is_notify_enabled()

			status_icon.set_from_stock( gtk.STOCK_SAVE )
			status_icon.set_visible( True )

			pynotify.init( self.config.APP_NAME )
			self.notification = pynotify.Notification( self.config.APP_NAME, '', '' )
			self.notification.set_urgency( pynotify.URGENCY_NORMAL )
			self.notification.set_timeout( pynotify.EXPIRES_NEVER )

			status_icon.connect('activate', self.show_notification )

			logger.info( '[GnomePlugin.Systray.run] begin loop' )

			while True:
				gtk.main_iteration( False )
				if self.stop_flag:
					break

				if not gtk.events_pending():
					if attach_notification:
						attach_notification = False
						self.notification.attach_to_status_icon( status_icon )

					message = self.snapshots.get_take_snapshot_message()
					if message is None and last_message is None:
						message = ( 0, _('Working...') )

					if not message is None:
						if message != last_message:
							last_message = message

							urgency = pynotify.URGENCY_NORMAL
							icon_name = gtk.STOCK_SAVE
							status_icon_blinking = False
							if last_message[0] != 0:
								urgency = pynotify.URGENCY_CRITICAL
								icon_name = 'dialog-error'
								status_icon_blinking = True

							status_icon.set_blinking( status_icon_blinking )
							status_icon.set_tooltip( last_message[1] )

							self.notification.update( self.config.APP_NAME, last_message[1], icon_name )
							self.notification.set_urgency( urgency )
						
							if last_message[0] != 0 and first_error:
								first_error = False
								self.notification.set_timeout( 10000 )
								self.notification.show()

					time.sleep( 0.2 )
			
			status_icon.set_visible( False )
			gtk.main_iteration( False )

			self.notification.close()
			pynotify.uninit()
			
			logger.info( '[GnomePlugin.Systray.run] end loop' )

	def __init__( self ):
		return

	def init( self, snapshots ):
		if not tools.process_exists( 'gnome-settings-daemon' ):
			return False

		if not tools.check_x_server():
			return False

		self.systray = None
		try:
			self.systray = GnomePlugin.Systray( snapshots )
		except:
			self.systray = None

		return True

	def is_gui( self ):
		return True

	def on_process_begins( self ):
		if not self.systray is None:
			self.systray.start()

	def on_process_ends( self ):
		if not self.systray is None:
			self.systray.stop()

	def on_error( self, code, message ):
		return

	def on_new_snapshot( self, snapshot_id, snapshot_path ):
		return

