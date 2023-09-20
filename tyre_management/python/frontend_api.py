import frappe

#Get Customer purchased tyre details
@frappe.whitelist()
def get_customer_purchase_type_details(customer):
	tyre_details=[]
	serial_no_list = frappe.get_all("Serial No",{"item_group":"Tires","status":"Delivered","customer":customer})
	for serial_no in serial_no_list:
		serial_no_doc = frappe.get_doc("Serial No",serial_no)
		data={
			"delivery_time" : serial_no_doc.delivery_time,
			"serial_no" : serial_no_doc.name,
			"purchase_rate" : serial_no_doc.purchase_rate,
			"brand" : serial_no_doc.brand,
			"tyre_size" : serial_no_doc.tyre_size,
			"tyre location" : None,
			"tyre_position" : None,
			"cost_per_kms" : 0,
			"Operational date" : None,
			"operational_end_date" : None,
			"preventive_maintenance":[],
			"breakdown_cost":[],
			"cummulative_preventive_maintenance_cost" : 0,
			"cummulative_breakdown_cost":0
		}
		if serial_no_doc.tyre_status == "Installed":
			data['vehicle_no'] = serial_no_doc.vehicle_no
			data['installed_datetime'] = serial_no_doc.installed_datetime
			tyre_position_doc = frappe.get_doc("Vehicle Tire Position",{"name":serial_no_doc.vehicle_tire_position})
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
				"rear_right_4"
			]
			for tyre_position in serial_no_fields:
				if serial_no_doc.name == tyre_position_doc.get(tyre_position):
					data['tyre_position'] = tyre_position.replace("_", " ").capitalize()
		elif serial_no_doc.tyre_status == "Operation Ended":
			data['operational_end_date'] = serial_no_doc.operational_end_date

		breakdown_cost=frappe.get_all("Tyre Maintenance",{"serial_no":serial_no_doc.name,"maintenance_type":"Breakdown"},['time_stamp','vehicle_no','customer','vehicle_tire_position','maintenance_type','serial_no','tire_position','cost'])
		cost_breakdown_values = [entry['cost'] for entry in breakdown_cost]
		cummulative_breakdown_cost = sum(cost_breakdown_values)
		data['breakdown_cost'] = breakdown_cost
		data['cummulative_breakdown_cost'] = cummulative_breakdown_cost

		preventive_maintenance=frappe.get_all("Tyre Maintenance",{"serial_no":serial_no_doc.name,"maintenance_type":"Preventive Maintenance"},['time_stamp','vehicle_no','customer','vehicle_tire_position','maintenance_type','serial_no','tire_position','cost'])
		cost_preventive_maintenance_values = [entry['cost'] for entry in preventive_maintenance]
		cummulative_preventive_maintenance_cost = sum(cost_preventive_maintenance_values)
		data['cummulative_preventive_maintenance_cost'] = cummulative_preventive_maintenance_cost
	
		data['preventive_maintenance'] = preventive_maintenance
		tyre_details.append(data)

	return tyre_details