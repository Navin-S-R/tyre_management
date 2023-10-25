# Copyright (c) 2023, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class VehicleTirePosition(Document):
	def on_submit(self):
		if not self.time_stamp:
			self.time_stamp = frappe.utils.now()
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
				serial_doc_details=frappe.db.get_value("Tyre Serial No",{"name":self.get(field)},['name','installed_datetime'],as_dict=True)
				if serial_doc_details.get('name'):
					values = "SET ref_doctype='{0}', vehicle_no='{1}',vehicle_tire_position='{2}',tyre_status='Installed'".format(self.ref_doctype,self.vehicle_no,self.name)
					if not serial_doc_details.get('installed_datetime'):
						values+=",installed_datetime='{0}' ".format(self.time_stamp)
					frappe.db.sql("""UPDATE `tabTyre Serial No` 
										{0}
										where name='{1}'
								""".format(values,self.get(field)))

		# Previous Tyre Positions
		previous_tyre_position_doc = frappe.db.get_value("Vehicle Tire Position",{"vehicle_no":self.vehicle_no,"docstatus":1,"name":["!=",self.name]},serial_no_fields,as_dict=True)
		if previous_tyre_position_doc:
			previous_tyres = list(filter(lambda x: x is not None, previous_tyre_position_doc.values()))

			# Current Tyre position
			current_tyre_position_doc = frappe.db.get_value("Vehicle Tire Position",{"name":self.name},serial_no_fields,as_dict=True)
			current_tyres = list(filter(lambda x: x is not None, current_tyre_position_doc.values()))

			removed_tyres = [tyre for tyre in previous_tyres if tyre not in current_tyres]
			if removed_tyres:
				#Updating the tyre status and operational_end_date
				for removed_tyre in removed_tyres:
					frappe.db.sql("UPDATE `tabTyre Serial No` SET operational_end_date='{0}',tyre_status='Operation Ended' WHERE name='{1}'".format(self.time_stamp,removed_tyre))
		
	def validate(self):
		#Same Serial No validation #Tyre Active in other vehicles
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
		for i in serial_no_fields:
			check_field = self.get(i)
			if check_field != None and frappe.db.get_value("Tyre Serial No",{"name":check_field,"docstatus":1},"tyre_status") == "Scarped":
				frappe.throw(_(f"{check_field} Tyre Already Scarped"))
			for j in serial_no_fields:
				if check_field != None and check_field == self.get(j) and i != j:
					frappe.throw(_(f"{i} and {j} have same tyre"))
		
		#wheel level validation
		if self.wheels == 4:
			tire_fields = [
				"front_left_1",
				"front_right_1",
				"rear_left_1",
				"rear_right_1"
			]
			for tire in tire_fields:
				if not self.get(tire):
					frappe.throw(_(f"{tire} is not mentioned"))
				previously_installed_vehicle=frappe.db.get_value("Tyre Serial No",{"name":self.get(tire),"tyre_status":"Installed"},"vehicle_no")
				if previously_installed_vehicle and previously_installed_vehicle != self.vehicle_no:
					frappe.throw(_(f"{previously_installed_vehicle} have same tyre installed"))
		if self.wheels == 6:
			tire_fields = [
				"front_left_1",
				"front_right_1",
				"rear_left_1",
				"rear_right_1",
				"rear_left_2",
				"rear_right_2"
			]
			for tire in tire_fields:
				if not self.get(tire):
					frappe.throw(_(f"{tire} is not mentioned"))
				previously_installed_vehicle=frappe.db.get_value("Tyre Serial No",{"name":self.get(tire),"tyre_status":"Installed"},"vehicle_no")
				if previously_installed_vehicle and previously_installed_vehicle != self.vehicle_no:
					frappe.throw(_(f"{previously_installed_vehicle} have same tyre installed"))

		if self.wheels == 8:
			tire_fields = [
				"front_left_1",
				"front_right_1",
				"middle_left_1",
				"middle_right_1",
				"rear_left_1",
				"rear_right_1"
				"rear_left_2",
				"rear_right_2"
			]
			for tire in tire_fields:
				if not self.get(tire):
					frappe.throw(_(f"{tire} is not mentioned"))
				previously_installed_vehicle=frappe.db.get_value("Tyre Serial No",{"name":self.get(tire),"tyre_status":"Installed"},"vehicle_no")
				if previously_installed_vehicle and previously_installed_vehicle != self.vehicle_no:
					frappe.throw(_(f"{previously_installed_vehicle} have same tyre installed"))

		if self.wheels == 10:
			tire_fields = [
				"front_left_1",
				"front_right_1",
				"middle_left_1",
				"middle_right_1",
				"middle_left_2",
				"middle_right_2",
				"rear_left_1",
				"rear_right_1",
				"rear_left_2",
				"rear_right_2"
			]
			for tire in tire_fields:
				if not self.get(tire):
					frappe.throw(_(f"{tire} is not mentioned"))
				previously_installed_vehicle=frappe.db.get_value("Tyre Serial No",{"name":self.get(tire),"tyre_status":"Installed"},"vehicle_no")
				if previously_installed_vehicle and previously_installed_vehicle != self.vehicle_no:
					frappe.throw(_(f"{previously_installed_vehicle} have same tyre installed"))
		
		if self.wheels == 12:
			tire_fields = [
				"front_left_1",
				"front_right_1",
				"middle_left_1",
				"middle_right_1",
				"middle_left_2",
				"middle_right_2",
				"rear_left_1",
				"rear_right_1",
				"rear_left_2",
				"rear_right_2",
				"rear_left_3",
				"rear_right_3"
			]
			for tire in tire_fields:
				if not self.get(tire):
					frappe.throw(_(f"{tire} is not mentioned"))
				previously_installed_vehicle=frappe.db.get_value("Tyre Serial No",{"name":self.get(tire),"tyre_status":"Installed"},"vehicle_no")
				if previously_installed_vehicle and previously_installed_vehicle != self.vehicle_no:
					frappe.throw(_(f"{previously_installed_vehicle} have same tyre installed"))

		if self.wheels == 14:
			tire_fields = [
				"front_left_1",
				"front_right_1",
				"middle_left_1",
				"middle_right_1",
				"middle_left_2",
				"middle_right_2",
				"middle_left_3",
				"middle_right_3",
				"rear_left_1",
				"rear_right_1",
				"rear_left_2",
				"rear_right_2",
				"rear_left_3",
				"rear_right_3"
			]
			for tire in tire_fields:
				if not self.get(tire):
					frappe.throw(_(f"{tire} is not mentioned"))
				previously_installed_vehicle=frappe.db.get_value("Tyre Serial No",{"name":self.get(tire),"tyre_status":"Installed"},"vehicle_no")
				if previously_installed_vehicle and previously_installed_vehicle != self.vehicle_no:
					frappe.throw(_(f"{previously_installed_vehicle} have same tyre installed"))

		if self.wheels == 14:
			tire_fields = [
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
				"rear_right_4"
			]
			for tire in tire_fields:
				if not self.get(tire):
					frappe.throw(_(f"{tire} is not mentioned"))
				previously_installed_vehicle=frappe.db.get_value("Tyre Serial No",{"name":self.get(tire),"tyre_status":"Installed"},"vehicle_no")
				if previously_installed_vehicle and previously_installed_vehicle != self.vehicle_no:
					frappe.throw(_(f"{previously_installed_vehicle} have same tyre installed"))


@frappe.whitelist()
def get_vehicle_tyre_positions(vehicles, get_optimal_values=None, get_nsd_values=None):
	final_data = {}
	serial_no_fields = [
		"front_left_1", "front_right_1", "middle_left_1", "middle_left_2", "middle_right_1", "middle_right_2",
		"middle_left_3", "middle_left_4", "middle_right_3", "middle_right_4", "rear_left_1", "rear_left_2",
		"rear_right_1", "rear_right_2", "rear_left_3", "rear_left_4", "rear_right_3", "rear_right_4",
		"spare_1", "spare_2"
	]

	for vehicle in vehicles:
		vehicle_data = []
		data = frappe.get_all("Vehicle Tire Position", {"vehicle_no": vehicle}, serial_no_fields,
							order_by="modified desc", limit=1)

		if data:
			filtered_data = {key: value for key, value in data[0].items() if value is not None}
			if filtered_data:
				vehicle_data.append(filtered_data)
				if get_optimal_values:
					optimal_values = get_optimal_tyre_values(vehicle)
					vehicle_data[0]["tyre_optimal_values"] = optimal_values
				if get_nsd_values:
					nsd_values = {}
					for key, value in filtered_data.items():
						if isinstance(value, str):
							nsd_value = frappe.db.get_value("Tyre Maintenance",
														{"serial_no": value, "maintenance_type": "Periodic Checkup", "docstatus": 0},
														'nsd_value')
							nsd_values[value] = nsd_value or 0
					vehicle_data[0]["nsd_values"] = nsd_values
		final_data[vehicle] = vehicle_data

	return final_data

@frappe.whitelist()
def get_optimal_tyre_values(vehicle_no):
	optimal_tyre_values=frappe.get_all("Vehicle Tire Position",{"vehicle_no": vehicle_no},
									['min_tyre_temperature','max_tyre_temperature',
									'min_tyre_pressure','max_tyre_pressure'],
							order_by="modified desc", limit=1)
	if optimal_tyre_values:
		return optimal_tyre_values[0]