# Copyright (c) 2023, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TyreMaintenance(Document):
	def on_submit(self):
		if not self.time_stamp:
			self.time_stamp = frappe.utils.now()
	def validate(self):
		if self.vehicle_no:
			if not self.vehicle_tire_position:
				tyre_position = frappe.get_value("Vehicle Tire Position",{"ref_doctype":self.ref_doctype,
																			"docstatus" : 1,
																			"vehicle_no":self.vehicle_no},"name")
				self.vehicle_tire_position

			if self.vehicle_tire_position == tyre_position:
				serial_no_fields = [
					"front_left_1",
					"front_right_1",
					"middle_left_1",
					"middle_right_1",
					"middle_left_2",
					"middle_right_2",
					"middle_left_3",
					"middle_right_3",
					"middle_left_4",
					"middle_right_4",
					"rear_left_1",
					"rear_right_1",
					"rear_left_2",
					"rear_right_2",
					"rear_left_3",
					"rear_right_3",
					"rear_left_4",
					"rear_right_4",
					"spare_1",
					"spare_2"
				]
				for field in serial_no_fields:
					if self.get(field):
						self.tire_position = field
			else:
				frappe.throw("This is not the latest tyre psition for this vehicle")

@frappe.whitelist()
def get_latest_tyre_position_for_vehicle(doctype, vehicle_no):
	tyre_position = frappe.get_value("Vehicle Tire Position",{"ref_doctype":doctype,"vehicle_no":vehicle_no},"name")
	return tyre_position