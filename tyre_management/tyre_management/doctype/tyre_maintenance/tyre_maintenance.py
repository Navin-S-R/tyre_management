# Copyright (c) 2023, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TyreMaintenance(Document):
	def on_submit(self):
		if not self.time_stamp:
			self.time_stamp = frappe.utils.now()